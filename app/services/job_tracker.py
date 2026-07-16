"""
Job Tracker decorator.
Automatically wraps scheduler jobs, logs their execution to `job_runs`,
and handles unexpected exceptions so the scheduler doesn't crash.
"""

import functools
import logging
import traceback
from datetime import datetime, timezone
from typing import Any, Callable

from app.services.db import get_session_factory
from app.models.job_run import JobRun

logger = logging.getLogger(__name__)


def track_job(job_name: str) -> Callable:
    """
    Decorator for APScheduler jobs to track their run status in DB.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            SessionLocal = get_session_factory()
            db = SessionLocal()
            
            job_run = JobRun(
                job_name=job_name,
                status="running",
                started_at=datetime.now(timezone.utc),
            )
            try:
                db.add(job_run)
                db.commit()
            except Exception as e:
                logger.error("Failed to create JobRun record: %s", e)
                db.close()
                # Continue executing the job even if logging fails
                return await func(*args, **kwargs)

            try:
                # Execute the actual scheduled job
                result = await func(*args, **kwargs)
                
                job_run.status = "success"
                job_run.finished_at = datetime.now(timezone.utc)
                db.commit()
                return result
                
            except Exception as e:
                logger.error("Job %s failed: %s", job_name, e, exc_info=True)
                job_run.status = "failed"
                job_run.error_message = traceback.format_exc()
                job_run.finished_at = datetime.now(timezone.utc)
                try:
                    db.commit()
                except Exception:
                    logger.error("Failed to update JobRun record on failure")
            finally:
                db.close()
                
        return wrapper
    return decorator
