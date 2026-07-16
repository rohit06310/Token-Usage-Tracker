"""
Usage limits API.
Returns active limits and remaining quota for providers.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import AuthenticatedUser
from app.services.db import get_db
from app.models.provider import Provider
from app.services.usage_limits import calculate_remaining_quota

router = APIRouter(
    prefix="/usage",
    tags=["Limits & Usage"],
)

@router.get("/{provider_slug}/remaining")
def get_provider_remaining_quota(
    provider_slug: str,
    db: Session = Depends(get_db),
    _user: AuthenticatedUser = None,
):
    """
    Get rolling window usage (RPM, TPM, RPD) against active rate limits
    for a specific provider.
    """
    provider = db.query(Provider).filter(Provider.slug == provider_slug).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_slug}' not found",
        )

    quotas = calculate_remaining_quota(db, provider.id, _user.id)
    return {
        "provider": provider.slug,
        "limits": quotas
    }


from typing import List
from datetime import date
from pydantic import BaseModel
from app.models.rate_limit import RateLimit
import uuid

class RateLimitCreate(BaseModel):
    tier_name: str
    rpm: int | None = None
    tpm: int | None = None
    rpd: int | None = None
    budget_usd: float | None = None
    effective_date: date

class RateLimitRead(RateLimitCreate):
    id: uuid.UUID
    provider_id: uuid.UUID

@router.get("/{provider_slug}/limits", response_model=List[RateLimitRead])
def list_provider_limits(
    provider_slug: str,
    db: Session = Depends(get_db),
    _user: AuthenticatedUser = None,
):
    provider = db.query(Provider).filter(Provider.slug == provider_slug).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
        
    limits = db.query(RateLimit).filter(RateLimit.provider_id == provider.id).order_by(RateLimit.effective_date.desc()).all()
    return limits

@router.post("/{provider_slug}/limits", response_model=RateLimitRead)
def create_provider_limit(
    provider_slug: str,
    limit_in: RateLimitCreate,
    db: Session = Depends(get_db),
    _user: AuthenticatedUser = None,
):
    provider = db.query(Provider).filter(Provider.slug == provider_slug).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
        
    db_limit = RateLimit(
        provider_id=provider.id,
        tier_name=limit_in.tier_name,
        rpm=limit_in.rpm,
        tpm=limit_in.tpm,
        rpd=limit_in.rpd,
        budget_usd=limit_in.budget_usd,
        effective_date=limit_in.effective_date
    )
    db.add(db_limit)
    db.commit()
    db.refresh(db_limit)
    return db_limit

@router.delete("/limits/{limit_id}", status_code=204)
def delete_provider_limit(
    limit_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: AuthenticatedUser = None,
):
    db_limit = db.query(RateLimit).filter(RateLimit.id == limit_id).first()
    if not db_limit:
        raise HTTPException(status_code=404, detail="Rate limit not found")
        
    db.delete(db_limit)
    db.commit()
    return None
