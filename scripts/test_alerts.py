"""
Script to manually trigger the alerts job for testing purposes.
"""

import asyncio
import logging
from app.services.alerts import check_thresholds_and_alert
from app.services.db import get_session_factory
from app.core.config import setup_logging

logger = logging.getLogger(__name__)

async def run_alerts():
    setup_logging()
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        logger.info("Running manual alert checks...")
        await check_thresholds_and_alert(db)
        logger.info("Manual alert checks completed successfully.")
    except Exception as e:
        logger.error("Failed to run alert checks: %s", e)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_alerts())
