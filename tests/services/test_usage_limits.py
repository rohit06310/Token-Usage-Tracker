"""Tests for the usage limits service."""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID
import pytest

from app.models.provider import Provider
from app.models.rate_limit import RateLimit
from app.models.usage_log import UsageLog
from app.services.usage_limits import calculate_remaining_quota

# Sentinel user id used across these tests
TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def mock_provider(db_session):
    provider = Provider(
        name="Test Limits Provider",
        slug="test-limits",
    )
    db_session.add(provider)
    db_session.commit()
    return provider


def test_calculate_remaining_quota_no_limits(db_session, mock_provider):
    res = calculate_remaining_quota(db_session, mock_provider.id, TEST_USER_ID)
    assert res == {}


def test_calculate_remaining_quota_with_limits(db_session, mock_provider):
    now = datetime.now(timezone.utc)
    
    # Add rate limit
    limit = RateLimit(
        provider_id=mock_provider.id,
        tier_name="Tier 1",
        rpm=10,
        tpm=1000,
        rpd=100,
        effective_date=now.date() - timedelta(days=1)
    )
    db_session.add(limit)
    
    # Add some usage
    log = UsageLog(
        provider_id=mock_provider.id,
        user_id=TEST_USER_ID,
        model="gpt-4o",
        status="success",
        tokens_in=200,
        tokens_out=100, # total 300
        cost=Decimal("0")
    )
    log.created_at = now - timedelta(seconds=10) # within last minute
    db_session.add(log)
    db_session.commit()

    res = calculate_remaining_quota(db_session, mock_provider.id, TEST_USER_ID)
    
    assert "tpm" in res
    assert res["tpm"]["limit"] == 1000
    assert res["tpm"]["used"] == 300
    assert res["tpm"]["remaining"] == 700
    assert res["tpm"]["percent_used"] == 30.0

    assert "rpm" in res
    assert res["rpm"]["limit"] == 10
    assert res["rpm"]["used"] == 1
    assert res["rpm"]["remaining"] == 9

    assert "rpd" in res
    assert res["rpd"]["used"] == 1
