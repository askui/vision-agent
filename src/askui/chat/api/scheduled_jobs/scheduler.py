"""
Module-level APScheduler singleton management.

Similar to how `engine.py` manages the database engine, this module manages
the APScheduler instance as a singleton to ensure jobs persist across requests.

Uses the shared database engine from `engine.py` which is configured with
optimized SQLite pragmas for concurrent access (WAL mode, etc.).
"""

import logging
from datetime import timedelta
from typing import Any

from apscheduler import AsyncScheduler
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore

from askui.chat.api.db.engine import engine

_logger = logging.getLogger(__name__)

# Use shared engine from db/engine.py (already configured with SQLite pragmas)
# APScheduler will create its own tables (apscheduler_*) in the same database
_data_store: Any = SQLAlchemyDataStore(engine_or_url=engine)

# Module-level singleton scheduler instance
# - max_concurrent_jobs=1: only one job runs at a time (sequential execution)
# At module level: just create the scheduler (don't start it)
scheduler: AsyncScheduler = AsyncScheduler(
    data_store=_data_store,
    max_concurrent_jobs=1,
    cleanup_interval=timedelta(minutes=1),  # Cleanup every minute
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
    _logger.info("Scheduler started in background")


async def shutdown_scheduler() -> None:
    """Shut down the scheduler gracefully."""
    await scheduler.__aexit__(None, None, None)
    _logger.info("Scheduler shut down")
