"""Assistant database model."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from askui.chat.api.assistants.models import Assistant
from askui.chat.api.db.orm.base import Base
from askui.chat.api.db.orm.types import UnixDatetime, create_prefixed_id_type

AssistantId = create_prefixed_id_type("asst")


class AssistantOrm(Base):
    """Assistant database model."""

    __tablename__ = "assistants"

    id: Mapped[str] = mapped_column(AssistantId, primary_key=True)
    workspace_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(UnixDatetime, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar: Mapped[str | None] = mapped_column(Text, nullable=True)
    tools: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    system: Mapped[str | None] = mapped_column(Text, nullable=True)

    @classmethod
    def from_model(cls, model: Assistant) -> "AssistantOrm":
        return cls(
            **model.model_dump(exclude={"object", "created_at"}),
            created_at=model.created_at,
        )

    def to_model(self) -> Assistant:
        return Assistant.model_validate(self, from_attributes=True)
