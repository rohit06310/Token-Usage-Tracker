from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.deps import AuthenticatedUser
from app.models.reconciliation_result import ReconciliationResult
from app.services.db import get_db

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])

@router.get("/", summary="List reconciliation results")
def list_reconciliation_results(
    provider_id: UUID | None = Query(None, description="Filter by provider"),
    date_from: date | None = Query(None, description="Filter from date (inclusive)"),
    date_to: date | None = Query(None, description="Filter to date (inclusive)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = None,
):
    query = db.query(ReconciliationResult)

    if provider_id:
        query = query.filter(ReconciliationResult.provider_id == provider_id)
    if date_from:
        query = query.filter(func.date(ReconciliationResult.period_start) >= date_from)
    if date_to:
        query = query.filter(func.date(ReconciliationResult.period_start) <= date_to)

    total = query.count()
    items = query.order_by(ReconciliationResult.period_start.desc()).offset(offset).limit(limit).all()

    # Join with provider to get slug/name
    from app.models.provider import Provider
    providers = {p.id: p for p in db.query(Provider).all()}

    results = []
    for item in items:
        p = providers.get(item.provider_id)
        results.append({
            "id": str(item.id),
            "provider_id": str(item.provider_id),
            "provider_name": p.name if p else "Unknown",
            "provider_slug": p.slug if p else "unknown",
            "confidence_level": p.confidence_level if p else "unknown",
            "period_start": item.period_start.isoformat(),
            "period_end": item.period_end.isoformat(),
            "self_logged_tokens": item.self_logged_tokens,
            "provider_reported_tokens": item.provider_reported_tokens,
            "difference": item.difference,
            "percent_diff": str(item.percent_diff),
            "status": item.status,
            "checked_at": item.checked_at.isoformat(),
        })

    return {"items": results, "total": total}
