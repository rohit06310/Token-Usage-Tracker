"""
BaseProviderAdapter — the architectural core of the unified client wrapper.

Every provider (OpenAI, Anthropic, Groq, Gemini) implements this interface.
The base class handles the cross-cutting concerns:
  - Enforcing the send_request() contract
  - Extracting token usage from provider responses
  - Calculating cost via the pricing service
  - Logging usage to usage_logs immediately after every call (success OR failure)
  - Returning the response to the caller unchanged

Phase 2: provider-specific logic is fully implemented in each adapter.
"""

from __future__ import annotations

import logging
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.usage_log import CallStatus, UsageLog
from app.services.pricing import calculate_cost, get_pricing_snapshot

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared response envelope
# ---------------------------------------------------------------------------

@dataclass
class ProviderResponse:
    """
    Normalised response returned by every adapter.

    All provider-specific response shapes are mapped into this envelope
    so downstream code (logging, cost calculation, tests) is provider-agnostic.
    """

    # The raw text/content from the model
    content: str

    # Token counts extracted from the provider response
    tokens_in: int = 0
    tokens_out: int = 0

    # The calculated cost in USD
    cost: Decimal = field(default_factory=lambda: Decimal("0"))

    # 'success' or 'failed'
    status: str = CallStatus.SUCCESS

    # The full raw response object from the provider (for raw_response column)
    raw_response: dict[str, Any] = field(default_factory=dict)

    # Name of the model that served the response
    model: str = ""

    # Provider slug (set by the adapter)
    provider_slug: str = ""

    @property
    def total_tokens(self) -> int:
        return self.tokens_in + self.tokens_out

    @property
    def is_success(self) -> bool:
        return self.status == CallStatus.SUCCESS


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class BaseProviderAdapter(ABC):
    """
    Abstract base class for all LLM provider adapters.

    Subclasses MUST implement:
      - send_request()   — calls the provider API and returns a ProviderResponse
      - extract_usage()  — maps the raw provider response to token counts

    Subclasses SHOULD NOT override:
      - execute()        — the public orchestration method
      - _log_usage()     — logs usage to the DB

    Usage:
        adapter = OpenAIAdapter(provider_id=uuid, api_key="sk-...")
        response = await adapter.execute(
            prompt="Hello!",
            model="gpt-4o",
            db=db_session,
            project_tag="my-project",
        )
        # Always returns — never raises. Check response.status for failures.
        print(response.content)
    """

    def __init__(
        self,
        provider_id: Any,
        provider_slug: str,
        api_key: str,
    ) -> None:
        """
        Parameters
        ----------
        provider_id : UUID
            The UUID of the Provider row in the database.
        provider_slug : str
            e.g. "openai", "anthropic" — used for cost lookup.
        api_key : str
            The **decrypted** provider API key.
        """
        self.provider_id = provider_id
        self.provider_slug = provider_slug
        self._api_key = api_key  # Never log or expose this

    # ------------------------------------------------------------------
    # Abstract interface — implemented per provider
    # ------------------------------------------------------------------

    @abstractmethod
    async def send_request(
        self,
        prompt: str,
        model: str,
        **kwargs: Any,
    ) -> ProviderResponse:
        """
        Call the underlying provider SDK / REST API.

        Implementations must:
        1. Call the provider SDK
        2. Call self.extract_usage(raw_response_dict) to get token counts
        3. Call calculate_cost() and get_pricing_snapshot() for cost
        4. Return a fully populated ProviderResponse

        Do NOT catch exceptions — let them propagate to execute() which
        handles failure logging.
        """
        raise NotImplementedError

    @abstractmethod
    def extract_usage(self, raw_response: dict[str, Any]) -> dict[str, int]:
        """
        Extract token counts from the provider's raw response object.

        Returns
        -------
        dict with keys: tokens_in (int), tokens_out (int)
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Orchestration — callers use this, NOT send_request() directly
    # ------------------------------------------------------------------

    async def execute(
        self,
        prompt: str,
        model: str,
        db: Session,
        project_tag: str | None = None,
        user_id: Any = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """
        Orchestrates the full request lifecycle:
          1. Calls send_request() (provider-specific)
          2. Logs the result to usage_logs (success OR failure)
          3. Returns the ProviderResponse — NEVER raises

        On failure, a UsageLog row is written with status='failed' and the
        error traceback in raw_response. The ProviderResponse returned has
        empty content and status='failed'.
        """
        logger.info(
            "Executing provider request",
            extra={
                "provider_slug": self.provider_slug,
                "provider_id": str(self.provider_id),
                "model": model,
            },
        )

        try:
            response = await self.send_request(prompt=prompt, model=model, **kwargs)
            response.status = CallStatus.SUCCESS

        except Exception as exc:
            error_tb = traceback.format_exc()
            logger.error(
                "Provider request FAILED: %s",
                str(exc),
                extra={
                    "provider_slug": self.provider_slug,
                    "model": model,
                },
                exc_info=False,  # Already captured in error_tb
            )
            # Build a failed ProviderResponse
            response = ProviderResponse(
                content="",
                tokens_in=0,
                tokens_out=0,
                cost=Decimal("0"),
                status=CallStatus.FAILED,
                model=model,
                provider_slug=self.provider_slug,
                raw_response={
                    "_status": "failed",
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "traceback": error_tb,
                },
            )

        # Log to DB — success or failure. DB errors must not propagate.
        try:
            self._log_usage(db=db, response=response, project_tag=project_tag, user_id=user_id)
        except Exception as db_exc:
            db.rollback()
            logger.error(
                "Failed to log usage to DB — response still returned to caller",
                exc_info=True,
            )

        return response

    @abstractmethod
    async def send_request_stream(
        self,
        prompt: str,
        model: str,
        **kwargs: Any,
    ):
        """
        Call the underlying provider SDK / REST API and yield SSE-compatible string chunks.
        Must yield JSON strings or text.
        At the end of the generator, it must yield a final `ProviderResponse` object containing the total usage.
        """
        raise NotImplementedError

    async def execute_stream(
        self,
        prompt: str,
        model: str,
        db: Session,
        project_tag: str | None = None,
        user_id: Any = None,
        **kwargs: Any,
    ):
        """
        Orchestrates the streaming request lifecycle:
          1. Calls send_request_stream()
          2. Yields chunks back to caller
          3. Logs the final result to usage_logs
        """
        logger.info(
            "Executing streaming provider request",
            extra={
                "provider_slug": self.provider_slug,
                "provider_id": str(self.provider_id),
                "model": model,
            },
        )
        
        try:
            stream_generator = self.send_request_stream(prompt=prompt, model=model, **kwargs)
            
            async for chunk in stream_generator:
                if isinstance(chunk, ProviderResponse):
                    # End of stream, log usage
                    chunk.status = CallStatus.SUCCESS
                    try:
                        self._log_usage(db=db, response=chunk, project_tag=project_tag, user_id=user_id)
                    except Exception as db_exc:
                        db.rollback()
                        logger.error("Failed to log usage to DB at end of stream", exc_info=True)
                else:
                    yield chunk

        except Exception as exc:
            error_tb = traceback.format_exc()
            logger.error("Provider stream FAILED: %s", str(exc), exc_info=False)
            response = ProviderResponse(
                content="",
                tokens_in=0,
                tokens_out=0,
                cost=Decimal("0"),
                status=CallStatus.FAILED,
                model=model,
                provider_slug=self.provider_slug,
                raw_response={
                    "_status": "failed",
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "traceback": error_tb,
                },
            )
            try:
                self._log_usage(db=db, response=response, project_tag=project_tag, user_id=user_id)
            except Exception as db_exc:
                db.rollback()
            yield f"data: {{\"error\": \"{str(exc)}\"}}\n\n"

    def _log_usage(
        self,
        db: Session,
        response: ProviderResponse,
        project_tag: str | None = None,
        user_id: Any = None,
    ) -> UsageLog:
        """
        Persist a UsageLog row for this API call (success or failure).
        Called automatically by execute() — not part of the public interface.
        """
        log_entry = UsageLog(
            provider_id=self.provider_id,
            user_id=user_id or "00000000-0000-0000-0000-000000000000",
            model=response.model or "unknown",
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            cost=response.cost,
            status=response.status,
            project_tag=project_tag,
            raw_response=response.raw_response or {},
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        logger.info(
            "Usage logged: status=%s model=%s tokens=(%d+%d) cost=$%s",
            log_entry.status,
            log_entry.model,
            log_entry.tokens_in,
            log_entry.tokens_out,
            log_entry.cost,
            extra={"log_id": str(log_entry.id)},
        )
        return log_entry
