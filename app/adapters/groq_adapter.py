"""
Groq Adapter — real implementation using the `groq` Python SDK.

Groq uses an OpenAI-compatible API so the response shape is identical.
Supports: Llama 3.3, Llama 3.1, Llama 3, Mixtral, Gemma (via Groq cloud).
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from app.adapters.base import BaseProviderAdapter, ProviderResponse
from app.services.pricing import calculate_cost, get_pricing_snapshot

logger = logging.getLogger(__name__)

PROVIDER_SLUG = "groq"


class GroqAdapter(BaseProviderAdapter):
    """
    Adapter for the Groq API (OpenAI-compatible Chat Completions).

    Requires the `groq` SDK: pip install groq

    Supported kwargs (passed through to the API):
      - system_prompt (str): System message content
      - temperature (float): Sampling temperature
      - max_tokens (int): Maximum completion tokens
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
        Call the Groq Chat Completions API.

        Parameters
        ----------
        prompt : str      The user message.
        model : str       Model ID, e.g. "llama-3.3-70b-versatile".
        **kwargs
          system_prompt   Optional system message.
          temperature     Sampling temperature.
          max_tokens      Max completion tokens.
        """
        try:
            from groq import AsyncGroq
        except ImportError:
            raise RuntimeError(
                "groq package is required. Install with: pip install groq"
            )

        client = AsyncGroq(api_key=self._api_key)

        # Build messages
        messages = []
        system_prompt = kwargs.pop("system_prompt", None)
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Filter supported kwargs
        api_kwargs: dict[str, Any] = {}
        for key in ("temperature", "max_tokens", "top_p", "stop"):
            if key in kwargs:
                api_kwargs[key] = kwargs[key]

        logger.debug("Calling Groq API: model=%s", model)

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
        Extract token counts from Groq's response.

        Groq uses the same shape as OpenAI:
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
            from groq import AsyncGroq
            import json
        except ImportError:
            raise RuntimeError("groq package is required.")

        client = AsyncGroq(api_key=self._api_key)

        messages = []
        system_prompt = kwargs.pop("system_prompt", None)
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        api_kwargs: dict[str, Any] = {}
        for key in ("temperature", "max_tokens", "top_p", "stop"):
            if key in kwargs:
                api_kwargs[key] = kwargs[key]

        logger.debug("Calling Groq API Stream: model=%s", model)

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
            if hasattr(chunk, "x_groq") and hasattr(chunk.x_groq, "usage") and chunk.x_groq.usage:
                tokens_in = getattr(chunk.x_groq.usage, "prompt_tokens", 0)
                tokens_out = getattr(chunk.x_groq.usage, "completion_tokens", 0)
            elif hasattr(chunk, "usage") and chunk.usage:
                tokens_in = getattr(chunk.usage, "prompt_tokens", 0)
                tokens_out = getattr(chunk.usage, "completion_tokens", 0)

        if tokens_out == 0:
            tokens_out = len(full_content) * 3
            
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
