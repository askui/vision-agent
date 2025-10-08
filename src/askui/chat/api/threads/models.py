"""Thread database model."""

from datetime import datetime, timezone

from askui.chat.api.db.base import Base
from askui.chat.api.db.types import ThreadId
from askui.chat.api.threads.schemas import Thread, ThreadCreateParams
from bson import ObjectId
from sqlalchemy import Column, DateTime, String


class ThreadModel(Base):
    """Thread database model."""

    __tablename__ = "threads"
    id = Column(ThreadId, primary_key=True)
    created_at = Column(DateTime, nullable=False, index=True)
    name = Column(String(128), nullable=True)

    @staticmethod
    def create_id() -> str:
        """Create a new thread ID with prefix."""
        return f"thread_{ObjectId()}"

    def to_pydantic(self) -> Thread:
        """Convert to Pydantic model."""
        # Ensure created_at is timezone-aware
        created_at = self.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        return Thread(
            id=self.id,  # Prefix is handled by the specialized type
            created_at=created_at,
            name=self.name,
        )

    @classmethod
    def from_pydantic(cls, thread: Thread) -> "ThreadModel":
        """Create from Pydantic model."""
        return cls(
            id=thread.id,
            created_at=thread.created_at,
            name=thread.name,
        )

    @classmethod
    def from_create_params(cls, params: ThreadCreateParams) -> "ThreadModel":
        """Create from create parameters."""
        return cls(
            id=cls.create_id(),
            created_at=datetime.now(timezone.utc),
            name=params.name,
        )
