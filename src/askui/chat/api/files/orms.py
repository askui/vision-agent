"""File database model."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from askui.chat.api.db.orm.base import Base
from askui.chat.api.db.orm.types import UnixDatetime, create_prefixed_id_type
from askui.chat.api.files.models import File

FileId = create_prefixed_id_type("file")


class FileOrm(Base):
    """File database model."""

    __tablename__ = "files"

    id: Mapped[str] = mapped_column(FileId, primary_key=True)
    workspace_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(UnixDatetime, nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    media_type: Mapped[str] = mapped_column(String, nullable=False)

    @classmethod
    def from_model(cls, model: File) -> "FileOrm":
        return cls(
            **model.model_dump(exclude={"object", "created_at"}),
            created_at=model.created_at,
        )

    def to_model(self) -> File:
        return File.model_validate(self, from_attributes=True)
