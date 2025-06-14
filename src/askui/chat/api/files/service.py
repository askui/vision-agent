from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from askui.chat.api.models import FileId, ListQuery, ListResponse, UnixDatetime
from askui.chat.api.utils import generate_time_ordered_id

FilePurpose = Literal["assistants", "assistants_output", "vision"]


class File(BaseModel):
    """A file that can be used in a thread."""

    id: FileId = Field(default_factory=lambda: generate_time_ordered_id("file"))
    bytes: int
    created_at: UnixDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    filename: str
    object: Literal["file"] = "file"


class FileService:
    """Service for managing files."""

    def __init__(self, base_dir: Path) -> None:
        """Initialize file service.

        Args:
            base_dir (Path): Base directory to store file data
        """
        self._base_dir = base_dir
        self._files_dir = base_dir / "files"

    def list_(self, query: ListQuery) -> ListResponse[File]:
        """List all available files.

        Args:
            query (ListQuery): Query parameters for listing files

        Returns:
            ListResponse[File]: ListResponse containing files sorted by creation date
        """
        if not self._files_dir.exists():
            return ListResponse(data=[])

        file_files = list(self._files_dir.glob("*.json"))
        files: list[File] = []
        for f in file_files:
            with f.open("r") as file:
                files.append(File.model_validate_json(file.read()))

        # Sort by creation date
        files = sorted(
            files, key=lambda f: f.created_at, reverse=(query.order == "desc")
        )

        # Apply before/after filters
        if query.after:
            files = [f for f in files if f.id > query.after]
        if query.before:
            files = [f for f in files if f.id < query.before]

        # Apply limit
        files = files[: query.limit]

        return ListResponse(
            data=files,
            first_id=files[0].id if files else None,
            last_id=files[-1].id if files else None,
            has_more=len(file_files) > query.limit,
        )

    def retrieve(self, file_id: FileId) -> File:
        """Retrieve a file by ID.

        Args:
            file_id (FileId): ID of file to retrieve

        Returns:
            File: Retrieved file object

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_file = self._files_dir / f"{file_id}.json"
        if not file_file.exists():
            error_msg = f"File {file_id} not found"
            raise FileNotFoundError(error_msg)

        with file_file.open("r") as f:
            return File.model_validate_json(f.read())

    def create(self, file_path: Path, filename: str | None = None) -> File:
        """Create a new file.

        Args:
            file_path (Path): Path to the file to upload
            filename (str | None, optional): Original filename. If None, uses file_path.name

        Returns:
            File: Created file object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is too large (>512MB)
        """
        if not file_path.exists():
            error_msg = f"File {file_path} not found"
            raise FileNotFoundError(error_msg)

        # Check file size (max 512MB)
        file_size = file_path.stat().st_size
        if file_size > 512 * 1024 * 1024:
            error_msg = "File size exceeds 512MB limit"
            raise ValueError(error_msg)

        file = File(
            bytes=file_size,
            filename=filename or file_path.name,
        )

        # Create files directory if it doesn't exist
        self._files_dir.mkdir(parents=True, exist_ok=True)

        # Save file metadata
        file_file = self._files_dir / f"{file.id}.json"
        with file_file.open("w") as f:
            f.write(file.model_dump_json())

        # Copy file to files directory
        file_content_path = self._files_dir / file.id
        with file_path.open("rb") as src, file_content_path.open("wb") as dst:
            dst.write(src.read())

        return file

    def delete(self, file_id: FileId) -> None:
        """Delete a file.

        Args:
            file_id (FileId): ID of file to delete

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_file = self._files_dir / f"{file_id}.json"
        if not file_file.exists():
            error_msg = f"File {file_id} not found"
            raise FileNotFoundError(error_msg)

        # Delete file metadata
        file_file.unlink()

        # Delete file content
        file_content_path = self._files_dir / file_id
        if file_content_path.exists():
            file_content_path.unlink()

    def get_content(self, file_id: FileId) -> bytes:
        """Get file content.

        Args:
            file_id (FileId): ID of file to get content for

        Returns:
            bytes: File content as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_content_path = self._files_dir / file_id
        if not file_content_path.exists():
            error_msg = f"File {file_id} not found"
            raise FileNotFoundError(error_msg)

        with file_content_path.open("rb") as f:
            return f.read()
