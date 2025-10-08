"""Initial schema migration."""

from askui.chat.migrations import register_migration


@register_migration(1)
def upgrade(engine, data_dir):
    """Create all tables."""
    from askui.chat.api.db.base import Base

    Base.metadata.create_all(engine)
