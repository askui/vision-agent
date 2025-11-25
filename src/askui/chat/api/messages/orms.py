"""Message database model."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from askui.chat.api.assistants.orms import AssistantId
from askui.chat.api.db.orm.base import Base
from askui.chat.api.db.orm.types import (
    RunId,
    ThreadId,
    UnixDatetime,
    create_prefixed_id_type,
)
from askui.chat.api.messages.models import Message

MessageId = create_prefixed_id_type("msg")


class MessageOrm(Base):
    """Message database model."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(MessageId, primary_key=True)
    thread_id: Mapped[str] = mapped_column(
        ThreadId,
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(UnixDatetime, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str | list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    stop_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    assistant_id: Mapped[str | None] = mapped_column(
        AssistantId, ForeignKey("assistants.id", ondelete="SET NULL"), nullable=True
    )
    run_id: Mapped[str | None] = mapped_column(
        RunId, ForeignKey("runs.id", ondelete="SET NULL"), nullable=True
    )
    parent_id: Mapped[str] = mapped_column(
        MessageId,
        nullable=False,
        index=True,
    )

    @classmethod
    def from_model(cls, model: Message) -> "MessageOrm":
        return cls(
            **model.model_dump(exclude={"object", "created_at"}),
            created_at=model.created_at,
        )

    def to_model(self) -> Message:
        return Message.model_validate(self, from_attributes=True)
