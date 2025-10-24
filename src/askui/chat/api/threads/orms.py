"""Thread database model."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from askui.chat.api.db.orm.base import Base
from askui.chat.api.db.orm.types import UnixDatetime, create_prefixed_id_type
from askui.chat.api.threads.models import Thread

ThreadId = create_prefixed_id_type("thread")


class ThreadOrm(Base):
    """Thread database model."""

    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(ThreadId, primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(UnixDatetime, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)

    @classmethod
    def from_model(cls, model: Thread) -> "ThreadOrm":
        return cls(**model.model_dump(exclude={"object"}))

    def to_model(self) -> Thread:
        return Thread.model_validate(self, from_attributes=True)
