"""
SQLAlchemy engine, session factory, and FastAPI DB dependency.
All database interaction goes through these primitives.

Design notes:
- Engine is created lazily (on first call to get_db or get_engine) so that
  tests can override DATABASE_URL via environment before any DB interaction.
- SQLite-safe: pool_size and pool_timeout args are only passed for non-SQLite
  dialects (SQLite uses StaticPool in tests via conftest override).
"""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_engine = None
_SessionLocal = None


def get_engine():
    """Return the SQLAlchemy engine, creating it on first call."""
    global _engine
    if _engine is None:
        settings = get_settings()
        url = settings.database_url
        is_sqlite = url.startswith("sqlite")

        engine_kwargs = {
            "echo": settings.debug,
        }

        if not is_sqlite:
            # PostgreSQL / Supabase-specific pool tuning
            engine_kwargs.update(
                {
                    "pool_size": settings.db_pool_size,
                    "max_overflow": settings.db_max_overflow,
                    "pool_timeout": settings.db_pool_timeout,
                    "pool_recycle": settings.db_pool_recycle,
                    "pool_pre_ping": True,
                }
            )
        else:
            # SQLite (used in tests) — StaticPool for thread safety
            from sqlalchemy.pool import StaticPool
            engine_kwargs["connect_args"] = {"check_same_thread": False}
            engine_kwargs["poolclass"] = StaticPool

        _engine = create_engine(url, **engine_kwargs)
    return _engine


def get_session_factory():
    """Return the sessionmaker factory, creating it on first call."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a SQLAlchemy session and ensures
    it is closed after the request, even on exceptions.

    Usage:
        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
