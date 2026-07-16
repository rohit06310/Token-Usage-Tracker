"""
Dashboard summary endpoint.
Returns a rich per-provider summary in a single round-trip:
  - provider metadata + confidence_level
  - today's token/cost/call totals
  - 30-day cost totals
  - remaining quota (rpm, tpm, rpd)

Avoids N+1 requests from the frontend.
"""

import logging
from datetime import datetime, timezone, timedelta, date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.deps import AuthenticatedUser
from app.models.provider import Provider
from app.models.usage_log import UsageLog
from app.services.db import get_db
from app.services.usage_limits import calculate_remaining_quota

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", summary="All-provider dashboard summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = None,
):
    """
    Return a single response with per-provider metrics needed by the
    dashboard summary cards. Joins providers with aggregated usage_logs
    to avoid N+1 round-trips from the frontend.
    """
    providers = db.query(Provider).order_by(Provider.name).all()

    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    # Bulk-aggregate today's usage per provider
    today_agg = (
        db.query(
            UsageLog.provider_id,
            func.count(UsageLog.id).label("call_count"),
            func.sum(UsageLog.tokens_in + UsageLog.tokens_out).label("total_tokens"),
            func.sum(UsageLog.cost).label("total_cost"),
        )
        .filter(UsageLog.user_id == current_user.id, UsageLog.created_at >= today_start)
        .group_by(UsageLog.provider_id)
        .all()
    )
    today_map = {str(r.provider_id): r for r in today_agg}

    # Bulk-aggregate 30-day cost per provider
    cost_30d_agg = (
        db.query(
            UsageLog.provider_id,
            func.sum(UsageLog.cost).label("total_cost"),
        )
        .filter(UsageLog.user_id == current_user.id, UsageLog.created_at >= thirty_days_ago)
        .group_by(UsageLog.provider_id)
        .all()
    )
    cost_30d_map = {str(r.provider_id): r for r in cost_30d_agg}

    results = []
    for p in providers:
        pid = str(p.id)
        today = today_map.get(pid)
        cost_30d = cost_30d_map.get(pid)
        quota = calculate_remaining_quota(db, p.id, current_user.id)

        results.append(
            {
                "provider_id": pid,
                "provider_name": p.name,
                "provider_slug": p.slug,
                "confidence_level": p.confidence_level,
                # Today
                "call_count_today": int(today.call_count) if today else 0,
                "total_tokens_today": int(today.total_tokens or 0) if today else 0,
                "total_cost_today": str(today.total_cost or "0") if today else "0",
                # 30-day
                "total_cost_30d": str(cost_30d.total_cost or "0") if cost_30d else "0",
                # Remaining quota (tpm/rpm/rpd)
                "remaining_quota": quota,
            }
        )

    return {"providers": results, "generated_at": now.isoformat()}
