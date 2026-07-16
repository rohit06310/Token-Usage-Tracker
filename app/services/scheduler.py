"""
Background scheduler — fetches provider-reported usage periodically.

Uses APScheduler (AsyncIOScheduler) so it runs inside the FastAPI process
with no additional broker (no Redis, no Celery) required.

Jobs:
  - fetch_openai_reported_usage  — calls OpenAI usage API
  - fetch_anthropic_reported_usage — calls Anthropic usage API
  (Groq and Gemini don't have public billing APIs as of 2025-07)

The scheduler is started in app/main.py's lifespan hook.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

from app.core.config import get_settings
from app.services.job_tracker import track_job

logger = logging.getLogger(__name__)

# Module-level scheduler instance (lazy-initialised)
_scheduler = None


def get_scheduler():
    """Return the global AsyncIOScheduler, creating it if needed."""
    global _scheduler
    if _scheduler is None:
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
        except ImportError:
            raise RuntimeError(
                "apscheduler is required. Install with: pip install apscheduler"
            )
        _scheduler = AsyncIOScheduler(timezone="UTC")
    return _scheduler


# ---------------------------------------------------------------------------
# Job: Fetch OpenAI reported usage
# ---------------------------------------------------------------------------

@track_job("fetch_openai_reported_usage")
async def job_fetch_openai_reported_usage() -> None:
    """
    Fetch OpenAI usage data from the OpenAI usage API and store it.

    OpenAI's usage endpoint:
        GET https://api.openai.com/v1/usage?date=YYYY-MM-DD
    Returns usage broken down by day and model.

    Note: As of 2025, OpenAI's usage API requires an admin API key
    (organization-level, not project-level).
    """
    settings = get_settings()

    if not settings.openai_api_key:
        logger.debug("OPENAI_API_KEY not set — skipping reported usage fetch")
        return

    try:
        from openai import AsyncOpenAI
        import httpx
    except ImportError:
        logger.error("openai package required for usage fetch")
        return

    # We fetch the last N days of usage
    lookback = settings.usage_initial_lookback_days
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=lookback)

    logger.info(
        "Fetching OpenAI reported usage: %s → %s",
        start_date,
        end_date,
    )

    try:
        # OpenAI usage API (uses admin key, different from chat API)
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch day by day (OpenAI usage API is per-day)
            current_date = start_date
            while current_date <= end_date:
                resp = await _fetch_openai_usage_with_retry(client, headers, current_date)
                if resp.status_code == 200:
                    data = resp.json()
                    await _store_openai_usage(data, current_date)
                else:
                    logger.warning(
                        "OpenAI usage API returned %d for date %s",
                        resp.status_code,
                        current_date,
                    )
                current_date += timedelta(days=1)

    except Exception as exc:
        logger.error("Error fetching OpenAI reported usage: %s", exc, exc_info=True)
        raise  # Re-raise so track_job captures the failure


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    reraise=True
)
async def _fetch_openai_usage_with_retry(client: httpx.AsyncClient, headers: dict, date) -> httpx.Response:
    resp = await client.get(
        "https://api.openai.com/v1/usage",
        headers=headers,
        params={"date": date.isoformat()},
    )
    if resp.status_code >= 500:
        resp.raise_for_status()  # Trigger retry on 5xx errors
    return resp


async def _store_openai_usage(data: dict, date) -> None:
    """Store OpenAI usage data in provider_reported_usage table."""
    from datetime import datetime, timezone
    from decimal import Decimal

    from app.models.provider import Provider
    from app.models.provider_reported_usage import ProviderReportedUsage
    from app.services.db import get_session_factory

    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        # Find the OpenAI provider
        provider = db.query(Provider).filter(Provider.slug == "openai").first()
        if not provider:
            logger.warning("OpenAI provider not found in DB — run seed_providers.py first")
            return

        period_start = datetime(date.year, date.month, date.day, tzinfo=timezone.utc)
        period_end = period_start + timedelta(days=1) - timedelta(seconds=1)

        # Check if we already have this record
        existing = (
            db.query(ProviderReportedUsage)
            .filter(
                ProviderReportedUsage.provider_id == provider.id,
                ProviderReportedUsage.period_start == period_start,
            )
            .first()
        )
        if existing:
            logger.debug("OpenAI usage already recorded for %s — skipping", date)
            return

        # Aggregate totals from the data
        total_tokens = sum(
            item.get("n_context_tokens_total", 0) + item.get("n_generated_tokens_total", 0)
            for item in data.get("data", [])
        )

        record = ProviderReportedUsage(
            provider_id=provider.id,
            period_start=period_start,
            period_end=period_end,
            total_tokens=total_tokens,
            total_cost=None,  # OpenAI usage API doesn't return cost directly
            fetched_at=datetime.now(timezone.utc),
            source="openai_usage_api",
        )
        db.add(record)
        db.commit()
        logger.info("Stored OpenAI reported usage for %s: %d tokens", date, total_tokens)

    except Exception as exc:
        db.rollback()
        logger.error("Failed to store OpenAI usage for %s: %s", date, exc, exc_info=True)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Job: Fetch Anthropic reported usage
# ---------------------------------------------------------------------------

@track_job("fetch_anthropic_reported_usage")
async def job_fetch_anthropic_reported_usage() -> None:
    """
    Fetch Anthropic usage data from the Anthropic usage API.

    Anthropic usage endpoint:
        GET https://api.anthropic.com/v1/usage
    Returns usage for the current billing period.

    Note: Anthropic's usage API is part of their admin console API.
    """
    settings = get_settings()

    if not settings.anthropic_api_key:
        logger.debug("ANTHROPIC_API_KEY not set — skipping reported usage fetch")
        return

    logger.info("Fetching Anthropic reported usage")

    try:
        import httpx
    except ImportError:
        logger.error("httpx required for Anthropic usage fetch")
        return

    try:
        headers = {
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await _fetch_anthropic_usage_with_retry(client, headers)

        if resp.status_code == 200:
            data = resp.json()
            await _store_anthropic_usage(data)
        elif resp.status_code == 404:
            logger.info(
                "Anthropic usage API returned 404 — endpoint may not be available on your plan"
            )
        else:
            logger.warning(
                "Anthropic usage API returned %d: %s",
                resp.status_code,
                resp.text[:200],
            )

    except Exception as exc:
        logger.error("Error fetching Anthropic reported usage: %s", exc, exc_info=True)
        raise


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    reraise=True
)
async def _fetch_anthropic_usage_with_retry(client: httpx.AsyncClient, headers: dict) -> httpx.Response:
    resp = await client.get(
        "https://api.anthropic.com/v1/usage",
        headers=headers,
    )
    if resp.status_code >= 500:
        resp.raise_for_status()
    return resp


async def _store_anthropic_usage(data: dict) -> None:
    """Store Anthropic usage data in provider_reported_usage table."""
    from datetime import datetime, timezone
    from decimal import Decimal

    from app.models.provider import Provider
    from app.models.provider_reported_usage import ProviderReportedUsage
    from app.services.db import get_session_factory

    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        provider = db.query(Provider).filter(Provider.slug == "anthropic").first()
        if not provider:
            logger.warning("Anthropic provider not found in DB — run seed_providers.py first")
            return

        now = datetime.now(timezone.utc)
        # Use billing period dates from response if available
        period_start_str = data.get("billing_period_start") or data.get("period_start")
        period_end_str = data.get("billing_period_end") or data.get("period_end")

        period_start = (
            datetime.fromisoformat(period_start_str.replace("Z", "+00:00"))
            if period_start_str
            else now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        )
        period_end = (
            datetime.fromisoformat(period_end_str.replace("Z", "+00:00"))
            if period_end_str
            else now
        )

        total_tokens = data.get("total_tokens", None)
        total_cost_str = data.get("total_cost") or data.get("amount_due")
        total_cost = Decimal(str(total_cost_str)) if total_cost_str is not None else None

        # Avoid duplicate records
        existing = (
            db.query(ProviderReportedUsage)
            .filter(
                ProviderReportedUsage.provider_id == provider.id,
                ProviderReportedUsage.period_start == period_start,
            )
            .first()
        )
        if existing:
            # Update with latest data
            existing.total_tokens = total_tokens
            existing.total_cost = total_cost
            existing.fetched_at = now
            db.commit()
            logger.info("Updated Anthropic reported usage for period %s", period_start.date())
        else:
            record = ProviderReportedUsage(
                provider_id=provider.id,
                period_start=period_start,
                period_end=period_end,
                total_tokens=total_tokens,
                total_cost=total_cost,
                fetched_at=now,
                source="anthropic_usage_api",
            )
            db.add(record)
            db.commit()
            logger.info("Stored Anthropic reported usage for period %s", period_start.date())

    except Exception as exc:
        db.rollback()
        logger.error("Failed to store Anthropic usage: %s", exc, exc_info=True)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Job: Fetch Groq reported usage (Stub)
# ---------------------------------------------------------------------------

@track_job("fetch_groq_reported_usage")
async def job_fetch_groq_reported_usage() -> None:
    """
    Fetch Groq usage data from the Groq API.
    (Stub implementation)
    """
    logger.info("Fetching Groq reported usage (stub)")
    # Not yet implemented by provider

# ---------------------------------------------------------------------------
# Job: Fetch Gemini reported usage (Stub)
# ---------------------------------------------------------------------------

@track_job("fetch_gemini_reported_usage")
async def job_fetch_gemini_reported_usage() -> None:
    """
    Fetch Gemini usage data from the Google API.
    (Stub implementation)
    """
    logger.info("Fetching Gemini reported usage (stub)")
    # Not yet implemented by provider


# ---------------------------------------------------------------------------
# Job: Reconcile Usage
# ---------------------------------------------------------------------------

@track_job("reconcile_usage")
async def job_reconcile_usage() -> None:
    """
    Run the reconciliation service to compare our logs vs reported usage.
    """
    from app.services.reconciliation import reconcile_provider_usage
    from app.services.db import get_session_factory
    
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        logger.info("Starting usage reconciliation...")
        reconcile_provider_usage(db)
        logger.info("Usage reconciliation completed.")
    except Exception as exc:
        logger.error("Error during reconciliation: %s", exc, exc_info=True)
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Job: Check Alerts
# ---------------------------------------------------------------------------

@track_job("check_alerts")
async def job_check_alerts() -> None:
    """
    Check current usage against configured thresholds and dispatch alerts.
    """
    from app.services.alerts import check_thresholds_and_alert
    from app.services.db import get_session_factory
    
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        await check_thresholds_and_alert(db)
    except Exception as exc:
        logger.error("Error checking alerts: %s", exc, exc_info=True)
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Scheduler lifecycle
# ---------------------------------------------------------------------------

def start_scheduler() -> None:
    """
    Start the APScheduler AsyncIOScheduler with all configured jobs.
    Called from the FastAPI lifespan hook.
    """
    settings = get_settings()

    if not settings.scheduler_enabled:
        logger.info("Scheduler is disabled (SCHEDULER_ENABLED=false)")
        return

    scheduler = get_scheduler()

    interval_hours = settings.usage_fetch_interval_hours

    # Register jobs
    scheduler.add_job(
        job_fetch_openai_reported_usage,
        trigger="interval",
        hours=interval_hours,
        id="fetch_openai_usage",
        name="Fetch OpenAI reported usage",
        replace_existing=True,
        misfire_grace_time=300,  # 5 min grace for missed triggers
    )

    scheduler.add_job(
        job_fetch_anthropic_reported_usage,
        trigger="interval",
        hours=interval_hours,
        id="fetch_anthropic_usage",
        name="Fetch Anthropic reported usage",
        replace_existing=True,
        misfire_grace_time=300,
    )

    scheduler.add_job(
        job_fetch_groq_reported_usage,
        trigger="interval",
        hours=interval_hours,
        id="fetch_groq_usage",
        name="Fetch Groq reported usage",
        replace_existing=True,
        misfire_grace_time=300,
    )

    scheduler.add_job(
        job_fetch_gemini_reported_usage,
        trigger="interval",
        hours=interval_hours,
        id="fetch_gemini_usage",
        name="Fetch Gemini reported usage",
        replace_existing=True,
        misfire_grace_time=300,
    )

    scheduler.add_job(
        job_reconcile_usage,
        trigger="interval",
        hours=interval_hours,  # Run at the same interval
        id="reconcile_usage",
        name="Reconcile Usage",
        replace_existing=True,
        misfire_grace_time=300,
    )

    scheduler.add_job(
        job_check_alerts,
        trigger="interval",
        minutes=5,  # Check alerts every 5 minutes
        id="check_alerts",
        name="Check Alerts",
        replace_existing=True,
        misfire_grace_time=60,
    )

    scheduler.start()
    logger.info(
        "Scheduler started — %d jobs registered, interval=%dh",
        len(scheduler.get_jobs()),
        interval_hours,
    )


def stop_scheduler() -> None:
    """
    Stop the scheduler gracefully.
    Called from the FastAPI lifespan hook on shutdown.
    """
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
