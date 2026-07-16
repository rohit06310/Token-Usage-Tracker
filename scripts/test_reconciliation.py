"""
Script to manually trigger the reconciliation job for testing purposes.
"""

import asyncio
import logging
from app.services.reconciliation import reconcile_provider_usage
from app.services.db import get_session_factory
from app.core.config import setup_logging

logger = logging.getLogger(__name__)

async def run_reconciliation():
    setup_logging()
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        logger.info("Running manual reconciliation...")
        reconcile_provider_usage(db)
        logger.info("Manual reconciliation completed successfully.")
    except Exception as e:
        logger.error("Failed to run reconciliation: %s", e)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_reconciliation())
