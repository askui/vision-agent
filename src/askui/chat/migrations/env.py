"""Alembic environment configuration."""

import logging

from alembic import context

# We need to import the orms to ensure they are registered
import askui.chat.api.assistants.orms
import askui.chat.api.files.orms
import askui.chat.api.mcp_configs.orms
import askui.chat.api.messages.orms
import askui.chat.api.runs.orms
import askui.chat.api.threads.orms
from askui.chat.api.db.orm.base import Base
from askui.chat.api.dependencies import get_settings
from askui.chat.api.telemetry.logs import setup_logging

config = context.config
settings = get_settings()
setup_logging(settings.telemetry.log)
sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
alembic_logger = logging.getLogger("alembic")
sqlalchemy_logger.setLevel(settings.telemetry.log.level)
alembic_logger.setLevel(settings.telemetry.log.level)
target_metadata = Base.metadata


def get_url() -> str:
    """Get database URL from settings."""
    return settings.db.url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    from askui.chat.api.db.engine import engine

    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
