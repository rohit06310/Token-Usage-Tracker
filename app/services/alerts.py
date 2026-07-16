"""
Alerts service.
Evaluates rate limits against configured thresholds and dispatches notifications
via SMTP and Slack. Handles deduplication using the `alerts_sent` table.
"""

import logging
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import httpx
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.provider import Provider
from app.models.alert_sent import AlertSent
from app.services.usage_limits import calculate_remaining_quota

logger = logging.getLogger(__name__)


async def send_alert(subject: str, message: str) -> None:
    """Send an alert via configured channels (SMTP and/or Slack)."""
    settings = get_settings()

    # Send Slack Alert
    slack_url = getattr(settings, "slack_webhook_url", None)
    if slack_url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(slack_url, json={"text": f"*{subject}*\n{message}"})
            logger.info("Sent Slack alert: %s", subject)
        except Exception as e:
            logger.error("Failed to send Slack alert: %s", e)

    # Send SMTP Alert
    smtp_server = getattr(settings, "smtp_server", None)
    if smtp_server:
        try:
            import aiosmtplib
            
            msg = EmailMessage()
            msg.set_content(message)
            msg["Subject"] = subject
            msg["From"] = getattr(settings, "smtp_user", "alerts@aiusagedashboard.com")
            msg["To"] = getattr(settings, "alert_email_to", msg["From"])

            await aiosmtplib.send(
                msg,
                hostname=smtp_server,
                port=getattr(settings, "smtp_port", 587),
                username=getattr(settings, "smtp_user", None),
                password=getattr(settings, "smtp_pass", None),
                use_tls=getattr(settings, "smtp_port", 587) == 465,
                start_tls=getattr(settings, "smtp_port", 587) == 587,
            )
            logger.info("Sent SMTP alert: %s", subject)
        except Exception as e:
            logger.error("Failed to send SMTP alert: %s", e)

    # Send Generic Webhook Alert
    generic_url = getattr(settings, "generic_webhook_url", None)
    if generic_url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(generic_url, json={"subject": subject, "message": message})
            logger.info("Sent Generic Webhook alert: %s", subject)
        except Exception as e:
            logger.error("Failed to send Generic Webhook alert: %s", e)


async def check_thresholds_and_alert(db: Session) -> None:
    """
    Check current usage against thresholds, dispatch alerts if crossed,
    and log to `alerts_sent` to prevent spamming.
    Scoped per-user: each user's usage is checked independently.
    """
    settings = get_settings()
    thresholds_str = getattr(settings, "alert_thresholds", "80,95")
    try:
        thresholds = [Decimal(t.strip()) for t in thresholds_str.split(",")]
    except ValueError:
        thresholds = [Decimal("80"), Decimal("95")]

    # Sort descending so we process highest crossed threshold first
    thresholds.sort(reverse=True)

    from app.models.user import User
    providers = db.query(Provider).all()
    users = db.query(User).all()
    now = datetime.now(timezone.utc)

    for user in users:
        for provider in providers:
            quotas = calculate_remaining_quota(db, provider.id, user.id)

            for limit_type, data in quotas.items():
                percent_used = Decimal(str(data["percent_used"]))

                # Find the highest crossed threshold
                crossed_threshold = None
                for t in thresholds:
                    if percent_used >= t:
                        crossed_threshold = t
                        break

                if crossed_threshold:
                    # Deduplication logic:
                    # For TPM/RPM (1 minute window), suppress alerts for 5 minutes.
                    # For RPD (1 day window), suppress alerts for 1 hour.
                    suppress_minutes = 60 if limit_type == "rpd" else 5
                    window_start = now - timedelta(minutes=suppress_minutes)

                    recent_alert = (
                        db.query(AlertSent)
                        .filter(
                            AlertSent.provider_id == provider.id,
                            AlertSent.user_id == user.id,
                            AlertSent.alert_type == limit_type,
                            AlertSent.threshold_percent == crossed_threshold,
                            AlertSent.sent_at >= window_start,
                        )
                        .first()
                    )

                    if not recent_alert:
                        # Dispatch alert
                        subject = (
                            f"[{provider.name}] {limit_type.upper()} Usage Alert: "
                            f"{crossed_threshold}% Threshold Reached"
                        )
                        msg = (
                            f"User: {user.email}\n"
                            f"Provider: {provider.name}\n"
                            f"Limit Type: {limit_type.upper()}\n"
                            f"Usage: {data['used']} / {data['limit']}\n"
                            f"Percent Used: {percent_used:.2f}%\n"
                        )
                        await send_alert(subject, msg)

                        # Record the alert
                        alert_record = AlertSent(
                            provider_id=provider.id,
                            user_id=user.id,
                            alert_type=limit_type,
                            threshold_percent=crossed_threshold,
                            window_start=window_start,
                            sent_at=now,
                        )
                        db.add(alert_record)
                        db.commit()
