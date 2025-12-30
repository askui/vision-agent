"""
Module-level APScheduler singleton management.

Similar to how `engine.py` manages the database engine, this module manages
the APScheduler instance as a singleton to ensure jobs persist across requests.
"""

import logging
from datetime import timedelta
from sqlite3 import Connection as SQLite3Connection
from typing import Any

from apscheduler import AsyncScheduler
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from sqlalchemy import create_engine, event

from askui.chat.api.dependencies import get_settings

_logger = logging.getLogger(__name__)

# Module-level settings for scheduler database
_settings = get_settings()
_connect_args = {"check_same_thread": False}
_echo = _logger.isEnabledFor(logging.DEBUG)

# Separate engine for scheduler database
scheduler_engine = create_engine(
    _settings.db.scheduler_url,
    connect_args=_connect_args,
    echo=_echo,
)


# Module-level singleton data store using separate scheduler database
_data_store: Any = SQLAlchemyDataStore(engine_or_url=scheduler_engine)

# Module-level singleton scheduler instance
# - max_concurrent_jobs=1: only one job runs at a time (sequential execution)
# At module level: just create the scheduler (don't start it)
scheduler: AsyncScheduler = AsyncScheduler(
    data_store=_data_store,
    max_concurrent_jobs=1,
    cleanup_interval=timedelta(minutes=1),  # Cleanup every minute
)


@event.listens_for(scheduler_engine, "connect")
def set_sqlite_pragma(dbapi_conn: SQLite3Connection, connection_record: Any) -> None:  # noqa: ARG001
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


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
