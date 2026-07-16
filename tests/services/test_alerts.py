"""Tests for the alerts service."""

import pytest
from unittest.mock import patch, AsyncMock
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from uuid import UUID

from app.models.provider import Provider
from app.models.rate_limit import RateLimit
from app.models.alert_sent import AlertSent
from app.models.user import User
from app.services.alerts import check_thresholds_and_alert


TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def mock_provider(db_session):
    provider = Provider(
        name="Test Alerts Provider",
        slug="test-alerts",
    )
    db_session.add(provider)
    db_session.commit()
    return provider


@pytest.fixture
def mock_user(db_session):
    """Create a user so the alerts loop has someone to iterate over."""
    user = User(
        id=TEST_USER_ID,
        email="test-alerts@example.com",
        hashed_password="$2b$12$fakehash",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.mark.asyncio
@patch("app.services.alerts.send_alert")
@patch("app.services.alerts.calculate_remaining_quota")
async def test_check_thresholds_sends_alert(mock_calc, mock_send, db_session, mock_provider, mock_user):
    mock_calc.return_value = {
        "tpm": {
            "limit": 1000,
            "used": 850,
            "remaining": 150,
            "percent_used": 85.0
        }
    }

    await check_thresholds_and_alert(db_session)

    # Since 85% > 80%, an alert should be dispatched (once per user × provider)
    mock_send.assert_called_once()

    # An AlertSent record should be created
    record = db_session.query(AlertSent).first()
    assert record is not None
    assert record.alert_type == "tpm"
    assert record.threshold_percent == Decimal("80")


@pytest.mark.asyncio
@patch("app.services.alerts.send_alert")
@patch("app.services.alerts.calculate_remaining_quota")
async def test_deduplication_prevents_duplicate_alerts(mock_calc, mock_send, db_session, mock_provider, mock_user):
    mock_calc.return_value = {
        "tpm": {
            "limit": 1000,
            "used": 850,
            "remaining": 150,
            "percent_used": 85.0
        }
    }

    # Insert a recent alert
    alert = AlertSent(
        provider_id=mock_provider.id,
        alert_type="tpm",
        threshold_percent=Decimal("80"),
        window_start=datetime.now(timezone.utc) - timedelta(minutes=2),
    )
    db_session.add(alert)
    db_session.commit()

    await check_thresholds_and_alert(db_session)

    # Should not send again
    mock_send.assert_not_called()
