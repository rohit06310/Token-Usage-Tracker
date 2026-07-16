"""
Integration tests: insert dummy UsageLog and read it back.
Confirms DB + ORM + Docker setup work end-to-end.
"""

import uuid
from decimal import Decimal

import pytest

from app.models.provider import Provider
from app.models.usage_log import UsageLog


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_provider(db_session) -> Provider:
    """Insert a provider for use in usage log tests."""
    provider = Provider(
        name="Test Provider",
        slug="test-provider",
        base_url="https://api.test.com",
        notes="For testing only",
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider


# ---------------------------------------------------------------------------
# ORM integration tests
# ---------------------------------------------------------------------------

class TestUsageLogORM:
    def test_insert_and_read_back(self, db_session, sample_provider):
        """
        Core smoke test: insert a UsageLog, read it back, verify all fields.
        """
        log = UsageLog(
            provider_id=sample_provider.id,
            model="gpt-4o",
            tokens_in=150,
            tokens_out=75,
            cost=Decimal("0.00225"),
            project_tag="phase1-test",
            raw_response={"usage": {"prompt_tokens": 150, "completion_tokens": 75}},
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        # Read back
        fetched = db_session.query(UsageLog).filter(UsageLog.id == log.id).first()

        assert fetched is not None
        assert fetched.model == "gpt-4o"
        assert fetched.tokens_in == 150
        assert fetched.tokens_out == 75
        assert fetched.cost == Decimal("0.00225")
        assert fetched.project_tag == "phase1-test"
        assert fetched.raw_response == {"usage": {"prompt_tokens": 150, "completion_tokens": 75}}
        assert fetched.created_at is not None

    def test_total_tokens_property(self, db_session, sample_provider):
        log = UsageLog(
            provider_id=sample_provider.id,
            model="claude-3-5-sonnet-20241022",
            tokens_in=200,
            tokens_out=100,
            cost=Decimal("0.003"),
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        assert log.total_tokens == 300

    def test_nullable_fields(self, db_session, sample_provider):
        """project_tag and raw_response should be nullable."""
        log = UsageLog(
            provider_id=sample_provider.id,
            model="gemini-1.5-flash",
            tokens_in=50,
            tokens_out=30,
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        assert log.project_tag is None
        assert log.raw_response is None

    def test_multiple_logs_per_provider(self, db_session, sample_provider):
        for i in range(5):
            log = UsageLog(
                provider_id=sample_provider.id,
                model=f"model-{i}",
                tokens_in=i * 10,
                tokens_out=i * 5,
            )
            db_session.add(log)
        db_session.commit()

        count = db_session.query(UsageLog).filter(
            UsageLog.provider_id == sample_provider.id
        ).count()
        assert count == 5


# ---------------------------------------------------------------------------
# API endpoint tests for usage logs
# ---------------------------------------------------------------------------

class TestUsageAPI:
    def test_list_usage_requires_auth(self, client):
        response = client.get("/api/v1/usage/")
        assert response.status_code == 401

    def test_list_usage_authenticated(self, authed_client):
        response = authed_client.get("/api/v1/usage/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_usage_summary_authenticated(self, authed_client):
        response = authed_client.get("/api/v1/usage/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_calls" in data
        assert "total_tokens_in" in data
        assert "total_cost" in data
