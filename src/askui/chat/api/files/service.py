import mimetypes
import shutil
import tempfile
from pathlib import Path

from fastapi import UploadFile

from askui.chat.api.files.models import File, FileCreateParams
from askui.chat.api.models import FileId
from askui.logger import logger
from askui.utils.api_utils import (
    ConflictError,
    FileTooLargeError,
    ListQuery,
    ListResponse,
    NotFoundError,
    list_resources,
)

# Constants
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB supported
CHUNK_SIZE = 1024 * 1024  # 1MB for uploading and downloading


class FileService:
    """Service for managing File resources with filesystem persistence."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._files_dir = base_dir / "files"
        self._static_dir = base_dir / "static"

    def _get_file_path(self, file_id: FileId, new: bool = False) -> Path:
        """Get the path for file metadata."""
        file_path = self._files_dir / f"{file_id}.json"
        exists = file_path.exists()
        if new and exists:
            error_msg = f"File {file_id} already exists"
            raise ConflictError(error_msg)
        if not new and not exists:
            error_msg = f"File {file_id} not found"
            raise NotFoundError(error_msg)
        return file_path

    def _get_static_file_path(self, file: File) -> Path:
        """Get the path for the static file based on extension."""
        # For application/octet-stream, don't add .bin extension
        extension = ""
        if file.media_type != "application/octet-stream":
            extension = mimetypes.guess_extension(file.media_type) or ""
        return self._static_dir / f"{file.id}{extension}"

    def list_(self, query: ListQuery) -> ListResponse[File]:
        """List files with pagination and filtering."""
        return list_resources(self._files_dir, query, File)

    def retrieve(self, file_id: FileId) -> File:
        """Retrieve file metadata by ID."""
        try:
            file_path = self._get_file_path(file_id)
            return File.model_validate_json(file_path.read_text())
        except FileNotFoundError as e:
            error_msg = f"File {file_id} not found"
            raise NotFoundError(error_msg) from e

    def delete(self, file_id: FileId) -> None:
        """Delete a file and its content.

        *Important*: We may be left with a static file that is not associated with any
        file metadata if this fails.
        """
        try:
            file = self.retrieve(file_id)
            static_path = self._get_static_file_path(file)
            self._get_file_path(file_id).unlink()
            if static_path.exists():
                static_path.unlink()
        except FileNotFoundError as e:
            error_msg = f"File {file_id} not found"
            raise NotFoundError(error_msg) from e

    def retrieve_file_content(self, file_id: FileId) -> tuple[File, Path]:
        """Get file metadata and path for downloading."""
        file = self.retrieve(file_id)
        static_path = self._get_static_file_path(file)
        return file, static_path

    async def _write_to_temp_file(
        self,
        file: UploadFile,
    ) -> tuple[FileCreateParams, Path]:
        size = 0
        self._static_dir.mkdir(parents=True, exist_ok=True)
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            dir=self._static_dir,
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
        params = FileCreateParams(
            filename=file.filename,
            size=size,
            media_type=mime_type,
        )
        return params, temp_path

    def create(self, params: FileCreateParams, path: Path) -> File:
        file_model = File.create(params)
        self._static_dir.mkdir(parents=True, exist_ok=True)
        static_path = self._get_static_file_path(file_model)
        shutil.move(path, static_path)
        self._save(file_model, new=True)

        return file_model

    async def upload_file(
        self,
        file: UploadFile,
    ) -> File:
        """Upload a file.

        *Important*: We may be left with a static file that is not associated with any
        file metadata if this fails.
        """
        temp_path: Path | None = None
        try:
            params, temp_path = await self._write_to_temp_file(file)
            file_model = self.create(params, temp_path)
        except Exception as e:
            logger.error(f"Failed to upload file: {e}", exc_info=True)
            raise
        else:
            return file_model
        finally:
            if temp_path:
                temp_path.unlink(missing_ok=True)

    def _save(self, file: File, new: bool = False) -> None:
        self._files_dir.mkdir(parents=True, exist_ok=True)
        file_path = self._get_file_path(file.id, new=new)
        content = file.model_dump_json()
        file_path.write_text(content, encoding="utf-8")
