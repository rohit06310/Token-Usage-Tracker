"""
Integration tests for OpenAIAdapter.
All API calls are mocked — no real network calls or API keys required.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.adapters.openai_adapter import OpenAIAdapter, PROVIDER_SLUG
from app.models.usage_log import CallStatus


PROVIDER_ID = uuid.uuid4()
FAKE_API_KEY = "sk-fake-openai-key-for-testing"
MODEL = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Helpers — build mock OpenAI response objects
# ---------------------------------------------------------------------------

def make_openai_response(
    content: str = "Hello from mock!",
    prompt_tokens: int = 120,
    completion_tokens: int = 45,
    model: str = MODEL,
) -> MagicMock:
    """Build a mock openai.ChatCompletion response matching SDK shape."""
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
    response.id = "chatcmpl-mock-id"
    response.object = "chat.completion"

    # model_dump() returns the dict we store in raw_response
    response.model_dump.return_value = {
        "id": "chatcmpl-mock-id",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
    return response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def adapter():
    return OpenAIAdapter(provider_id=PROVIDER_ID, api_key=FAKE_API_KEY)


@pytest.fixture
def mock_db(db_session):
    """Use the conftest SQLite session as the DB."""
    return db_session


# ---------------------------------------------------------------------------
# Tests: extract_usage
# ---------------------------------------------------------------------------

class TestOpenAIExtractUsage:
    def test_extracts_prompt_and_completion_tokens(self, adapter):
        raw = {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            }
        }
        usage = adapter.extract_usage(raw)
        assert usage["tokens_in"] == 100
        assert usage["tokens_out"] == 50

    def test_missing_usage_returns_zeros(self, adapter):
        usage = adapter.extract_usage({})
        assert usage["tokens_in"] == 0
        assert usage["tokens_out"] == 0

    def test_partial_usage_fields(self, adapter):
        raw = {"usage": {"prompt_tokens": 200}}
        usage = adapter.extract_usage(raw)
        assert usage["tokens_in"] == 200
        assert usage["tokens_out"] == 0

    def test_null_usage_returns_zeros(self, adapter):
        usage = adapter.extract_usage({"usage": None})
        assert usage["tokens_in"] == 0
        assert usage["tokens_out"] == 0


# ---------------------------------------------------------------------------
# Tests: send_request (mocked SDK)
# ---------------------------------------------------------------------------

class TestOpenAISendRequest:
    @pytest.mark.asyncio
    async def test_successful_call_returns_response(self, adapter):
        mock_response = make_openai_response(
            content="Test response",
            prompt_tokens=120,
            completion_tokens=45,
        )
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            response = await adapter.send_request(
                prompt="Say hello",
                model=MODEL,
            )

        assert response.content == "Test response"
        assert response.tokens_in == 120
        assert response.tokens_out == 45
        assert response.model == MODEL
        assert response.provider_slug == PROVIDER_SLUG
        assert response.cost > Decimal("0")

    @pytest.mark.asyncio
    async def test_cost_calculated_correctly(self, adapter):
        """gpt-4o-mini: $0.15/1M in, $0.60/1M out"""
        mock_response = make_openai_response(
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
        )
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            response = await adapter.send_request(prompt="test", model=MODEL)

        # 1M input @ $0.15 + 1M output @ $0.60 = $0.75
        expected = Decimal("0.75").quantize(Decimal("0.00000001"))
        assert response.cost == expected

    @pytest.mark.asyncio
    async def test_pricing_snapshot_embedded_in_raw_response(self, adapter):
        mock_response = make_openai_response()
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            response = await adapter.send_request(prompt="test", model=MODEL)

        assert "_pricing_used" in response.raw_response
        assert response.raw_response["_pricing_used"]["model"] == MODEL
        assert "input_per_1m_usd" in response.raw_response["_pricing_used"]

    @pytest.mark.asyncio
    async def test_system_prompt_passed_to_api(self, adapter):
        mock_response = make_openai_response()
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            await adapter.send_request(
                prompt="Hello",
                model=MODEL,
                system_prompt="You are a helpful assistant.",
            )

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages", call_kwargs.args[0] if call_kwargs.args else [])
        # Find messages from the call
        all_kwargs = call_kwargs[1] if call_kwargs[1] else {}
        messages = all_kwargs.get("messages", [])
        system_msgs = [m for m in messages if m.get("role") == "system"]
        assert len(system_msgs) == 1
        assert system_msgs[0]["content"] == "You are a helpful assistant."


# ---------------------------------------------------------------------------
# Tests: execute() — full pipeline including DB logging
# ---------------------------------------------------------------------------

class TestOpenAIExecute:
    @pytest.mark.asyncio
    async def test_successful_execute_logs_to_db(self, adapter, mock_db, sample_provider_openai):
        """Full execute() pipeline: call → log to DB → return response."""
        adapter.provider_id = sample_provider_openai.id

        mock_response = make_openai_response(
            content="Hello!",
            prompt_tokens=100,
            completion_tokens=30,
        )
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            response = await adapter.execute(
                prompt="Say hello",
                model=MODEL,
                db=mock_db,
                project_tag="test-project",
            )

        assert response.status == CallStatus.SUCCESS
        assert response.content == "Hello!"
        assert response.tokens_in == 100
        assert response.tokens_out == 30

        # Verify DB row was written
        from app.models.usage_log import UsageLog
        log = mock_db.query(UsageLog).filter(
            UsageLog.provider_id == sample_provider_openai.id
        ).first()
        assert log is not None
        assert log.status == CallStatus.SUCCESS
        assert log.tokens_in == 100
        assert log.tokens_out == 30
        assert log.project_tag == "test-project"
        assert log.cost > Decimal("0")

    @pytest.mark.asyncio
    async def test_failed_call_logs_status_failed(self, adapter, mock_db, sample_provider_openai):
        """On API error, execute() logs status='failed' and does NOT re-raise."""
        adapter.provider_id = sample_provider_openai.id

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Connection timeout")
        )

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            response = await adapter.execute(
                prompt="Say hello",
                model=MODEL,
                db=mock_db,
            )

        # Should NOT raise — returns a failed ProviderResponse
        assert response.status == CallStatus.FAILED
        assert response.content == ""
        assert response.tokens_in == 0
        assert response.cost == Decimal("0")

        # Verify failed row in DB
        from app.models.usage_log import UsageLog
        log = mock_db.query(UsageLog).filter(
            UsageLog.provider_id == sample_provider_openai.id
        ).first()
        assert log is not None
        assert log.status == CallStatus.FAILED
        assert "Connection timeout" in log.raw_response.get("error", "")
        assert log.raw_response.get("_status") == "failed"

    @pytest.mark.asyncio
    async def test_execute_returns_even_if_db_fails(self, adapter, sample_provider_openai):
        """DB logging failure should not propagate to the caller."""
        adapter.provider_id = sample_provider_openai.id

        mock_response = make_openai_response()
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Create a broken DB session
        broken_db = MagicMock()
        broken_db.add = MagicMock(side_effect=Exception("DB connection lost"))

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            # Should NOT raise even when DB write fails
            response = await adapter.execute(
                prompt="test",
                model=MODEL,
                db=broken_db,
            )

        assert response.content == "Hello from mock!"


# ---------------------------------------------------------------------------
# Shared fixture for this test module
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_provider_openai(db_session):
    """Create an OpenAI provider row for testing."""
    from app.models.provider import Provider
    provider = Provider(
        name="OpenAI (test)",
        slug="openai-test",
        base_url="https://api.openai.com/v1",
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider
