"""
Usage limits service.
Calculates rolling window usage (RPM, TPM, RPD) against active rate limits.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.provider import Provider
from app.models.rate_limit import RateLimit
from app.models.usage_log import UsageLog


def get_active_rate_limit(db: Session, provider_id) -> Optional[RateLimit]:
    """Get the currently active rate limit for a provider."""
    return (
        db.query(RateLimit)
        .filter(
            RateLimit.provider_id == provider_id,
            RateLimit.effective_date <= datetime.now(timezone.utc).date()
        )
        .order_by(RateLimit.effective_date.desc())
        .first()
    )


def calculate_remaining_quota(db: Session, provider_id, user_id) -> Dict[str, Any]:
    """
    Calculate the remaining RPM, TPM, and RPD for a given provider and user.
    Returns a dictionary of limits and current usage.
    """
    rate_limit = get_active_rate_limit(db, provider_id)
    if not rate_limit:
        return {}

    now = datetime.now(timezone.utc)
    one_minute_ago = now - timedelta(minutes=1)
    one_day_ago = now - timedelta(days=1)

    # Calculate TPM (last 1 minute)
    used_tpm = (
        db.query(func.sum(UsageLog.tokens_in + UsageLog.tokens_out))
        .filter(
            UsageLog.provider_id == provider_id,
            UsageLog.user_id == user_id,
            UsageLog.created_at >= one_minute_ago
        )
        .scalar()
    ) or 0

    # Calculate RPM (last 1 minute)
    used_rpm = (
        db.query(func.count(UsageLog.id))
        .filter(
            UsageLog.provider_id == provider_id,
            UsageLog.user_id == user_id,
            UsageLog.created_at >= one_minute_ago
        )
        .scalar()
    ) or 0

    # Calculate RPD (last 1 day)
    used_rpd = (
        db.query(func.count(UsageLog.id))
        .filter(
            UsageLog.provider_id == provider_id,
            UsageLog.user_id == user_id,
            UsageLog.created_at >= one_day_ago
        )
        .scalar()
    ) or 0

    # Calculate Budget USD (current calendar month)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    used_budget = (
        db.query(func.sum(UsageLog.cost))
        .filter(
            UsageLog.provider_id == provider_id,
            UsageLog.user_id == user_id,
            UsageLog.created_at >= start_of_month
        )
        .scalar()
    ) or 0.0

    result = {}
    
    if rate_limit.tpm is not None:
        result["tpm"] = {
            "limit": rate_limit.tpm,
            "used": used_tpm,
            "remaining": max(0, rate_limit.tpm - used_tpm),
            "percent_used": (used_tpm / rate_limit.tpm) * 100 if rate_limit.tpm > 0 else 100.0,
        }
        
    if rate_limit.rpm is not None:
        result["rpm"] = {
            "limit": rate_limit.rpm,
            "used": used_rpm,
            "remaining": max(0, rate_limit.rpm - used_rpm),
            "percent_used": (used_rpm / rate_limit.rpm) * 100 if rate_limit.rpm > 0 else 100.0,
        }
        
    if rate_limit.rpd is not None:
        result["rpd"] = {
            "limit": rate_limit.rpd,
            "used": used_rpd,
            "remaining": max(0, rate_limit.rpd - used_rpd),
            "percent_used": (used_rpd / rate_limit.rpd) * 100 if rate_limit.rpd > 0 else 100.0,
        }

    if rate_limit.budget_usd is not None:
        budget = float(rate_limit.budget_usd)
        used_b = float(used_budget)
        result["budget"] = {
            "limit": budget,
            "used": used_b,
            "remaining": max(0, budget - used_b),
            "percent_used": (used_b / budget) * 100 if budget > 0 else 100.0,
        }

    return result
