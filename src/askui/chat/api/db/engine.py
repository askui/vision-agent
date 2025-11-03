import logging
from sqlite3 import Connection as SQLite3Connection
from typing import Any

from sqlalchemy import Engine, create_engine, event

from askui.chat.api.dependencies import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
connect_args = {"check_same_thread": False}
echo = logger.isEnabledFor(logging.DEBUG)
engine = create_engine(settings.db.url, connect_args=connect_args, echo=echo)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn: SQLite3Connection, connection_record: Any) -> None:  # noqa: ARG001
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
