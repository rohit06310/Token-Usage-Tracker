"""
Reconciliation service.
Compares self-logged usage against provider-reported usage and records the result.
Updates provider confidence level based on history.
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.provider import Provider
from app.models.usage_log import UsageLog
from app.models.provider_reported_usage import ProviderReportedUsage
from app.models.reconciliation_result import ReconciliationResult

logger = logging.getLogger(__name__)


def reconcile_provider_usage(db: Session) -> None:
    """
    Find provider reported usage records that haven't been reconciled yet,
    compare them with our internal usage logs, and create reconciliation results.
    Also updates the provider's confidence level.
    """
    providers = db.query(Provider).all()
    
    for provider in providers:
        _reconcile_for_provider(db, provider)


def _reconcile_for_provider(db: Session, provider: Provider) -> None:
    """
    Reconciles usage for a specific provider.
    For providers without billing APIs (Groq, Gemini), we mark as 'no_official_data'.
    """
    if provider.slug in ["groq", "gemini"]:
        # Just update confidence to self_logged_only if not already
        if provider.confidence_level != "self_logged_only":
            provider.confidence_level = "self_logged_only"
            db.commit()
        return

    # For OpenAI/Anthropic, find reported usage records from the last 14 days
    # that don't have a matching reconciliation result.
    fourteen_days_ago = datetime.now(timezone.utc) - timedelta(days=14)
    
    reported_records = (
        db.query(ProviderReportedUsage)
        .filter(ProviderReportedUsage.provider_id == provider.id)
        .filter(ProviderReportedUsage.period_start >= fourteen_days_ago)
        .order_by(ProviderReportedUsage.period_start.asc())
        .all()
    )

    for reported in reported_records:
        # Check if we already reconciled this period
        existing_result = (
            db.query(ReconciliationResult)
            .filter(
                ReconciliationResult.provider_id == provider.id,
                ReconciliationResult.period_start == reported.period_start,
                ReconciliationResult.period_end == reported.period_end,
            )
            .first()
        )
        if existing_result:
            continue

        # Calculate our self-logged total
        self_logged_total = (
            db.query(func.sum(UsageLog.tokens_in + UsageLog.tokens_out))
            .filter(
                UsageLog.provider_id == provider.id,
                UsageLog.created_at >= reported.period_start,
                UsageLog.created_at <= reported.period_end,
                UsageLog.status == "success",  # Only count successful calls
            )
            .scalar()
        ) or 0

        provider_reported_tokens = reported.total_tokens or 0
        diff = provider_reported_tokens - self_logged_total
        
        if provider_reported_tokens == 0:
            percent_diff = Decimal("0") if self_logged_total == 0 else Decimal("100")
        else:
            percent_diff = (Decimal(abs(diff)) / Decimal(provider_reported_tokens)) * 100
            percent_diff = percent_diff.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # Matched if difference is within 2%
        status = "matched" if percent_diff <= Decimal("2.0") else "mismatched"

        result = ReconciliationResult(
            provider_id=provider.id,
            period_start=reported.period_start,
            period_end=reported.period_end,
            self_logged_tokens=self_logged_total,
            provider_reported_tokens=provider_reported_tokens,
            difference=diff,
            percent_diff=percent_diff,
            status=status,
            checked_at=datetime.now(timezone.utc),
        )
        db.add(result)
        db.commit()
        
        logger.info(
            "Reconciled %s for period %s: self=%d reported=%d diff=%d (%.2f%%) status=%s",
            provider.slug,
            reported.period_start.date(),
            self_logged_total,
            provider_reported_tokens,
            diff,
            percent_diff,
            status,
        )

    _update_confidence_level(db, provider)


def _update_confidence_level(db: Session, provider: Provider) -> None:
    """
    Update confidence level based on recent reconciliation history.
    Requires the last 3 periods to be 'matched' to become 'verified'.
    If any of the last 3 are 'mismatched', becomes 'unreliable'.
    """
    recent_results = (
        db.query(ReconciliationResult)
        .filter(ReconciliationResult.provider_id == provider.id)
        .order_by(ReconciliationResult.period_start.desc())
        .limit(3)
        .all()
    )

    if not recent_results:
        return

    mismatches = sum(1 for r in recent_results if r.status == "mismatched")
    matches = sum(1 for r in recent_results if r.status == "matched")

    new_level = provider.confidence_level

    if mismatches > 0:
        new_level = "unreliable"
    elif matches == 3:
        new_level = "verified"
    else:
        new_level = "self_logged_only"

    if new_level != provider.confidence_level:
        logger.info(
            "Provider %s confidence changed from %s to %s",
            provider.slug,
            provider.confidence_level,
            new_level,
        )
        provider.confidence_level = new_level
        db.commit()
