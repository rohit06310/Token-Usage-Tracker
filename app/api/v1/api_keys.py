"""
API Key management endpoints.
Handles storing encrypted provider API keys.
All routes require dashboard authentication.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

from app.core.deps import AuthenticatedUser
from app.core.security import get_encryption
from app.models.api_key import ApiKey
from app.models.provider import Provider
from app.schemas.api_key import ApiKeyCreate, ApiKeyRead
from app.services.db import get_db
from app.adapters import get_adapter_class

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.get("/", response_model=list[ApiKeyRead], summary="List API keys (metadata only)")
def list_api_keys(
    provider_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = None,
):
    """
    List stored API key metadata.
    The encrypted key and plaintext are NEVER returned.
    """
    query = db.query(ApiKey).filter(ApiKey.user_id == current_user.id)
    if provider_id:
        query = query.filter(ApiKey.provider_id == provider_id)
    return query.order_by(ApiKey.created_at.desc()).all()


@router.post(
    "/",
    response_model=ApiKeyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Store a new encrypted API key",
)
def create_api_key(
    payload: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = None,
):
    """
    Store a provider API key, encrypted at rest using Fernet.

    The plaintext `raw_key` from the request body is encrypted immediately
    and never stored. Only the ciphertext and label are persisted.
    """
    # Verify provider exists
    provider = db.query(Provider).filter(Provider.id == payload.provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider with id '{payload.provider_id}' not found.",
        )

    # Encrypt the key before storing
    encryption = get_encryption()
    encrypted_key = encryption.encrypt(payload.raw_key)

    api_key = ApiKey(
        provider_id=payload.provider_id,
        user_id=current_user.id,
        encrypted_key=encrypted_key,
        label=payload.label,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    logger.info(
        "API key stored (encrypted)",
        extra={"key_id": str(api_key.id), "provider": provider.slug},
    )
    return api_key


@router.post(
    "/{key_id}/test",
    summary="Test an API key",
)
async def test_api_key(
    key_id: UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = None,
):
    """
    Tests an API key by making a minimal request to the provider.
    Returns { success: bool, message: str }.
    """
    key = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.user_id == current_user.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found.")
    
    provider = db.query(Provider).filter(Provider.id == key.provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found.")

    encryption = get_encryption()
    try:
        raw_key = encryption.decrypt(key.encrypted_key)
    except Exception:
        return {"success": False, "message": "Failed to decrypt API key."}

    # Decide minimal model
    model_map = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-haiku-20240307",
        "groq": "llama3-8b-8192",
        "gemini": "gemini-1.5-flash",
    }
    model_name = model_map.get(provider.slug, "gpt-4o-mini")

    try:
        adapter_cls = get_adapter_class(provider.slug)
    except ValueError:
        return {"success": False, "message": f"Unsupported provider slug: {provider.slug}"}
    
    adapter = adapter_cls(api_key=raw_key, base_url=provider.base_url)

    from app.schemas.completion import CompletionRequest, Message
    req = CompletionRequest(
        model=model_name,
        messages=[Message(role="user", content="ping")],
        max_tokens=1
    )

    try:
        # Actually execute request using adapter
        res = await adapter.execute(req)
        if hasattr(res, "error") and res.error:
            return {"success": False, "message": str(res.error)}
        return {"success": True, "message": "Connection successful"}
    except Exception as e:
        logger.error(f"Test connection failed: {e}")
        return {"success": False, "message": str(e)}


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an API key",
)
def delete_api_key(
    key_id: UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = None,
):
    key = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.user_id == current_user.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found.")
    db.delete(key)
    db.commit()
