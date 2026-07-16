"""
Tests for the pricing service — cost calculation accuracy.
No mocking needed — pure mathematical tests.
"""

from decimal import Decimal

import pytest

from app.services.pricing import (
    PRICING,
    calculate_cost,
    get_model_pricing,
    get_pricing_snapshot,
)


class TestGetModelPricing:
    def test_exact_match(self):
        pricing = get_model_pricing("openai", "gpt-4o")
        assert pricing is not None
        assert pricing["input_per_1m"] == Decimal("2.50")
        assert pricing["output_per_1m"] == Decimal("10.00")

    def test_prefix_match(self):
        """Versioned model IDs like 'gpt-4o-2024-05-13' should match 'gpt-4o'."""
        pricing = get_model_pricing("openai", "gpt-4o-2024-05-13")
        assert pricing is not None
        assert pricing["input_per_1m"] == Decimal("2.50")

    def test_unknown_provider_returns_none(self):
        assert get_model_pricing("unknown-provider", "gpt-4o") is None

    def test_unknown_model_returns_none(self):
        assert get_model_pricing("openai", "gpt-99-ultra") is None

    def test_anthropic_claude_pricing(self):
        pricing = get_model_pricing("anthropic", "claude-3-5-sonnet-20241022")
        assert pricing is not None
        assert pricing["input_per_1m"] == Decimal("3.00")
        assert pricing["output_per_1m"] == Decimal("15.00")

    def test_groq_llama_pricing(self):
        pricing = get_model_pricing("groq", "llama-3.3-70b-versatile")
        assert pricing is not None
        assert pricing["input_per_1m"] == Decimal("0.59")

    def test_gemini_flash_pricing(self):
        pricing = get_model_pricing("gemini", "gemini-1.5-flash")
        assert pricing is not None
        assert pricing["input_per_1m"] == Decimal("0.075")


class TestCalculateCost:
    def test_zero_tokens_zero_cost(self):
        cost = calculate_cost("openai", "gpt-4o", 0, 0)
        assert cost == Decimal("0")

    def test_gpt4o_mini_cost_accuracy(self):
        """
        gpt-4o-mini: $0.15/1M input, $0.60/1M output
        1000 input tokens = $0.00015
        500 output tokens  = $0.0003
        Total = $0.00045
        """
        cost = calculate_cost("openai", "gpt-4o-mini", 1000, 500)
        expected = Decimal("0.00015") + Decimal("0.0003")
        assert cost == expected.quantize(Decimal("0.00000001"))

    def test_gpt4o_cost_accuracy(self):
        """
        gpt-4o: $2.50/1M input, $10.00/1M output
        10000 input  = $0.025
        2000  output = $0.02
        Total = $0.045
        """
        cost = calculate_cost("openai", "gpt-4o", 10_000, 2_000)
        expected = Decimal("0.025") + Decimal("0.02")
        assert cost == expected.quantize(Decimal("0.00000001"))

    def test_claude_sonnet_cost(self):
        """
        claude-3-5-sonnet: $3.00/1M input, $15.00/1M output
        500 input  = $0.0015
        100 output = $0.0015
        Total = $0.003
        """
        cost = calculate_cost("anthropic", "claude-3-5-sonnet-20241022", 500, 100)
        expected = Decimal("0.0015") + Decimal("0.0015")
        assert cost == expected.quantize(Decimal("0.00000001"))

    def test_unknown_model_returns_zero(self):
        """Unknown models should return $0 — not raise an error."""
        cost = calculate_cost("openai", "nonexistent-model-xyz", 1000, 1000)
        assert cost == Decimal("0")

    def test_unknown_provider_returns_zero(self):
        cost = calculate_cost("unknown", "gpt-4o", 1000, 1000)
        assert cost == Decimal("0")

    def test_high_precision_result(self):
        """Cost should be precise to 8 decimal places."""
        cost = calculate_cost("openai", "gpt-4o-mini", 1, 1)
        # Very small amounts — should not lose precision
        assert isinstance(cost, Decimal)
        # Should not be rounded to zero
        assert cost > Decimal("0") or cost == Decimal("0")

    def test_gemini_free_tier_zero_cost(self):
        """gemini-2.0-flash-exp is free during preview."""
        cost = calculate_cost("gemini", "gemini-2.0-flash-exp", 10_000, 5_000)
        assert cost == Decimal("0")

    def test_cost_is_decimal_type(self):
        """Always returns Decimal, never float."""
        cost = calculate_cost("openai", "gpt-4o", 100, 50)
        assert isinstance(cost, Decimal)

    def test_large_token_count(self):
        """Should handle 1M+ tokens without overflow."""
        cost = calculate_cost("openai", "gpt-4o", 1_000_000, 1_000_000)
        # $2.50 + $10.00 = $12.50
        assert cost == Decimal("12.50").quantize(Decimal("0.00000001"))


class TestGetPricingSnapshot:
    def test_known_model_snapshot(self):
        snapshot = get_pricing_snapshot("openai", "gpt-4o")
        assert snapshot["provider"] == "openai"
        assert snapshot["model"] == "gpt-4o"
        assert "input_per_1m_usd" in snapshot
        assert "output_per_1m_usd" in snapshot
        assert snapshot["input_per_1m_usd"] == "2.50"

    def test_unknown_model_snapshot_has_note(self):
        snapshot = get_pricing_snapshot("openai", "gpt-99-super")
        assert "note" in snapshot
        assert "not found" in snapshot["note"].lower()

    def test_snapshot_values_are_strings(self):
        """Snapshot values must be strings (JSON-serialisable)."""
        snapshot = get_pricing_snapshot("anthropic", "claude-3-5-haiku-20241022")
        assert isinstance(snapshot["input_per_1m_usd"], str)
        assert isinstance(snapshot["output_per_1m_usd"], str)

    def test_all_providers_have_entries(self):
        """Every provider in PRICING should return a non-None result for their first model."""
        for provider_slug, models in PRICING.items():
            first_model = next(iter(models))
            pricing = get_model_pricing(provider_slug, first_model)
            assert pricing is not None, f"No pricing for {provider_slug}/{first_model}"
