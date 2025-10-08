"""Migration version database model."""

from askui.chat.api.db.base import Base
from sqlalchemy import Column, DateTime, Integer


class MigrationVersionModel(Base):
    """Migration version tracking model."""

    __tablename__ = "migration_version"
    version = Column(Integer, primary_key=True)
    applied_at = Column(DateTime, nullable=False)
