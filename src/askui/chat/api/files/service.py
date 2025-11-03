import logging
import mimetypes
import shutil
import tempfile
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from askui.chat.api.db.queries import list_all
from askui.chat.api.files.models import File, FileCreate
from askui.chat.api.files.orms import FileOrm
from askui.chat.api.models import FileId, WorkspaceId
from askui.utils.api_utils import (
    FileTooLargeError,
    ForbiddenError,
    ListQuery,
    ListResponse,
    NotFoundError,
)

logger = logging.getLogger(__name__)

# Constants
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB supported
CHUNK_SIZE = 1024 * 1024  # 1MB for uploading and downloading


class FileService:
    """Service for managing File resources with database persistence."""

    def __init__(self, session: Session, data_dir: Path) -> None:
        self._session = session
        self._data_dir = data_dir

    def _find_by_id(self, workspace_id: WorkspaceId | None, file_id: FileId) -> FileOrm:
        """Find file by ID."""
        file_orm: FileOrm | None = (
            self._session.query(FileOrm)
            .filter(
                FileOrm.id == file_id,
                or_(
                    FileOrm.workspace_id == workspace_id,
                    FileOrm.workspace_id.is_(None),
                ),
            )
            .first()
        )
        if file_orm is None:
            error_msg = f"File {file_id} not found"
            raise NotFoundError(error_msg)
        return file_orm

    def _get_static_file_path(self, file: File) -> Path:
        """Get the path for the static file based on extension."""
        # For application/octet-stream, don't add .bin extension
        extension = ""
        if file.media_type != "application/octet-stream":
            extension = mimetypes.guess_extension(file.media_type) or ""
        base_name = f"{file.id}{extension}"
        path = self._data_dir / "static" / base_name
        if file.workspace_id is not None:
            path = (
                self._data_dir
                / "workspaces"
                / str(file.workspace_id)
                / "static"
                / base_name
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def list_(
        self, workspace_id: WorkspaceId | None, query: ListQuery
    ) -> ListResponse[File]:
        """List files with pagination and filtering."""
        q = self._session.query(FileOrm).filter(
            or_(
                FileOrm.workspace_id == workspace_id,
                FileOrm.workspace_id.is_(None),
            ),
        )
        orms: list[FileOrm]
        orms, has_more = list_all(q, query, FileOrm.id)
        data = [orm.to_model() for orm in orms]
        return ListResponse(
            data=data,
            has_more=has_more,
            first_id=data[0].id if data else None,
            last_id=data[-1].id if data else None,
        )

    def retrieve(self, workspace_id: WorkspaceId | None, file_id: FileId) -> File:
        """Retrieve file metadata by ID."""
        file_orm = self._find_by_id(workspace_id, file_id)
        return file_orm.to_model()

    def delete(
        self, workspace_id: WorkspaceId | None, file_id: FileId, force: bool = False
    ) -> None:
        """Delete a file and its content.

        *Important*: We may be left with a static file that is not associated with any
        file metadata if this fails.
        """
        file_orm = self._find_by_id(workspace_id, file_id)
        file = file_orm.to_model()
        if file.workspace_id is None and not force:
            error_msg = f"Default file {file_id} cannot be deleted"
            raise ForbiddenError(error_msg)
        self._session.delete(file_orm)
        self._session.commit()
        static_path = self._get_static_file_path(file)
        static_path.unlink()

    def retrieve_file_content(
        self, workspace_id: WorkspaceId | None, file_id: FileId
    ) -> tuple[File, Path]:
        """Get file metadata and path for downloading."""
        file = self.retrieve(workspace_id, file_id)
        static_path = self._get_static_file_path(file)
        return file, static_path

    async def _write_to_temp_file(
        self,
        file: UploadFile,
    ) -> tuple[FileCreate, Path]:
        size = 0
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".temp",
        )
        temp_path = Path(temp_file.name)
        with temp_file:
            while chunk := await file.read(CHUNK_SIZE):
                temp_file.write(chunk)
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise FileTooLargeError(MAX_FILE_SIZE)
        mime_type = file.content_type or "application/octet-stream"
        params = FileCreate(
            filename=file.filename,
            size=size,
            media_type=mime_type,
        )
        return params, temp_path

    def create(
        self, workspace_id: WorkspaceId | None, params: FileCreate, path: Path
    ) -> File:
        """Create a file and its content.

        *Important*: We may be left with a static file that is not associated with any
        file metadata if this fails.
        """
        file_model = File.create(workspace_id, params)
        static_path = self._get_static_file_path(file_model)
        shutil.move(path, static_path)
        file_orm = FileOrm.from_model(file_model)
        self._session.add(file_orm)
        self._session.commit()
        return file_model

    async def upload_file(
        self,
        workspace_id: WorkspaceId | None,
        file: UploadFile,
    ) -> File:
        """Upload a file.

        *Important*: We may be left with a static file that is not associated with any
        file metadata if this fails.
        """
        temp_path: Path | None = None
        try:
            params, temp_path = await self._write_to_temp_file(file)
            file_model = self.create(workspace_id, params, temp_path)
        except Exception:
            logger.exception("Failed to upload file")
            raise
        else:
            return file_model
        finally:
            if temp_path:
                temp_path.unlink(missing_ok=True)
