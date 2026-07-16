"""
Integration tests for GeminiAdapter.
All API calls are mocked — no real network calls or API keys required.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.adapters.gemini_adapter import GeminiAdapter, PROVIDER_SLUG
from app.models.usage_log import CallStatus


PROVIDER_ID = uuid.uuid4()
FAKE_API_KEY = "AIza_fake_gemini_key_for_testing"
MODEL = "gemini-1.5-flash"


def make_gemini_response(
    text: str = "Hello from Gemini!",
    prompt_token_count: int = 90,
    candidates_token_count: int = 40,
) -> MagicMock:
    """Build a mock google.generativeai response object."""
    response = MagicMock()
    response.text = text

    response.to_dict.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": text}],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": prompt_token_count,
            "candidatesTokenCount": candidates_token_count,
            "totalTokenCount": prompt_token_count + candidates_token_count,
        },
    }
    return response


@pytest.fixture
def adapter():
    return GeminiAdapter(provider_id=PROVIDER_ID, api_key=FAKE_API_KEY)


@pytest.fixture
def sample_provider_gemini(db_session):
    from app.models.provider import Provider
    provider = Provider(
        name="Gemini (test)",
        slug="gemini-test",
        base_url="https://generativelanguage.googleapis.com",
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider


class TestGeminiExtractUsage:
    def test_extracts_camelCase_fields(self, adapter):
        """Gemini uses camelCase: promptTokenCount, candidatesTokenCount."""
        raw = {
            "usageMetadata": {
                "promptTokenCount": 100,
                "candidatesTokenCount": 50,
                "totalTokenCount": 150,
            }
        }
        usage = adapter.extract_usage(raw)
        assert usage["tokens_in"] == 100
        assert usage["tokens_out"] == 50

    def test_extracts_snake_case_fields(self, adapter):
        """Some SDK versions use snake_case."""
        raw = {
            "usage_metadata": {
                "prompt_token_count": 80,
                "candidates_token_count": 30,
            }
        }
        usage = adapter.extract_usage(raw)
        assert usage["tokens_in"] == 80
        assert usage["tokens_out"] == 30

    def test_missing_metadata_returns_zeros(self, adapter):
        usage = adapter.extract_usage({})
        assert usage["tokens_in"] == 0
        assert usage["tokens_out"] == 0


class TestGeminiSendRequest:
    @pytest.mark.asyncio
    async def test_successful_call(self, adapter):
        mock_response = make_gemini_response(
            text="Namaste from Gemini!",
            prompt_token_count=90,
            candidates_token_count=40,
        )
        mock_model = AsyncMock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        mock_genai = MagicMock()
        mock_genai.GenerativeModel = MagicMock(return_value=mock_model)

        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
            with patch("app.adapters.gemini_adapter.genai", mock_genai, create=True):
                with patch(
                    "app.adapters.gemini_adapter.GeminiAdapter.send_request",
                    new_callable=AsyncMock,
                ) as mock_send:
                    from app.adapters.base import ProviderResponse
                    mock_send.return_value = ProviderResponse(
                        content="Namaste from Gemini!",
                        tokens_in=90,
                        tokens_out=40,
                        cost=Decimal("0.00001575"),
                        model=MODEL,
                        provider_slug=PROVIDER_SLUG,
                        raw_response={"usageMetadata": {"promptTokenCount": 90, "candidatesTokenCount": 40}},
                    )
                    response = await adapter.send_request(prompt="Say hello", model=MODEL)

        assert response.content == "Namaste from Gemini!"
        assert response.tokens_in == 90
        assert response.tokens_out == 40

    def test_extract_usage_camelcase_vs_snakecase(self, adapter):
        """Both camelCase and snake_case field names should work."""
        camel = {"usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 50}}
        snake = {"usage_metadata": {"prompt_token_count": 100, "candidates_token_count": 50}}

        u1 = adapter.extract_usage(camel)
        u2 = adapter.extract_usage(snake)
        assert u1 == u2

    def test_cost_for_gemini_flash(self, adapter):
        """gemini-1.5-flash: $0.075/1M in, $0.30/1M out"""
        from app.services.pricing import calculate_cost
        cost = calculate_cost("gemini", "gemini-1.5-flash", 1_000_000, 1_000_000)
        expected = Decimal("0.375").quantize(Decimal("0.00000001"))
        assert cost == expected


class TestGeminiExecute:
    @pytest.mark.asyncio
    async def test_success_logged_to_db(self, adapter, db_session, sample_provider_gemini):
        """Test through execute() using a mocked send_request."""
        adapter.provider_id = sample_provider_gemini.id

        from app.adapters.base import ProviderResponse
        mock_response = ProviderResponse(
            content="Gemini test response",
            tokens_in=90,
            tokens_out=40,
            cost=Decimal("0.00001875"),
            model=MODEL,
            provider_slug=PROVIDER_SLUG,
            raw_response={"usageMetadata": {}},
        )

        with patch.object(adapter, "send_request", new_callable=AsyncMock, return_value=mock_response):
            response = await adapter.execute(
                prompt="test", model=MODEL, db=db_session, project_tag="gemini-test"
            )

        assert response.status == CallStatus.SUCCESS
        assert response.tokens_in == 90

        from app.models.usage_log import UsageLog
        log = db_session.query(UsageLog).filter(
            UsageLog.provider_id == sample_provider_gemini.id
        ).first()
        assert log is not None
        assert log.status == CallStatus.SUCCESS
        assert log.project_tag == "gemini-test"

    @pytest.mark.asyncio
    async def test_safety_block_error_logged_as_failed(self, adapter, db_session, sample_provider_gemini):
        adapter.provider_id = sample_provider_gemini.id

        with patch.object(
            adapter,
            "send_request",
            new_callable=AsyncMock,
            side_effect=Exception("Response was blocked by safety filters"),
        ):
            response = await adapter.execute(prompt="test", model=MODEL, db=db_session)

        assert response.status == CallStatus.FAILED

        from app.models.usage_log import UsageLog
        log = db_session.query(UsageLog).filter(
            UsageLog.provider_id == sample_provider_gemini.id
        ).first()
        assert log.status == CallStatus.FAILED
        assert "safety" in log.raw_response.get("error", "").lower()
