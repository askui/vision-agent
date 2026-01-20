import logging
from sqlite3 import Connection as SQLite3Connection
from typing import Any

from sqlalchemy import create_engine, event

from askui.chat.api.dependencies import get_settings

_logger = logging.getLogger(__name__)

_settings = get_settings()
_connect_args = {"check_same_thread": False}
_echo = _logger.isEnabledFor(logging.DEBUG)

# Create engine with optimized settings
engine = create_engine(
    _settings.db.url,
    connect_args=_connect_args,
    echo=_echo,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn: SQLite3Connection, connection_record: Any) -> None:  # noqa: ARG001
    """
    Configure SQLite pragmas for optimal web application performance.

    Applied on each new connection:
    - foreign_keys=ON: Enable foreign key constraint enforcement
    - journal_mode=WAL: Write-Ahead Logging for better concurrency (readers don't block writers)
    - synchronous=NORMAL: Sync every 1000 pages instead of every write (faster, still durable with WAL)
    - busy_timeout=30000: Wait up to 30 seconds for locks instead of failing immediately
    """
    cursor = dbapi_conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.execute("PRAGMA busy_timeout = 30000")

    cursor.close()
