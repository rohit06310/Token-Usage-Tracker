"""
Integration tests for GroqAdapter.
All API calls are mocked — no real network calls or API keys required.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.adapters.groq_adapter import GroqAdapter, PROVIDER_SLUG
from app.models.usage_log import CallStatus


PROVIDER_ID = uuid.uuid4()
FAKE_API_KEY = "gsk_fake_groq_key_for_testing"
MODEL = "llama-3.1-8b-instant"


def make_groq_response(
    content: str = "Hello from Groq!",
    prompt_tokens: int = 60,
    completion_tokens: int = 25,
    model: str = MODEL,
) -> MagicMock:
    """Groq uses the same OpenAI-compatible shape."""
    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    usage.total_tokens = prompt_tokens + completion_tokens

    message = MagicMock()
    message.content = content
    message.role = "assistant"

    choice = MagicMock()
    choice.message = message
    choice.finish_reason = "stop"
    choice.index = 0

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    response.model = model
    response.id = "groq-mock-id"

    response.model_dump.return_value = {
        "id": "groq-mock-id",
        "model": model,
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
    return response


@pytest.fixture
def adapter():
    return GroqAdapter(provider_id=PROVIDER_ID, api_key=FAKE_API_KEY)


@pytest.fixture
def sample_provider_groq(db_session):
    from app.models.provider import Provider
    provider = Provider(
        name="Groq (test)",
        slug="groq-test",
        base_url="https://api.groq.com/openai/v1",
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider


class TestGroqExtractUsage:
    def test_extracts_openai_compatible_usage(self, adapter):
        raw = {"usage": {"prompt_tokens": 70, "completion_tokens": 30}}
        usage = adapter.extract_usage(raw)
        assert usage["tokens_in"] == 70
        assert usage["tokens_out"] == 30

    def test_missing_usage_returns_zeros(self, adapter):
        usage = adapter.extract_usage({})
        assert usage["tokens_in"] == 0
        assert usage["tokens_out"] == 0


class TestGroqSendRequest:
    @pytest.mark.asyncio
    async def test_successful_call(self, adapter):
        mock_response = make_groq_response(
            content="Fast Llama response!",
            prompt_tokens=60,
            completion_tokens=25,
        )
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("groq.AsyncGroq", return_value=mock_client):
            response = await adapter.send_request(prompt="Hello", model=MODEL)

        assert response.content == "Fast Llama response!"
        assert response.tokens_in == 60
        assert response.tokens_out == 25
        assert response.provider_slug == PROVIDER_SLUG

    @pytest.mark.asyncio
    async def test_cost_calculation(self, adapter):
        """llama-3.1-8b-instant: $0.05/1M in, $0.08/1M out"""
        mock_response = make_groq_response(
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
        )
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("groq.AsyncGroq", return_value=mock_client):
            response = await adapter.send_request(prompt="test", model=MODEL)

        # $0.05 + $0.08 = $0.13
        expected = Decimal("0.13").quantize(Decimal("0.00000001"))
        assert response.cost == expected

    @pytest.mark.asyncio
    async def test_pricing_snapshot_in_raw_response(self, adapter):
        mock_response = make_groq_response()
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("groq.AsyncGroq", return_value=mock_client):
            response = await adapter.send_request(prompt="test", model=MODEL)

        assert "_pricing_used" in response.raw_response
        assert response.raw_response["_pricing_used"]["provider"] == "groq"


class TestGroqExecute:
    @pytest.mark.asyncio
    async def test_success_logged_to_db(self, adapter, db_session, sample_provider_groq):
        adapter.provider_id = sample_provider_groq.id

        mock_response = make_groq_response(prompt_tokens=60, completion_tokens=25)
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("groq.AsyncGroq", return_value=mock_client):
            response = await adapter.execute(prompt="test", model=MODEL, db=db_session)

        assert response.status == CallStatus.SUCCESS

        from app.models.usage_log import UsageLog
        log = db_session.query(UsageLog).filter(
            UsageLog.provider_id == sample_provider_groq.id
        ).first()
        assert log is not None
        assert log.status == CallStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_rate_limit_error_logged_as_failed(self, adapter, db_session, sample_provider_groq):
        adapter.provider_id = sample_provider_groq.id

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Rate limit exceeded: 6000 tokens per minute")
        )

        with patch("groq.AsyncGroq", return_value=mock_client):
            response = await adapter.execute(prompt="test", model=MODEL, db=db_session)

        assert response.status == CallStatus.FAILED
        assert response.content == ""

        from app.models.usage_log import UsageLog
        log = db_session.query(UsageLog).filter(
            UsageLog.provider_id == sample_provider_groq.id
        ).first()
        assert log.status == CallStatus.FAILED
        assert "Rate limit" in log.raw_response.get("error", "")
