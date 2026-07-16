"""
Adapters package — registry mapping provider slugs to adapter classes.
"""

from app.adapters.openai_adapter import OpenAIAdapter
from app.adapters.anthropic_adapter import AnthropicAdapter
from app.adapters.groq_adapter import GroqAdapter
from app.adapters.gemini_adapter import GeminiAdapter

# Registry: slug → adapter class
ADAPTER_REGISTRY: dict[str, type] = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "groq": GroqAdapter,
    "gemini": GeminiAdapter,
}


def get_adapter_class(provider_slug: str) -> type:
    """
    Return the adapter class for a given provider slug.

    Raises ValueError if the slug is not registered.
    """
    cls = ADAPTER_REGISTRY.get(provider_slug)
    if cls is None:
        raise ValueError(
            f"No adapter registered for provider '{provider_slug}'. "
            f"Available: {list(ADAPTER_REGISTRY.keys())}"
        )
    return cls


__all__ = [
    "OpenAIAdapter",
    "AnthropicAdapter",
    "GroqAdapter",
    "GeminiAdapter",
    "ADAPTER_REGISTRY",
    "get_adapter_class",
]
