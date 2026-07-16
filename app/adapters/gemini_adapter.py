"""
Gemini Adapter — real implementation using the `google-generativeai` Python SDK.

Supports: Gemini 2.0 Flash, Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini 1.5 Flash-8B
"""

from __future__ import annotations

import asyncio
import logging
from decimal import Decimal
from typing import Any

from app.adapters.base import BaseProviderAdapter, ProviderResponse
from app.services.pricing import calculate_cost, get_pricing_snapshot

logger = logging.getLogger(__name__)

PROVIDER_SLUG = "gemini"


class GeminiAdapter(BaseProviderAdapter):
    """
    Adapter for the Google Gemini API.

    Requires the `google-generativeai` SDK: pip install google-generativeai

    Note: The google-generativeai SDK's async support is via
    `generate_content_async`. For older SDK versions, we fall back to
    running the sync call in a thread pool executor.

    Supported kwargs:
      - system_prompt (str): System instruction for the model
      - temperature (float): Sampling temperature (0.0–2.0)
      - max_output_tokens (int): Maximum output tokens
      - top_p (float): Nucleus sampling parameter
      - top_k (int): Top-k sampling parameter
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
        Call the Gemini GenerateContent API.

        Parameters
        ----------
        prompt : str      The user prompt.
        model : str       Model ID, e.g. "gemini-1.5-flash", "gemini-2.0-flash".
        **kwargs
          system_prompt         Optional system instruction string.
          temperature           Sampling temperature.
          max_output_tokens     Maximum output tokens.
          top_p                 Nucleus sampling.
          top_k                 Top-k sampling.
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise RuntimeError(
                "google-generativeai package is required. "
                "Install with: pip install google-generativeai"
            )

        genai.configure(api_key=self._api_key)

        # Build generation config
        generation_config: dict[str, Any] = {}
        for key in ("temperature", "max_output_tokens", "top_p", "top_k"):
            if key in kwargs:
                generation_config[key] = kwargs[key]

        # Build model instance
        system_instruction = kwargs.pop("system_prompt", None)
        model_kwargs: dict[str, Any] = {}
        if system_instruction:
            model_kwargs["system_instruction"] = system_instruction
        if generation_config:
            model_kwargs["generation_config"] = generation_config

        gemini_model = genai.GenerativeModel(model, **model_kwargs)

        logger.debug("Calling Gemini API: model=%s", model)

        # Use async API if available, otherwise run in thread pool
        try:
            raw = await gemini_model.generate_content_async(prompt)
        except AttributeError:
            # Fallback for older SDK versions without generate_content_async
            loop = asyncio.get_event_loop()
            raw = await loop.run_in_executor(
                None, gemini_model.generate_content, prompt
            )

        # Convert to dict for storage
        try:
            raw_dict = raw.to_dict()
        except Exception:
            # Fallback if to_dict() not available
            raw_dict = {
                "text": raw.text if hasattr(raw, "text") else "",
                "candidates": [],
            }

        usage = self.extract_usage(raw_dict)
        cost = calculate_cost(
            provider_slug=PROVIDER_SLUG,
            model=model,
            tokens_in=usage["tokens_in"],
            tokens_out=usage["tokens_out"],
        )
        raw_dict["_pricing_used"] = get_pricing_snapshot(PROVIDER_SLUG, model)

        # Extract text from response
        content_text = ""
        try:
            content_text = raw.text
        except Exception:
            # Handle safety blocks or empty responses
            if raw_dict.get("candidates"):
                first_candidate = raw_dict["candidates"][0]
                parts = first_candidate.get("content", {}).get("parts", [])
                if parts:
                    content_text = parts[0].get("text", "")

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
        Extract token counts from Gemini's response.

        Gemini shape (via to_dict()):
            raw_response["usageMetadata"]["promptTokenCount"]
            raw_response["usageMetadata"]["candidatesTokenCount"]

        Note: field names use camelCase in the raw dict.
        """
        meta = raw_response.get("usageMetadata") or raw_response.get("usage_metadata") or {}
        return {
            "tokens_in": (
                meta.get("promptTokenCount")
                or meta.get("prompt_token_count")
                or 0
            ),
            "tokens_out": (
                meta.get("candidatesTokenCount")
                or meta.get("candidates_token_count")
                or 0
            ),
        }

    async def send_request_stream(
        self,
        prompt: str,
        model: str,
        **kwargs: Any,
    ):
        try:
            import google.generativeai as genai
            import json
        except ImportError:
            raise RuntimeError("google-generativeai package is required.")

        genai.configure(api_key=self._api_key)

        generation_config: dict[str, Any] = {}
        for key in ("temperature", "max_output_tokens", "top_p", "top_k"):
            if key in kwargs:
                generation_config[key] = kwargs[key]

        system_instruction = kwargs.pop("system_prompt", None)
        model_kwargs: dict[str, Any] = {}
        if system_instruction:
            model_kwargs["system_instruction"] = system_instruction
        if generation_config:
            model_kwargs["generation_config"] = generation_config

        gemini_model = genai.GenerativeModel(model, **model_kwargs)
        logger.debug("Calling Gemini API Stream: model=%s", model)

        try:
            stream = await gemini_model.generate_content_async(prompt, stream=True)
        except AttributeError:
            import asyncio
            loop = asyncio.get_event_loop()
            stream = await loop.run_in_executor(
                None, lambda: gemini_model.generate_content(prompt, stream=True)
            )

        full_content = []
        tokens_in = 0
        tokens_out = 0
        
        async for chunk in stream:
            text = chunk.text
            if text:
                full_content.append(text)
                payload = json.dumps({"content": text})
                yield f"data: {payload}\n\n"
            
            # Gemini includes usage metadata usually in the last chunk
            if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                tokens_in = getattr(chunk.usage_metadata, "prompt_token_count", tokens_in)
                tokens_out = getattr(chunk.usage_metadata, "candidates_token_count", tokens_out)

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
