"""v1 API router — assembles all sub-routers."""

from fastapi import APIRouter, Depends

from app.api.v1 import (
    alerts_panel,
    api_keys,
    auth,
    completions,
    dashboard,
    health,
    limits,
    providers,
    usage,
    reconciliation,
)
from app.core.deps import get_current_user

router = APIRouter()

# Public routes (no auth)
router.include_router(health.router)
router.include_router(auth.router, prefix="/auth", tags=["Auth"])

# Protected routes (require dashboard auth)
router.include_router(providers.router, dependencies=[Depends(get_current_user)])
router.include_router(api_keys.router, dependencies=[Depends(get_current_user)])
router.include_router(usage.router, dependencies=[Depends(get_current_user)])
router.include_router(dashboard.router, dependencies=[Depends(get_current_user)])
router.include_router(alerts_panel.router, dependencies=[Depends(get_current_user)])
router.include_router(limits.router, dependencies=[Depends(get_current_user)])
router.include_router(completions.router, dependencies=[Depends(get_current_user)])
router.include_router(reconciliation.router, dependencies=[Depends(get_current_user)])
