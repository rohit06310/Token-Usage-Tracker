"""
Provider CRUD endpoints.
All routes require dashboard API-key authentication.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import AuthenticatedUser
from app.models.provider import Provider
from app.schemas.provider import ProviderCreate, ProviderRead, ProviderUpdate
from app.services.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.get("/", response_model=list[ProviderRead], summary="List all providers")
def list_providers(
    db: Session = Depends(get_db),
    _user: AuthenticatedUser = None,
):
    """Return all registered LLM providers."""
    return db.query(Provider).order_by(Provider.name).all()


@router.post(
    "/",
    response_model=ProviderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new provider",
)
def create_provider(
    payload: ProviderCreate,
    db: Session = Depends(get_db),
    _user: AuthenticatedUser = None,
):
    """Register a new LLM provider."""
    existing = db.query(Provider).filter(Provider.slug == payload.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A provider with slug '{payload.slug}' already exists.",
        )

    provider = Provider(**payload.model_dump())
    db.add(provider)
    db.commit()
    db.refresh(provider)
    logger.info("Provider created", extra={"provider_id": str(provider.id), "slug": provider.slug})
    return provider


@router.get("/{provider_id}", response_model=ProviderRead, summary="Get a provider by ID")
def get_provider(
    provider_id: UUID,
    db: Session = Depends(get_db),
    _user: AuthenticatedUser = None,
):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found.")
    return provider


@router.patch("/{provider_id}", response_model=ProviderRead, summary="Update a provider")
def update_provider(
    provider_id: UUID,
    payload: ProviderUpdate,
    db: Session = Depends(get_db),
    _user: AuthenticatedUser = None,
):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(provider, key, value)

    db.commit()
    db.refresh(provider)
    return provider


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a provider")
def delete_provider(
    provider_id: UUID,
    db: Session = Depends(get_db),
    _user: AuthenticatedUser = None,
):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found.")
    db.delete(provider)
    db.commit()
