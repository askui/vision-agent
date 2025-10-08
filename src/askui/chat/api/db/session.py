"""Session management for chat API database."""

import logging
from contextlib import contextmanager
from typing import Callable, Generator

from askui.chat.api.settings import Settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)


def get_session_factory(
    settings: Settings,
) -> Callable[[], Generator[Session, None, None]]:
    """Get SQLAlchemy session factory.

    Args:
        settings (Settings): Application settings containing database URL.

    Returns:
        Callable[[], Generator[Session, None, None]]: Session factory that returns a context manager.
    """
    # Enable SQL logging if debug level is set
    echo = logger.isEnabledFor(logging.DEBUG)
    engine = create_engine(settings.db.url, echo=echo)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    @contextmanager
    def session_factory() -> Generator[Session, None, None]:
        session = SessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return session_factory
