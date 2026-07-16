"""Tests for the reconciliation service."""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest

from app.models.provider import Provider
from app.models.provider_reported_usage import ProviderReportedUsage
from app.models.usage_log import UsageLog
from app.models.reconciliation_result import ReconciliationResult
from app.services.reconciliation import reconcile_provider_usage


@pytest.fixture
def mock_provider(db_session):
    provider = Provider(
        name="Test Provider",
        slug="openai",
        confidence_level="self_logged_only"
    )
    db_session.add(provider)
    db_session.commit()
    return provider


def test_reconcile_no_official_data(db_session, mock_provider):
    mock_provider.slug = "groq"
    db_session.commit()

    reconcile_provider_usage(db_session)

    # Groq should simply remain or become self_logged_only
    assert mock_provider.confidence_level == "self_logged_only"
    
    # No results created
    results = db_session.query(ReconciliationResult).all()
    assert len(results) == 0


def test_reconcile_match(db_session, mock_provider):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=1)
    end = now

    # Add reported usage
    reported = ProviderReportedUsage(
        provider_id=mock_provider.id,
        period_start=start,
        period_end=end,
        total_tokens=1000,
        fetched_at=now,
        source="openai"
    )
    db_session.add(reported)

    # Add self logged usage
    log = UsageLog(
        provider_id=mock_provider.id,
        model="gpt-4o",
        status="success",
        tokens_in=500,
        tokens_out=490, # 990 total -> 10 diff -> 1% diff
        cost=Decimal("0.1")
    )
    log.created_at = start + timedelta(hours=1)
    db_session.add(log)
    db_session.commit()

    reconcile_provider_usage(db_session)

    result = db_session.query(ReconciliationResult).first()
    assert result is not None
    assert result.status == "matched"
    assert result.percent_diff == Decimal("1.0000")
    assert result.difference == 10
    
    # Needs 3 matches to become verified
    assert mock_provider.confidence_level == "self_logged_only"


def test_reconcile_mismatch_updates_confidence(db_session, mock_provider):
    mock_provider.confidence_level = "verified"
    db_session.commit()

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=1)
    end = now

    reported = ProviderReportedUsage(
        provider_id=mock_provider.id,
        period_start=start,
        period_end=end,
        total_tokens=1000,
        fetched_at=now,
        source="openai"
    )
    db_session.add(reported)

    # Add self logged usage (massive difference)
    log = UsageLog(
        provider_id=mock_provider.id,
        model="gpt-4o",
        status="success",
        tokens_in=100,
        tokens_out=100, # 200 total -> 80% diff
        cost=Decimal("0.1")
    )
    log.created_at = start + timedelta(hours=1)
    db_session.add(log)
    db_session.commit()

    reconcile_provider_usage(db_session)

    result = db_session.query(ReconciliationResult).first()
    assert result.status == "mismatched"
    
    # Should become unreliable
    assert mock_provider.confidence_level == "unreliable"
