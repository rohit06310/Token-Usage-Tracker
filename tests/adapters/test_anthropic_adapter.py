"""
Integration tests for AnthropicAdapter.
All API calls are mocked — no real network calls or API keys required.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.adapters.anthropic_adapter import AnthropicAdapter, PROVIDER_SLUG
from app.models.usage_log import CallStatus


PROVIDER_ID = uuid.uuid4()
FAKE_API_KEY = "sk-ant-fake-key-for-testing"
MODEL = "claude-3-5-haiku-20241022"


# ---------------------------------------------------------------------------
# Helper — build mock Anthropic response
# ---------------------------------------------------------------------------

def make_anthropic_response(
    content: str = "Hello from mock Claude!",
    input_tokens: int = 80,
    output_tokens: int = 35,
    model: str = MODEL,
) -> MagicMock:
    """Build a mock anthropic.Message response matching SDK shape."""
    usage = MagicMock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens

    content_block = MagicMock()
    content_block.text = content
    content_block.type = "text"

    response = MagicMock()
    response.content = [content_block]
    response.usage = usage
    response.model = model
    response.id = "msg_mock_id"
    response.type = "message"
    response.role = "assistant"
    response.stop_reason = "end_turn"

    response.model_dump.return_value = {
        "id": "msg_mock_id",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": [{"type": "text", "text": content}],
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
        "stop_reason": "end_turn",
    }
    return response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def adapter():
    return AnthropicAdapter(provider_id=PROVIDER_ID, api_key=FAKE_API_KEY)


@pytest.fixture
def sample_provider_anthropic(db_session):
    from app.models.provider import Provider
    provider = Provider(
        name="Anthropic (test)",
        slug="anthropic-test",
        base_url="https://api.anthropic.com",
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider


# ---------------------------------------------------------------------------
# Tests: extract_usage
# ---------------------------------------------------------------------------

class TestAnthropicExtractUsage:
    def test_extracts_input_and_output_tokens(self, adapter):
        raw = {
            "usage": {
                "input_tokens": 150,
                "output_tokens": 60,
            }
        }
        usage = adapter.extract_usage(raw)
        assert usage["tokens_in"] == 150
        assert usage["tokens_out"] == 60

    def test_missing_usage_returns_zeros(self, adapter):
        usage = adapter.extract_usage({})
        assert usage["tokens_in"] == 0
        assert usage["tokens_out"] == 0

    def test_null_usage_returns_zeros(self, adapter):
        usage = adapter.extract_usage({"usage": None})
        assert usage["tokens_in"] == 0
        assert usage["tokens_out"] == 0


# ---------------------------------------------------------------------------
# Tests: send_request
# ---------------------------------------------------------------------------

class TestAnthropicSendRequest:
    @pytest.mark.asyncio
    async def test_successful_call_extracts_content(self, adapter):
        mock_response = make_anthropic_response(
            content="Bonjour from Claude!",
            input_tokens=80,
            output_tokens=35,
        )
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            response = await adapter.send_request(prompt="Say hello in French", model=MODEL)

        assert response.content == "Bonjour from Claude!"
        assert response.tokens_in == 80
        assert response.tokens_out == 35
        assert response.provider_slug == PROVIDER_SLUG

    @pytest.mark.asyncio
    async def test_cost_calculated_correctly(self, adapter):
        """claude-3-5-haiku: $0.80/1M input, $4.00/1M output"""
        mock_response = make_anthropic_response(
            input_tokens=1_000_000,
            output_tokens=1_000_000,
        )
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            response = await adapter.send_request(prompt="test", model=MODEL)

        # $0.80 + $4.00 = $4.80
        expected = Decimal("4.80").quantize(Decimal("0.00000001"))
        assert response.cost == expected

    @pytest.mark.asyncio
    async def test_system_prompt_passed_correctly(self, adapter):
        mock_response = make_anthropic_response()
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            await adapter.send_request(
                prompt="Hello",
                model=MODEL,
                system_prompt="Be concise.",
            )

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs.get("system") == "Be concise."

    @pytest.mark.asyncio
    async def test_max_tokens_default_applied(self, adapter):
        mock_response = make_anthropic_response()
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            await adapter.send_request(prompt="test", model=MODEL)

        call_kwargs = mock_client.messages.create.call_args[1]
        assert "max_tokens" in call_kwargs
        assert call_kwargs["max_tokens"] == 1024  # DEFAULT_MAX_TOKENS


# ---------------------------------------------------------------------------
# Tests: execute()
# ---------------------------------------------------------------------------

class TestAnthropicExecute:
    @pytest.mark.asyncio
    async def test_success_logs_correct_status(self, adapter, db_session, sample_provider_anthropic):
        adapter.provider_id = sample_provider_anthropic.id

        mock_response = make_anthropic_response(input_tokens=50, output_tokens=20)
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            response = await adapter.execute(
                prompt="test", model=MODEL, db=db_session
            )

        assert response.status == CallStatus.SUCCESS

        from app.models.usage_log import UsageLog
        log = db_session.query(UsageLog).filter(
            UsageLog.provider_id == sample_provider_anthropic.id
        ).first()
        assert log.status == CallStatus.SUCCESS
        assert log.tokens_in == 50
        assert log.tokens_out == 20

    @pytest.mark.asyncio
    async def test_api_error_logs_failed_status(self, adapter, db_session, sample_provider_anthropic):
        adapter.provider_id = sample_provider_anthropic.id

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            side_effect=Exception("Anthropic API 529 overloaded")
        )

        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            response = await adapter.execute(
                prompt="test", model=MODEL, db=db_session
            )

        assert response.status == CallStatus.FAILED
        assert response.tokens_in == 0
        assert response.cost == Decimal("0")

        from app.models.usage_log import UsageLog
        log = db_session.query(UsageLog).filter(
            UsageLog.provider_id == sample_provider_anthropic.id
        ).first()
        assert log.status == CallStatus.FAILED
        assert "529" in log.raw_response.get("error", "")
