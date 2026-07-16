"""
Usage log endpoints — query and aggregate usage data.
All routes require dashboard authentication.
"""

import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import AuthenticatedUser
from app.models.usage_log import UsageLog
from app.schemas.usage_log import UsageLogRead, UsageLogPaginated
from app.services.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/usage", tags=["Usage"])

@router.get("/", response_model=UsageLogPaginated, summary="List usage logs")
def list_usage_logs(
    provider_id: UUID | None = Query(None, description="Filter by provider"),
    model: str | None = Query(None, description="Filter by model name"),
    project_tag: str | None = Query(None, description="Filter by project tag"),
    date_from: date | None = Query(None, description="Filter from date (inclusive)"),
    date_to: date | None = Query(None, description="Filter to date (inclusive)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = None,
):
    """
    List usage log entries with optional filtering.
    Returns paginated items and the total count matching the filters.
    Results are ordered by newest first.
    """
    query = db.query(UsageLog).filter(UsageLog.user_id == current_user.id)

    if provider_id:
        query = query.filter(UsageLog.provider_id == provider_id)
    if model:
        query = query.filter(UsageLog.model == model)
    if project_tag:
        query = query.filter(UsageLog.project_tag == project_tag)
    if date_from:
        query = query.filter(func.date(UsageLog.created_at) >= date_from)
    if date_to:
        query = query.filter(func.date(UsageLog.created_at) <= date_to)

    total = query.count()
    items = query.order_by(UsageLog.created_at.desc()).offset(offset).limit(limit).all()
    
    return {"items": items, "total": total}


@router.get("/summary", summary="Aggregate usage summary")
def usage_summary(
    provider_id: UUID | None = Query(None),
    project_tag: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = None,
):
    """
    Return aggregated totals: call count, total tokens, total cost.
    Phase 2 will add per-model and per-project breakdowns.
    """
    query = db.query(
        func.count(UsageLog.id).label("total_calls"),
        func.sum(UsageLog.tokens_in).label("total_tokens_in"),
        func.sum(UsageLog.tokens_out).label("total_tokens_out"),
        func.sum(UsageLog.cost).label("total_cost"),
    ).filter(UsageLog.user_id == current_user.id)

    if provider_id:
        query = query.filter(UsageLog.provider_id == provider_id)
    if project_tag:
        query = query.filter(UsageLog.project_tag == project_tag)
    if date_from:
        query = query.filter(func.date(UsageLog.created_at) >= date_from)
    if date_to:
        query = query.filter(func.date(UsageLog.created_at) <= date_to)

    result = query.one()

    return {
        "total_calls": result.total_calls or 0,
        "total_tokens_in": int(result.total_tokens_in or 0),
        "total_tokens_out": int(result.total_tokens_out or 0),
        "total_tokens": int((result.total_tokens_in or 0) + (result.total_tokens_out or 0)),
        "total_cost": str(result.total_cost or "0"),
    }


@router.get("/history", summary="Time-series usage aggregation for charts")
def usage_history(
    range: str = Query("7d", description="Preset range: today | 7d | 30d"),
    group_by: str = Query("day", description="Grouping: hour | day"),
    provider_id: UUID | None = Query(None, description="Filter by provider UUID"),
    provider_slug: str | None = Query(None, description="Filter by provider slug"),
    project_tag: str | None = Query(None),
    model: str | None = Query(None),
    date_from: date | None = Query(None, description="Override range start (ISO date)"),
    date_to: date | None = Query(None, description="Override range end (ISO date)"),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = None,
):
    """
    Returns time-series data grouped by hour or day.
    Used by the Usage-Over-Time chart. Supports preset ranges and custom
    date_from/date_to overrides. When provider_id is omitted, returns
    combined totals with a per-provider breakdown.
    """
    from datetime import datetime, timezone, timedelta
    from app.models.provider import Provider

    now = datetime.now(timezone.utc)

    # Resolve date range
    if date_from and date_to:
        start_dt = datetime(date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc)
        end_dt = datetime(date_to.year, date_to.month, date_to.day, 23, 59, 59, tzinfo=timezone.utc)
    elif range == "today":
        start_dt = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        end_dt = now
    elif range == "30d":
        start_dt = now - timedelta(days=30)
        end_dt = now
    else:  # 7d default
        start_dt = now - timedelta(days=7)
        end_dt = now

    # Resolve group_by truncation
    trunc_unit = "hour" if group_by == "hour" else "day"

    # Resolve provider filter
    pid_filter = provider_id
    if provider_slug and not pid_filter:
        p = db.query(Provider).filter(Provider.slug == provider_slug).first()
        if p:
            pid_filter = p.id

    # Build query — group by truncated timestamp + provider
    q = db.query(
        func.date_trunc(trunc_unit, UsageLog.created_at).label("period"),
        UsageLog.provider_id,
        func.count(UsageLog.id).label("call_count"),
        func.sum(UsageLog.tokens_in).label("tokens_in"),
        func.sum(UsageLog.tokens_out).label("tokens_out"),
        func.sum(UsageLog.tokens_in + UsageLog.tokens_out).label("total_tokens"),
        func.sum(UsageLog.cost).label("total_cost"),
    ).filter(
        UsageLog.user_id == current_user.id,
        UsageLog.created_at >= start_dt,
        UsageLog.created_at <= end_dt,
    )

    if pid_filter:
        q = q.filter(UsageLog.provider_id == pid_filter)
    if project_tag:
        q = q.filter(UsageLog.project_tag == project_tag)
    if model:
        q = q.filter(UsageLog.model == model)

    rows = q.group_by(
        func.date_trunc(trunc_unit, UsageLog.created_at),
        UsageLog.provider_id,
    ).order_by(func.date_trunc(trunc_unit, UsageLog.created_at).asc()).all()

    # Build provider name lookup
    all_providers = {str(p.id): p for p in db.query(Provider).all()}

    data = []
    for row in rows:
        prov = all_providers.get(str(row.provider_id))
        data.append({
            "period": row.period.isoformat() if row.period else None,
            "provider_id": str(row.provider_id),
            "provider_slug": prov.slug if prov else "unknown",
            "provider_name": prov.name if prov else "Unknown",
            "call_count": int(row.call_count),
            "tokens_in": int(row.tokens_in or 0),
            "tokens_out": int(row.tokens_out or 0),
            "total_tokens": int(row.total_tokens or 0),
            "total_cost": str(row.total_cost or "0"),
        })

    return {
        "data": data,
        "range": range,
        "group_by": group_by,
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
    }


@router.get("/cost-breakdown", summary="Cost aggregation by provider and model")
def cost_breakdown(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    project_tag: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = None,
):
    """
    Returns cost aggregation at two granularities:
    - by_provider: cost per provider (for the pie chart)
    - by_model:    cost per model within each provider (for the table)
    """
    from app.models.provider import Provider

    base_filter = [UsageLog.user_id == current_user.id]
    if date_from:
        base_filter.append(func.date(UsageLog.created_at) >= date_from)
    if date_to:
        base_filter.append(func.date(UsageLog.created_at) <= date_to)
    if project_tag:
        base_filter.append(UsageLog.project_tag == project_tag)

    # By provider
    by_provider_rows = (
        db.query(
            UsageLog.provider_id,
            func.count(UsageLog.id).label("call_count"),
            func.sum(UsageLog.cost).label("total_cost"),
            func.sum(UsageLog.tokens_in + UsageLog.tokens_out).label("total_tokens"),
        )
        .filter(*base_filter)
        .group_by(UsageLog.provider_id)
        .all()
    )

    # By model
    by_model_rows = (
        db.query(
            UsageLog.provider_id,
            UsageLog.model,
            func.count(UsageLog.id).label("call_count"),
            func.sum(UsageLog.tokens_in).label("tokens_in"),
            func.sum(UsageLog.tokens_out).label("tokens_out"),
            func.sum(UsageLog.cost).label("total_cost"),
        )
        .filter(*base_filter)
        .group_by(UsageLog.provider_id, UsageLog.model)
        .order_by(func.sum(UsageLog.cost).desc())
        .all()
    )

    all_providers = {str(p.id): p for p in db.query(Provider).all()}

    by_provider = []
    for row in by_provider_rows:
        prov = all_providers.get(str(row.provider_id))
        by_provider.append({
            "provider_id": str(row.provider_id),
            "provider_name": prov.name if prov else "Unknown",
            "provider_slug": prov.slug if prov else "unknown",
            "call_count": int(row.call_count),
            "total_cost": str(row.total_cost or "0"),
            "total_tokens": int(row.total_tokens or 0),
        })

    by_model = []
    for row in by_model_rows:
        prov = all_providers.get(str(row.provider_id))
        by_model.append({
            "provider_id": str(row.provider_id),
            "provider_name": prov.name if prov else "Unknown",
            "provider_slug": prov.slug if prov else "unknown",
            "model": row.model,
            "call_count": int(row.call_count),
            "tokens_in": int(row.tokens_in or 0),
            "tokens_out": int(row.tokens_out or 0),
            "total_cost": str(row.total_cost or "0"),
        })

    return {"by_provider": by_provider, "by_model": by_model}


@router.get("/tags", summary="Available project tags for filter dropdown")
def list_tags(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = None,
):
    """
    Returns distinct project_tag values with usage count.
    Used to populate the project_tag filter dropdown.
    """
    rows = (
        db.query(
            UsageLog.project_tag,
            func.count(UsageLog.id).label("call_count"),
        )
        .filter(UsageLog.user_id == current_user.id, UsageLog.project_tag.isnot(None))
        .group_by(UsageLog.project_tag)
        .order_by(func.count(UsageLog.id).desc())
        .all()
    )

    return [{"tag": row.project_tag, "call_count": int(row.call_count)} for row in rows]


@router.get("/models", summary="Available models for filter dropdown")
def list_models(
    provider_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = None,
):
    """
    Returns distinct model names with provider and usage count.
    Optionally filtered by provider_id.
    """
    from app.models.provider import Provider

    q = db.query(
        UsageLog.model,
        UsageLog.provider_id,
        func.count(UsageLog.id).label("call_count"),
    ).filter(UsageLog.user_id == current_user.id)

    if provider_id:
        q = q.filter(UsageLog.provider_id == provider_id)

    rows = (
        q.group_by(UsageLog.model, UsageLog.provider_id)
        .order_by(func.count(UsageLog.id).desc())
        .all()
    )

    all_providers = {str(p.id): p for p in db.query(Provider).all()}

    return [
        {
            "model": row.model,
            "provider_id": str(row.provider_id),
            "provider_slug": all_providers[str(row.provider_id)].slug
            if str(row.provider_id) in all_providers else "unknown",
            "call_count": int(row.call_count),
        }
        for row in rows
    ]
