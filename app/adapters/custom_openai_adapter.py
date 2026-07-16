"""
Custom OpenAI Adapter — for OpenAI-compatible endpoints like Ollama, vLLM, or LiteLLM.
"""

import logging
from typing import Any
from urllib.parse import urlparse

from app.adapters.openai_adapter import OpenAIAdapter

logger = logging.getLogger(__name__)


class CustomOpenAIAdapter(OpenAIAdapter):
    """
    Adapter for custom OpenAI-compatible endpoints.
    
    Inherits from OpenAIAdapter but intercepts the client creation
    to inject a custom base_url.
    """

    def __init__(self, provider_id: Any, api_key: str, base_url: str, provider_slug: str) -> None:
        # We call super().__init__ but pass the dynamic slug instead of hardcoded 'openai'
        # To do this safely with OpenAIAdapter, we temporarily override PROVIDER_SLUG
        # Or we can just bypass the parent's super call and do BaseProviderAdapter's super
        from app.adapters.base import BaseProviderAdapter
        BaseProviderAdapter.__init__(
            self,
            provider_id=provider_id,
            provider_slug=provider_slug,
            api_key=api_key,
        )
        self.base_url = base_url

    async def send_request(
        self,
        prompt: str,
        model: str,
        **kwargs: Any,
    ):
        """
        Call the Custom OpenAI-compatible endpoint.
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise RuntimeError(
                "openai package is required. Install with: pip install openai"
            )

        client = AsyncOpenAI(
            api_key=self._api_key or "dummy",
            base_url=self.base_url,
        )

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

        logger.debug("Calling Custom OpenAI API at %s: model=%s", self.base_url, model)

        raw = await client.chat.completions.create(
            model=model,
            messages=messages,
            **api_kwargs,
        )

        raw_dict = raw.model_dump()
        usage = self.extract_usage(raw_dict)
        
        # We calculate cost dynamically.
        from app.services.pricing import calculate_cost, get_pricing_snapshot
        cost = calculate_cost(
            provider_slug=self._provider_slug,
            model=model,
            tokens_in=usage["tokens_in"],
            tokens_out=usage["tokens_out"],
        )

        # Embed pricing snapshot
        raw_dict["_pricing_used"] = get_pricing_snapshot(self._provider_slug, model)

        from app.adapters.base import ProviderResponse
        return ProviderResponse(
            content=raw.choices[0].message.content or "",
            tokens_in=usage["tokens_in"],
            tokens_out=usage["tokens_out"],
            cost=cost,
            model=model,
            provider_slug=self._provider_slug,
            raw_response=raw_dict,
        )
