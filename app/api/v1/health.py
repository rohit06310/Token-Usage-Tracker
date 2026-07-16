"""Health check endpoint — no auth required."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health check",
    description="Returns application health status and database connectivity.",
    response_description="Health status object",
)
def health_check(db: Session = Depends(get_db)):
    """
    Public health check endpoint — no authentication required.

    Checks:
    - Application is running
    - Database connection is alive

    Used by Docker healthcheck and load balancers.
    """
    settings = get_settings()
    db_status = "disconnected"
    db_error = None

    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        logger.error("Database health check failed", exc_info=True)
        db_error = str(exc)

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "db": db_status,
        **({"db_error": db_error} if db_error else {}),
    }
