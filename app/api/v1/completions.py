"""
Completions endpoint — the primary interface for making LLM calls through the dashboard.

POST /api/v1/completions
  → Looks up the provider by slug
  → Fetches the active API key from the database (decrypts it)
  → Calls the appropriate adapter's execute() method
  → Returns the response along with usage and cost info
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.adapters import ADAPTER_REGISTRY, get_adapter_class
from app.core.deps import AuthenticatedUser
from app.core.security import get_encryption
from app.models.api_key import ApiKey
from app.models.provider import Provider
from app.schemas.usage_log import UsageLogRead
from app.services.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/completions", tags=["Completions"])


class CompletionRequest(BaseModel):
    """Request body for a completion call."""
    provider_slug: str = Field(
        ...,
        examples=["openai", "anthropic", "groq", "gemini"],
        description="Provider slug — must match a registered provider.",
    )
    model: str = Field(
        ...,
        examples=["gpt-4o-mini", "claude-3-5-haiku-20241022"],
        description="Model identifier.",
    )
    prompt: str = Field(..., min_length=1, description="The user prompt.")
    project_tag: str | None = Field(
        None,
        description="Optional tag for cost attribution.",
    )
    # Optional provider-specific parameters
    system_prompt: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=1)
    stream: bool = Field(False, description="Whether to stream the response back using SSE.")
    api_key_id: UUID | None = Field(
        None,
        description="Specific api_keys.id to use. If omitted, uses the most recent active key.",
    )


class CompletionResponse(BaseModel):
    """Response from a completion call."""
    content: str
    model: str
    provider_slug: str
    tokens_in: int
    tokens_out: int
    total_tokens: int
    cost_usd: str
    status: str
    log_id: str | None = None


from fastapi.responses import StreamingResponse

@router.post(
    "/",
    summary="Run an LLM completion through the dashboard",
    description=(
        "Sends a prompt to the specified provider, logs usage and cost to Supabase, "
        "and returns the response. Always returns 200 — check `status` field for failures."
    ),
)
async def create_completion(
    payload: CompletionRequest,
    db: Session = Depends(get_db),
    _user: AuthenticatedUser = None,
):
    """
    Make an LLM API call through the unified adapter layer.

    The response always returns HTTP 200. If the provider call failed,
    the `status` field will be 'failed' and `content` will be empty.
    A usage_log row is always written (with status=failed on errors).
    """
    # 1. Look up the provider
    provider = db.query(Provider).filter(Provider.slug == payload.provider_slug).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{payload.provider_slug}' not found. "
                   "Register it first via POST /api/v1/providers/",
        )

    # 2. Look up the adapter class
    try:
        adapter_cls = get_adapter_class(payload.provider_slug)
    except ValueError as e:
        if provider.base_url:
            from app.adapters.custom_openai_adapter import CustomOpenAIAdapter
            adapter_cls = CustomOpenAIAdapter
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e) + " OR set a base_url for a custom OpenAI-compatible endpoint.",
            )

    # 3. Fetch and decrypt the API key
    key_query = (
        db.query(ApiKey)
        .filter(ApiKey.provider_id == provider.id, ApiKey.is_active == True)  # noqa: E712
    )
    if payload.api_key_id:
        key_query = key_query.filter(ApiKey.id == payload.api_key_id)
    else:
        key_query = key_query.order_by(ApiKey.created_at.desc())

    api_key_row = key_query.first()
    if not api_key_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active API key found for provider '{payload.provider_slug}'. "
                   "Add one via POST /api/v1/api-keys/",
        )

    encryption = get_encryption()
    try:
        decrypted_key = encryption.decrypt(api_key_row.encrypted_key)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt the stored API key. "
                   "The encryption key may have changed — please re-add the key.",
        )

    # 4. Build kwargs for the adapter
    adapter_kwargs = {}
    if payload.system_prompt:
        adapter_kwargs["system_prompt"] = payload.system_prompt
    if payload.temperature is not None:
        adapter_kwargs["temperature"] = payload.temperature
    if payload.max_tokens is not None:
        adapter_kwargs["max_tokens"] = payload.max_tokens

    # 5. Execute via adapter
    if adapter_cls.__name__ == "CustomOpenAIAdapter":
        adapter = adapter_cls(
            provider_id=provider.id,
            api_key=decrypted_key,
            base_url=provider.base_url,
            provider_slug=provider.slug
        )
    else:
        adapter = adapter_cls(provider_id=provider.id, api_key=decrypted_key)

    if payload.stream:
        return StreamingResponse(
            adapter.execute_stream(
                prompt=payload.prompt,
                model=payload.model,
                db=db,
                project_tag=payload.project_tag,
                user_id=_user.id,
                **adapter_kwargs,
            ),
            media_type="text/event-stream"
        )
    else:
        response = await adapter.execute(
            prompt=payload.prompt,
            model=payload.model,
            db=db,
            project_tag=payload.project_tag,
            user_id=_user.id,
            **adapter_kwargs,
        )

        # 6. Find the log entry that was just written
        from app.models.usage_log import UsageLog
        latest_log = (
            db.query(UsageLog)
            .filter(
                UsageLog.provider_id == provider.id,
                UsageLog.model == payload.model,
            )
            .order_by(UsageLog.created_at.desc())
            .first()
        )

        return CompletionResponse(
            content=response.content,
            model=response.model,
            provider_slug=response.provider_slug,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            total_tokens=response.total_tokens,
            cost_usd=str(response.cost),
            status=response.status,
            log_id=str(latest_log.id) if latest_log else None,
        )
