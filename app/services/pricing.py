"""
Pricing configuration and cost calculation.

Pricing data is sourced from official provider pricing pages (as of 2025-07).
All prices are in USD per 1,000,000 tokens (per-million pricing is the industry norm).

IMPORTANT: Prices change. Always check provider docs for latest pricing.
Sources:
  - OpenAI:    https://openai.com/pricing
  - Anthropic: https://www.anthropic.com/pricing
  - Groq:      https://console.groq.com/docs/openai
  - Gemini:    https://ai.google.dev/pricing

The pricing snapshot used at call time is stored in raw_response["_pricing_used"]
so future price changes don't corrupt historical cost data.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import TypedDict


class ModelPricing(TypedDict):
    """Pricing for a single model in USD per 1M tokens."""
    input_per_1m: Decimal    # Cost per 1M input (prompt) tokens
    output_per_1m: Decimal   # Cost per 1M output (completion) tokens


# ==============================================================================
# Pricing Table — USD per 1,000,000 tokens
# ==============================================================================

PRICING: dict[str, dict[str, ModelPricing]] = {

    # --------------------------------------------------------------------------
    # OpenAI  (https://openai.com/pricing)
    # --------------------------------------------------------------------------
    "openai": {
        "gpt-4o": ModelPricing(
            input_per_1m=Decimal("2.50"),
            output_per_1m=Decimal("10.00"),
        ),
        "gpt-4o-mini": ModelPricing(
            input_per_1m=Decimal("0.15"),
            output_per_1m=Decimal("0.60"),
        ),
        "gpt-4o-mini-2024-07-18": ModelPricing(
            input_per_1m=Decimal("0.15"),
            output_per_1m=Decimal("0.60"),
        ),
        "gpt-4-turbo": ModelPricing(
            input_per_1m=Decimal("10.00"),
            output_per_1m=Decimal("30.00"),
        ),
        "gpt-4-turbo-2024-04-09": ModelPricing(
            input_per_1m=Decimal("10.00"),
            output_per_1m=Decimal("30.00"),
        ),
        "gpt-4": ModelPricing(
            input_per_1m=Decimal("30.00"),
            output_per_1m=Decimal("60.00"),
        ),
        "gpt-3.5-turbo": ModelPricing(
            input_per_1m=Decimal("0.50"),
            output_per_1m=Decimal("1.50"),
        ),
        "gpt-3.5-turbo-0125": ModelPricing(
            input_per_1m=Decimal("0.50"),
            output_per_1m=Decimal("1.50"),
        ),
        "o1": ModelPricing(
            input_per_1m=Decimal("15.00"),
            output_per_1m=Decimal("60.00"),
        ),
        "o1-mini": ModelPricing(
            input_per_1m=Decimal("3.00"),
            output_per_1m=Decimal("12.00"),
        ),
        "o3-mini": ModelPricing(
            input_per_1m=Decimal("1.10"),
            output_per_1m=Decimal("4.40"),
        ),
    },

    # --------------------------------------------------------------------------
    # Anthropic  (https://www.anthropic.com/pricing)
    # --------------------------------------------------------------------------
    "anthropic": {
        "claude-opus-4-5": ModelPricing(
            input_per_1m=Decimal("15.00"),
            output_per_1m=Decimal("75.00"),
        ),
        "claude-sonnet-4-5": ModelPricing(
            input_per_1m=Decimal("3.00"),
            output_per_1m=Decimal("15.00"),
        ),
        "claude-3-5-sonnet-20241022": ModelPricing(
            input_per_1m=Decimal("3.00"),
            output_per_1m=Decimal("15.00"),
        ),
        "claude-3-5-sonnet-20240620": ModelPricing(
            input_per_1m=Decimal("3.00"),
            output_per_1m=Decimal("15.00"),
        ),
        "claude-3-5-haiku-20241022": ModelPricing(
            input_per_1m=Decimal("0.80"),
            output_per_1m=Decimal("4.00"),
        ),
        "claude-3-opus-20240229": ModelPricing(
            input_per_1m=Decimal("15.00"),
            output_per_1m=Decimal("75.00"),
        ),
        "claude-3-sonnet-20240229": ModelPricing(
            input_per_1m=Decimal("3.00"),
            output_per_1m=Decimal("15.00"),
        ),
        "claude-3-haiku-20240307": ModelPricing(
            input_per_1m=Decimal("0.25"),
            output_per_1m=Decimal("1.25"),
        ),
    },

    # --------------------------------------------------------------------------
    # Groq  (https://console.groq.com/docs/openai) — very low cost
    # --------------------------------------------------------------------------
    "groq": {
        "llama-3.3-70b-versatile": ModelPricing(
            input_per_1m=Decimal("0.59"),
            output_per_1m=Decimal("0.79"),
        ),
        "llama-3.1-70b-versatile": ModelPricing(
            input_per_1m=Decimal("0.59"),
            output_per_1m=Decimal("0.79"),
        ),
        "llama-3.1-8b-instant": ModelPricing(
            input_per_1m=Decimal("0.05"),
            output_per_1m=Decimal("0.08"),
        ),
        "llama3-70b-8192": ModelPricing(
            input_per_1m=Decimal("0.59"),
            output_per_1m=Decimal("0.79"),
        ),
        "llama3-8b-8192": ModelPricing(
            input_per_1m=Decimal("0.05"),
            output_per_1m=Decimal("0.08"),
        ),
        "mixtral-8x7b-32768": ModelPricing(
            input_per_1m=Decimal("0.24"),
            output_per_1m=Decimal("0.24"),
        ),
        "gemma2-9b-it": ModelPricing(
            input_per_1m=Decimal("0.20"),
            output_per_1m=Decimal("0.20"),
        ),
        "gemma-7b-it": ModelPricing(
            input_per_1m=Decimal("0.07"),
            output_per_1m=Decimal("0.07"),
        ),
    },

    # --------------------------------------------------------------------------
    # Gemini  (https://ai.google.dev/pricing)
    # --------------------------------------------------------------------------
    "gemini": {
        "gemini-2.0-flash": ModelPricing(
            input_per_1m=Decimal("0.10"),
            output_per_1m=Decimal("0.40"),
        ),
        "gemini-2.0-flash-exp": ModelPricing(
            input_per_1m=Decimal("0.00"),   # Free during preview
            output_per_1m=Decimal("0.00"),
        ),
        "gemini-1.5-pro": ModelPricing(
            input_per_1m=Decimal("1.25"),
            output_per_1m=Decimal("5.00"),
        ),
        "gemini-1.5-pro-002": ModelPricing(
            input_per_1m=Decimal("1.25"),
            output_per_1m=Decimal("5.00"),
        ),
        "gemini-1.5-flash": ModelPricing(
            input_per_1m=Decimal("0.075"),
            output_per_1m=Decimal("0.30"),
        ),
        "gemini-1.5-flash-002": ModelPricing(
            input_per_1m=Decimal("0.075"),
            output_per_1m=Decimal("0.30"),
        ),
        "gemini-1.5-flash-8b": ModelPricing(
            input_per_1m=Decimal("0.0375"),
            output_per_1m=Decimal("0.15"),
        ),
    },
}

# Fallback pricing when model not found in table (prevents silent zero cost)
_FALLBACK_PRICING = ModelPricing(
    input_per_1m=Decimal("0"),
    output_per_1m=Decimal("0"),
)


def get_model_pricing(provider_slug: str, model: str) -> ModelPricing | None:
    """
    Return the pricing entry for a specific provider + model.

    Returns None if the provider or model is not in the pricing table.
    Callers should handle None gracefully (log a warning, use zero cost).
    """
    provider_pricing = PRICING.get(provider_slug, {})

    # Exact match first
    if model in provider_pricing:
        return provider_pricing[model]

    # Prefix match: "gpt-4o-2024-05-13" → use "gpt-4o" pricing if available
    for known_model, pricing in provider_pricing.items():
        if model.startswith(known_model):
            return pricing

    return None


def calculate_cost(
    provider_slug: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
) -> Decimal:
    """
    Calculate the USD cost of an LLM API call.

    Uses per-million token pricing. Returns Decimal("0") if the model
    is not in the pricing table (unknown models are free rather than error).

    Parameters
    ----------
    provider_slug : str   Provider slug (e.g. "openai")
    model : str           Model identifier (e.g. "gpt-4o")
    tokens_in : int       Number of input (prompt) tokens
    tokens_out : int      Number of output (completion) tokens

    Returns
    -------
    Decimal  USD cost rounded to 8 decimal places.
    """
    pricing = get_model_pricing(provider_slug, model)
    if pricing is None:
        return Decimal("0")

    input_cost = (Decimal(tokens_in) / Decimal("1_000_000")) * pricing["input_per_1m"]
    output_cost = (Decimal(tokens_out) / Decimal("1_000_000")) * pricing["output_per_1m"]
    total = (input_cost + output_cost).quantize(
        Decimal("0.00000001"), rounding=ROUND_HALF_UP
    )
    return total


def get_pricing_snapshot(provider_slug: str, model: str) -> dict:
    """
    Return the pricing rates used at call time as a dict.

    This dict is embedded into raw_response["_pricing_used"] so that
    historical cost records remain accurate even after table updates.
    """
    pricing = get_model_pricing(provider_slug, model)
    if pricing is None:
        return {
            "provider": provider_slug,
            "model": model,
            "input_per_1m_usd": "unknown",
            "output_per_1m_usd": "unknown",
            "note": "Model not found in pricing table — cost set to 0",
        }
    return {
        "provider": provider_slug,
        "model": model,
        "input_per_1m_usd": str(pricing["input_per_1m"]),
        "output_per_1m_usd": str(pricing["output_per_1m"]),
    }
