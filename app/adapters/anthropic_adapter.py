"""
Anthropic Adapter — real implementation using the `anthropic` Python SDK.

Supports: Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus, Claude 3 Haiku,
          claude-sonnet-4-5, claude-opus-4-5
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from app.adapters.base import BaseProviderAdapter, ProviderResponse
from app.services.pricing import calculate_cost, get_pricing_snapshot

logger = logging.getLogger(__name__)

PROVIDER_SLUG = "anthropic"
DEFAULT_MAX_TOKENS = 1024  # Anthropic requires max_tokens to be set


class AnthropicAdapter(BaseProviderAdapter):
    """
    Adapter for the Anthropic Messages API (Claude family).

    Requires the `anthropic` SDK: pip install anthropic

    Supported kwargs:
      - system_prompt (str): System message content
      - max_tokens (int): Maximum completion tokens (default: 1024)
      - temperature (float): Sampling temperature (0.0–1.0)
    """

    def __init__(self, provider_id: Any, api_key: str) -> None:
        super().__init__(
            provider_id=provider_id,
            provider_slug=PROVIDER_SLUG,
            api_key=api_key,
        )

    async def send_request(
        self,
        prompt: str,
        model: str,
        **kwargs: Any,
    ) -> ProviderResponse:
        """
        Call the Anthropic Messages API.

        Parameters
        ----------
        prompt : str      The user message.
        model : str       Model ID, e.g. "claude-3-5-sonnet-20241022".
        **kwargs
          system_prompt   Optional system message string.
          max_tokens      Max completion tokens (default: 1024).
          temperature     Sampling temperature (0.0–1.0).
        """
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise RuntimeError(
                "anthropic package is required. Install with: pip install anthropic"
            )

        client = AsyncAnthropic(api_key=self._api_key)

        # Build API call parameters
        api_kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": kwargs.pop("max_tokens", DEFAULT_MAX_TOKENS),
            "messages": [{"role": "user", "content": prompt}],
        }

        system_prompt = kwargs.pop("system_prompt", None)
        if system_prompt:
            api_kwargs["system"] = system_prompt

        for key in ("temperature", "top_p", "top_k"):
            if key in kwargs:
                api_kwargs[key] = kwargs[key]

        logger.debug("Calling Anthropic API: model=%s", model)

        raw = await client.messages.create(**api_kwargs)
        raw_dict = raw.model_dump()

        usage = self.extract_usage(raw_dict)
        cost = calculate_cost(
            provider_slug=PROVIDER_SLUG,
            model=model,
            tokens_in=usage["tokens_in"],
            tokens_out=usage["tokens_out"],
        )
        raw_dict["_pricing_used"] = get_pricing_snapshot(PROVIDER_SLUG, model)

        # Extract text content from first content block
        content_text = ""
        if raw.content and len(raw.content) > 0:
            first_block = raw.content[0]
            if hasattr(first_block, "text"):
                content_text = first_block.text

        return ProviderResponse(
            content=content_text,
            tokens_in=usage["tokens_in"],
            tokens_out=usage["tokens_out"],
            cost=cost,
            model=model,
            provider_slug=PROVIDER_SLUG,
            raw_response=raw_dict,
        )

    def extract_usage(self, raw_response: dict[str, Any]) -> dict[str, int]:
        """
        Extract token counts from Anthropic's response.

        Anthropic shape:
            raw_response["usage"]["input_tokens"]
            raw_response["usage"]["output_tokens"]
        """
        usage = raw_response.get("usage") or {}
        return {
            "tokens_in": usage.get("input_tokens", 0),
            "tokens_out": usage.get("output_tokens", 0),
        }

    async def send_request_stream(
        self,
        prompt: str,
        model: str,
        **kwargs: Any,
    ):
        try:
            from anthropic import AsyncAnthropic
            import json
        except ImportError:
            raise RuntimeError("anthropic package is required.")

        client = AsyncAnthropic(api_key=self._api_key)

        api_kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": kwargs.pop("max_tokens", DEFAULT_MAX_TOKENS),
            "messages": [{"role": "user", "content": prompt}],
        }

        system_prompt = kwargs.pop("system_prompt", None)
        if system_prompt:
            api_kwargs["system"] = system_prompt

        for key in ("temperature", "top_p", "top_k"):
            if key in kwargs:
                api_kwargs[key] = kwargs[key]

        logger.debug("Calling Anthropic API Stream: model=%s", model)

        full_content = []
        tokens_in = 0
        tokens_out = 0

        async with client.messages.stream(**api_kwargs) as stream:
            async for text in stream.text_stream:
                full_content.append(text)
                payload = json.dumps({"content": text})
                yield f"data: {payload}\n\n"
            
            message = await stream.get_final_message()
            tokens_in = message.usage.input_tokens
            tokens_out = message.usage.output_tokens

        cost = calculate_cost(
            provider_slug=PROVIDER_SLUG,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )

        raw_dict = {
            "streamed": True,
            "_pricing_used": get_pricing_snapshot(PROVIDER_SLUG, model)
        }

        meta_payload = json.dumps({
            "status": "success",
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": str(cost),
        })
        yield f"data: {meta_payload}\n\n"

        yield ProviderResponse(
            content="".join(full_content),
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost,
            model=model,
            provider_slug=PROVIDER_SLUG,
            raw_response=raw_dict,
        )
