"""Migration runner for Alembic."""

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Run Alembic migrations to upgrade database to head."""
    migrations_dir = Path(__file__).parent
    alembic_cfg = Config(str(migrations_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(migrations_dir))
    logger.info("Running database migrations...")
    try:
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception:
        logger.exception("Failed to run database migrations")
        raise
