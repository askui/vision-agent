"""File service with SQLAlchemy persistence."""

import logging
import shutil
from pathlib import Path
from typing import Callable

from askui.chat.api.db.query_builder import QueryBuilder
from askui.chat.api.files.models import FileModel
from askui.chat.api.files.schemas import File
from askui.chat.api.models import FileId
from askui.utils.api_utils import (
    FileTooLargeError,
    ListQuery,
    ListResponse,
    NotFoundError,
)
from fastapi import UploadFile
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Constants
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB supported


class FileService:
    """Service for managing File resources with SQLAlchemy persistence."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory
        self._files_dir = Path.cwd() / "chat" / "files"
        self._static_dir = Path.cwd() / "chat" / "static"

    def _to_pydantic(self, db_model: FileModel) -> File:
        """Convert SQLAlchemy model to Pydantic model."""
        return db_model.to_pydantic()

    def list_(self, query: ListQuery) -> ListResponse[File]:
        """List files with pagination."""
        with self._session_factory() as session:
            q = session.query(FileModel)

            # Apply list query parameters
            q = QueryBuilder.apply_list_query(
                q, FileModel, query, FileModel.created_at, FileModel.id
            )

            # Apply limit
            limit = query.limit or 20
            q = q.limit(limit + 1)  # +1 to check if there are more

            results = q.all()
            return QueryBuilder.build_list_response(results, limit, self._to_pydantic)

    def retrieve(self, file_id: FileId) -> File:
        """Retrieve a file by ID."""
        with self._session_factory() as session:
            db_file = session.query(FileModel).filter(FileModel.id == file_id).first()
            if not db_file:
                error_msg = f"File {file_id} not found"
                raise NotFoundError(error_msg)
            return self._to_pydantic(db_file)

    def create(
        self, filename: str, size: int, media_type: str, file: UploadFile
    ) -> File:
        """Create a new file."""
        # Check file size
        if file.size and file.size > MAX_FILE_SIZE:
            error_msg = (
                f"File size {file.size} exceeds maximum allowed size {MAX_FILE_SIZE}"
            )
            raise FileTooLargeError(MAX_FILE_SIZE)

        with self._session_factory() as session:
            # Create database record
            db_file = FileModel.from_create_params(filename, size, media_type)
            session.add(db_file)
            session.commit()
            session.refresh(db_file)

            # Save file content to filesystem
            self._files_dir.mkdir(parents=True, exist_ok=True)
            file_path = self._files_dir / db_file.id
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            return self._to_pydantic(db_file)

    def delete(self, file_id: FileId) -> None:
        """Delete a file."""
        with self._session_factory() as session:
            db_file = session.query(FileModel).filter(FileModel.id == file_id).first()
            if not db_file:
                error_msg = f"File {file_id} not found"
                raise NotFoundError(error_msg)

            # Delete file from filesystem
            file_path = self._files_dir / file_id
            if file_path.exists():
                file_path.unlink()

            # Delete database record
            session.delete(db_file)
            session.commit()

    def get_file_path(self, file_id: FileId) -> Path:
        """Get the filesystem path for a file."""
        return self._files_dir / file_id

    async def upload_file(self, file: UploadFile) -> File:
        """Upload a file (async wrapper for create)."""
        filename = file.filename or "unknown"
        size = file.size or 0
        media_type = file.content_type or "application/octet-stream"
        return self.create(filename, size, media_type, file)

    def retrieve_file_content(self, file_id: FileId) -> tuple[File, Path]:
        """Retrieve file metadata and filesystem path."""
        file_metadata = self.retrieve(file_id)
        file_path = self.get_file_path(file_id)
        return file_metadata, file_path
        return file_metadata, file_path
        return file_metadata, file_path
