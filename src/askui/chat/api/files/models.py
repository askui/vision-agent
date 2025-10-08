"""File database model."""

from datetime import datetime, timezone

from askui.chat.api.db.base import Base
from askui.chat.api.db.types import FileId
from askui.chat.api.files.schemas import File as FileSchema
from bson import ObjectId
from sqlalchemy import Column, DateTime, Integer, String


class FileModel(Base):
    """File database model."""

    __tablename__ = "files"
    id = Column(FileId, primary_key=True)
    created_at = Column(DateTime, nullable=False, index=True)
    filename = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    media_type = Column(String, nullable=False)

    @staticmethod
    def create_id() -> str:
        """Create a new file ID with prefix."""
        return f"file_{ObjectId()}"

    def to_pydantic(self) -> FileSchema:
        """Convert to Pydantic model."""
        return FileSchema(
            id=self.id,  # Prefix is handled by the specialized type
            created_at=self.created_at,
            filename=self.filename,
            size=self.size,
            media_type=self.media_type,
        )

    @classmethod
    def from_pydantic(cls, file: FileSchema) -> "FileModel":
        """Create from Pydantic model."""
        return cls(
            id=file.id,
            created_at=file.created_at,
            filename=file.filename,
            size=file.size,
            media_type=file.media_type,
        )

    @classmethod
    def from_create_params(
        cls, filename: str, size: int, media_type: str
    ) -> "FileModel":
        """Create from create parameters."""
        return cls(
            id=cls.create_id(),
            created_at=datetime.now(timezone.utc),
            filename=filename,
            size=size,
            media_type=media_type,
        )
