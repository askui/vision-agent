"""
Module-level APScheduler singleton management.

Similar to how `engine.py` manages the database engine, this module manages
the APScheduler instance as a singleton to ensure jobs persist across requests.
"""

import logging
from typing import Any

from apscheduler import AsyncScheduler
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore

from askui.chat.api.db.engine import engine

logger = logging.getLogger(__name__)

# Module-level singleton data store (similar to engine pattern)
_data_store: Any = SQLAlchemyDataStore(engine_or_url=engine)

# Module-level singleton scheduler instance
# - max_concurrent_jobs=1: only one job runs at a time (sequential execution)
# At module level: just create the scheduler (don't start it)
scheduler: AsyncScheduler = AsyncScheduler(
    data_store=_data_store,
    max_concurrent_jobs=1,
)


async def start_scheduler() -> None:
    """
    Start the scheduler to begin processing jobs.

    This initializes the scheduler and starts it in the background so it can
    poll for and execute scheduled jobs while the FastAPI application handles requests.
    """
    # First initialize the scheduler via context manager entry
    await scheduler.__aenter__()
    # Then start background processing of jobs
    await scheduler.start_in_background()
    logger.info("Scheduler started in background")


async def shutdown_scheduler() -> None:
    """Shut down the scheduler gracefully."""
    await scheduler.__aexit__(None, None, None)
    logger.info("Scheduler shut down")
