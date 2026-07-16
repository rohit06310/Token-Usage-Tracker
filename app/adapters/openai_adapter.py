"""
OpenAI Adapter — real implementation using the `openai` Python SDK.

Supports: GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-3.5-turbo, o1, o1-mini, o3-mini
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from app.adapters.base import BaseProviderAdapter, ProviderResponse
from app.services.pricing import calculate_cost, get_pricing_snapshot

logger = logging.getLogger(__name__)

PROVIDER_SLUG = "openai"


class OpenAIAdapter(BaseProviderAdapter):
    """
    Adapter for the OpenAI Chat Completions API.

    Requires the `openai` SDK: pip install openai

    Supported kwargs (passed through to the API):
      - system_prompt (str): System message content
      - temperature (float): Sampling temperature (0.0–2.0)
      - max_tokens (int): Maximum completion tokens
      - top_p (float): Nucleus sampling parameter
      - stream (bool): NOT supported — always False in this adapter
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
        Call the OpenAI Chat Completions API.

        Parameters
        ----------
        prompt : str      The user message.
        model : str       Model ID, e.g. "gpt-4o", "gpt-4o-mini".
        **kwargs
          system_prompt   Optional system message.
          temperature     Sampling temperature (default: 1.0).
          max_tokens      Max tokens for the completion.
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise RuntimeError(
                "openai package is required. Install with: pip install openai"
            )

        client = AsyncOpenAI(api_key=self._api_key)

        # Build messages
        messages = []
        system_prompt = kwargs.pop("system_prompt", None)
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Filter supported kwargs
        api_kwargs: dict[str, Any] = {}
        for key in ("temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"):
            if key in kwargs:
                api_kwargs[key] = kwargs[key]

        logger.debug("Calling OpenAI API: model=%s", model)

        raw = await client.chat.completions.create(
            model=model,
            messages=messages,
            **api_kwargs,
        )

        raw_dict = raw.model_dump()
        usage = self.extract_usage(raw_dict)
        cost = calculate_cost(
            provider_slug=PROVIDER_SLUG,
            model=model,
            tokens_in=usage["tokens_in"],
            tokens_out=usage["tokens_out"],
        )

        # Embed pricing snapshot for historical accuracy
        raw_dict["_pricing_used"] = get_pricing_snapshot(PROVIDER_SLUG, model)

        return ProviderResponse(
            content=raw.choices[0].message.content or "",
            tokens_in=usage["tokens_in"],
            tokens_out=usage["tokens_out"],
            cost=cost,
            model=model,
            provider_slug=PROVIDER_SLUG,
            raw_response=raw_dict,
        )

    def extract_usage(self, raw_response: dict[str, Any]) -> dict[str, int]:
        """
        Extract token counts from OpenAI's response.

        OpenAI shape:
            raw_response["usage"]["prompt_tokens"]
            raw_response["usage"]["completion_tokens"]
        """
        usage = raw_response.get("usage") or {}
        return {
            "tokens_in": usage.get("prompt_tokens", 0),
            "tokens_out": usage.get("completion_tokens", 0),
        }

    async def send_request_stream(
        self,
        prompt: str,
        model: str,
        **kwargs: Any,
    ):
        try:
            from openai import AsyncOpenAI
            import json
        except ImportError:
            raise RuntimeError("openai package is required.")

        client = AsyncOpenAI(api_key=self._api_key)

        messages = []
        system_prompt = kwargs.pop("system_prompt", None)
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        api_kwargs = {}
        for key in ("temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"):
            if key in kwargs:
                api_kwargs[key] = kwargs[key]

        logger.debug("Calling OpenAI API Stream: model=%s", model)

        # Ensure we request usage data in the stream
        if "stream_options" not in api_kwargs:
            api_kwargs["stream_options"] = {"include_usage": True}

        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            **api_kwargs,
        )

        full_content = []
        tokens_in = 0
        tokens_out = 0
        
        async for chunk in stream:
            if len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_content.append(text)
                payload = json.dumps({"content": text})
                yield f"data: {payload}\n\n"
            
            # Extract usage if provided in the chunk
            if hasattr(chunk, "usage") and chunk.usage:
                tokens_in = getattr(chunk.usage, "prompt_tokens", 0)
                tokens_out = getattr(chunk.usage, "completion_tokens", 0)

        # Some models don't return stream usage (e.g. older ones).
        # We try to calculate it if 0.
        if tokens_out == 0:
            tokens_out = len(full_content) * 3 # Very rough estimate if API doesn't return
            
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

        # Send final metadata to frontend
        meta_payload = json.dumps({
            "status": "success",
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": str(cost),
        })
        yield f"data: {meta_payload}\n\n"

        # Yield ProviderResponse for the base class to log
        yield ProviderResponse(
            content="".join(full_content),
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost,
            model=model,
            provider_slug=PROVIDER_SLUG,
            raw_response=raw_dict,
        )
