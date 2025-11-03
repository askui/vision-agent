"""Run database model."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import String

from askui.chat.api.assistants.orms import AssistantId
from askui.chat.api.db.orm.base import Base
from askui.chat.api.db.orm.types import ThreadId, UnixDatetime, create_prefixed_id_type
from askui.chat.api.runs.models import Run

RunId = create_prefixed_id_type("run")


class RunOrm(Base):
    """Run database model."""

    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(RunId, primary_key=True)
    thread_id: Mapped[str] = mapped_column(
        ThreadId,
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(UnixDatetime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UnixDatetime, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(UnixDatetime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(UnixDatetime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(UnixDatetime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(UnixDatetime, nullable=True)
    tried_cancelling_at: Mapped[datetime | None] = mapped_column(
        UnixDatetime, nullable=True
    )
    last_error: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    assistant_id: Mapped[str | None] = mapped_column(
        AssistantId, ForeignKey("assistants.id", ondelete="SET NULL"), nullable=True
    )

    @classmethod
    def from_model(cls, model: Run) -> "RunOrm":
        return cls(**model.model_dump(exclude={"object"}))

    def to_model(self) -> Run:
        return Run.model_validate(self, from_attributes=True)
