"""
Unified AI Usage Dashboard — FastAPI Application Factory.

Startup sequence:
  1. Load settings (validates all required env vars)
  2. Create FastAPI app with metadata
  3. Register middleware (CORS)
  4. Mount API v1 router
  5. Start APScheduler (if enabled)
  6. Register startup/shutdown lifecycle events
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.v1.router import router as v1_router
from app.core.config import get_settings

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle hooks."""
    settings = get_settings()
    logger.info(
        "Starting %s v%s in [%s] mode",
        settings.app_name,
        settings.app_version,
        settings.app_env,
    )

    # Start the background scheduler
    if settings.scheduler_enabled:
        try:
            from app.services.scheduler import start_scheduler
            start_scheduler()
        except Exception as exc:
            logger.error("Failed to start scheduler: %s", exc, exc_info=True)

    yield

    # Graceful shutdown
    try:
        from app.services.scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass

    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "A unified dashboard for tracking LLM token usage and costs "
            "across OpenAI, Anthropic, Groq, and Gemini."
        ),
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.include_router(v1_router, prefix="/api/v1")

    # Also mount health at root for Docker healthcheck
    from app.api.v1.health import router as health_router
    app.include_router(health_router)

    return app


app = create_app()
