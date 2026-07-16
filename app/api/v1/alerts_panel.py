"""
Alerts panel endpoint.
Exposes recent alert records from `alerts_sent` for display in the UI.
Derives `severity` from threshold_percent so the frontend can apply
visual distinction without extra logic.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import AuthenticatedUser
from app.models.alert_sent import AlertSent
from app.models.provider import Provider
from app.services.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _derive_severity(threshold_percent) -> str:
    """
    Derive UI severity from the threshold that was crossed.
    >= 95%  → critical  (limit exceeded or near-exceeded)
    >= 80%  → warning   (approaching limit)
    < 80%   → info
    """
    pct = float(threshold_percent)
    if pct >= 95:
        return "critical"
    if pct >= 80:
        return "warning"
    return "info"


@router.get("/recent", summary="Recent alerts for the UI panel")
def get_recent_alerts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user: AuthenticatedUser = None,
):
    """
    Returns recent alerts ordered by sent_at desc.
    Scoped to providers that the current user has usage logs for,
    preventing cross-user data leakage.
    """
    rows = (
        db.query(AlertSent, Provider.name.label("provider_name"), Provider.slug.label("provider_slug"))
        .join(Provider, AlertSent.provider_id == Provider.id)
        .filter(AlertSent.user_id == _user.id)
        .order_by(AlertSent.sent_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    total = (
        db.query(AlertSent)
        .filter(AlertSent.user_id == _user.id)
        .count()
    )

    items = []
    for alert, provider_name, provider_slug in rows:
        items.append(
            {
                "id": str(alert.id),
                "provider_id": str(alert.provider_id),
                "provider_name": provider_name,
                "provider_slug": provider_slug,
                "alert_type": alert.alert_type,
                "threshold_percent": str(alert.threshold_percent),
                "window_start": alert.window_start.isoformat(),
                "sent_at": alert.sent_at.isoformat(),
                "severity": _derive_severity(alert.threshold_percent),
                # Human-readable message synthesized from fields
                "message": (
                    f"{provider_name} {alert.alert_type.upper()} usage reached "
                    f"{float(alert.threshold_percent):.0f}% of limit"
                ),
            }
        )

    return {"items": items, "total": total, "limit": limit, "offset": offset}

