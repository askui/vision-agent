"""Database engine configuration for chat API."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def create_database_engine(db_path: Path) -> Engine:
    """Create SQLAlchemy engine for SQLite database.

    Args:
        db_path (Path): Path to SQLite database file.

    Returns:
        Engine: Configured SQLAlchemy engine.
    """
    return create_engine(f"sqlite:///{db_path}")
