"""Integration tests for the FileService class."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import UploadFile
from sqlalchemy.orm import Session

from askui.chat.api.files.models import File, FileCreate
from askui.chat.api.files.service import FileService
from askui.chat.api.models import FileId
from askui.utils.api_utils import FileTooLargeError, NotFoundError


class TestFileService:
    """Test suite for the FileService class."""

    @pytest.fixture
    def temp_workspace_dir(self) -> Path:
        """Create a temporary workspace directory for testing."""
        temp_dir = tempfile.mkdtemp()
        return Path(temp_dir)

    @pytest.fixture
    def file_service(
        self, test_db_session: Session, temp_workspace_dir: Path
    ) -> FileService:
        """Create a FileService instance with temporary workspace."""
        return FileService(test_db_session, temp_workspace_dir)

    @pytest.fixture
    def sample_file_params(self) -> FileCreate:
        """Create sample file creation parameters."""
        return FileCreate(filename="test.txt", size=32, media_type="text/plain")

    def test_get_static_file_path(self, file_service: FileService) -> None:
        """Test getting static file path based on file extension."""
        from datetime import datetime, timezone

        file = File(
            id="file_test123",
            object="file",
            created_at=datetime.now(timezone.utc),
            filename="test.txt",
            size=32,
            media_type="text/plain",
            workspace_id=None,
        )

        static_path = file_service._get_static_file_path(file)
        expected_path = file_service._data_dir / "static" / "file_test123.txt"
        assert static_path == expected_path

    def test_get_static_file_path_no_extension(self, file_service: FileService) -> None:
        """Test getting static file path when MIME type has no extension."""
        from datetime import datetime, timezone

        file = File(
            id="file_test123",
            object="file",
            created_at=datetime.now(timezone.utc),
            filename="test",
            size=32,
            media_type="application/octet-stream",
            workspace_id=None,
        )

        static_path = file_service._get_static_file_path(file)
        expected_path = file_service._data_dir / "static" / "file_test123"
        assert static_path == expected_path

    def test_list_files_empty(self, file_service: FileService) -> None:
        """Test listing files when no files exist."""
        from askui.utils.api_utils import ListQuery

        query = ListQuery()
        result = file_service.list_(None, query)

        assert result.object == "list"
        assert result.data == []
        assert result.has_more is False

    def test_list_files_with_files(
        self, file_service: FileService, sample_file_params: FileCreate
    ) -> None:
        """Test listing files when files exist."""
        from askui.utils.api_utils import ListQuery

        # Create a file first
        temp_file = Path(tempfile.mktemp())
        file_content = b"test content"
        temp_file.write_bytes(file_content)

        # Update the size to match the actual file content
        params = FileCreate(
            filename=sample_file_params.filename,
            size=len(file_content),
            media_type=sample_file_params.media_type,
        )

        try:
            file = file_service.create(None, params, temp_file)

            query = ListQuery()
            result = file_service.list_(None, query)

            assert result.object == "list"
            assert len(result.data) == 1
            assert result.data[0].id == file.id
            assert result.data[0].filename == file.filename
        finally:
            temp_file.unlink(missing_ok=True)

    def test_retrieve_file_success(
        self, file_service: FileService, sample_file_params: FileCreate
    ) -> None:
        """Test successful file retrieval."""
        # Create a file first
        temp_file = Path(tempfile.mktemp())
        file_content = b"test content"
        temp_file.write_bytes(file_content)

        # Update the size to match the actual file content
        params = FileCreate(
            filename=sample_file_params.filename,
            size=len(file_content),
            media_type=sample_file_params.media_type,
        )

        try:
            file = file_service.create(None, params, temp_file)

            retrieved_file = file_service.retrieve(None, file.id)

            assert retrieved_file.id == file.id
            assert retrieved_file.filename == file.filename
            assert retrieved_file.size == file.size
            assert retrieved_file.media_type == file.media_type
        finally:
            temp_file.unlink(missing_ok=True)

    def test_retrieve_file_not_found(self, file_service: FileService) -> None:
        """Test file retrieval when file doesn't exist."""
        file_id = FileId("file_nonexistent123")

        with pytest.raises(NotFoundError):
            file_service.retrieve(None, file_id)

    def test_delete_file_success(
        self, file_service: FileService, sample_file_params: FileCreate
    ) -> None:
        """Test successful file deletion."""
        from uuid import UUID

        # Create a workspace_id for the test file (non-default files can be deleted)
        workspace_id = UUID("75592acb-9f48-4a10-8331-ea8faeed54a5")

        # Create a file first
        temp_file = Path(tempfile.mktemp())
        file_content = b"test content"
        temp_file.write_bytes(file_content)

        # Update the size to match the actual file content
        params = FileCreate(
            filename=sample_file_params.filename,
            size=len(file_content),
            media_type=sample_file_params.media_type,
        )

        try:
            file = file_service.create(workspace_id, params, temp_file)

            # Verify file exists by retrieving it
            retrieved_file = file_service.retrieve(workspace_id, file.id)
            assert retrieved_file.id == file.id

            # Delete the file
            file_service.delete(workspace_id, file.id)

            # Verify file is deleted by trying to retrieve it
            # (should raise NotFoundError)
            with pytest.raises(NotFoundError):
                file_service.retrieve(workspace_id, file.id)
        finally:
            temp_file.unlink(missing_ok=True)

    def test_delete_file_not_found(self, file_service: FileService) -> None:
        """Test file deletion when file doesn't exist."""
        file_id = FileId("file_nonexistent123")

        with pytest.raises(NotFoundError):
            file_service.delete(None, file_id)

    def test_retrieve_file_content_success(
        self, file_service: FileService, sample_file_params: FileCreate
    ) -> None:
        """Test successful file content retrieval."""
        # Create a file first
        temp_file = Path(tempfile.mktemp())
        file_content = b"test content"
        temp_file.write_bytes(file_content)

        # Update the size to match the actual file content
        params = FileCreate(
            filename=sample_file_params.filename,
            size=len(file_content),
            media_type=sample_file_params.media_type,
        )

        try:
            file = file_service.create(None, params, temp_file)

            retrieved_file, file_path = file_service.retrieve_file_content(
                None, file.id
            )

            assert retrieved_file.id == file.id
            assert file_path.exists()
        finally:
            temp_file.unlink(missing_ok=True)

    def test_retrieve_file_content_not_found(self, file_service: FileService) -> None:
        """Test file content retrieval when file doesn't exist."""
        file_id = FileId("file_nonexistent123")

        with pytest.raises(NotFoundError):
            file_service.retrieve_file_content(None, file_id)

    def test_create_file_success(
        self, file_service: FileService, sample_file_params: FileCreate
    ) -> None:
        """Test successful file creation."""
        temp_file = Path(tempfile.mktemp())
        file_content = b"test content"
        temp_file.write_bytes(file_content)

        try:
            # Update the size to match the actual file content
            params = FileCreate(
                filename=sample_file_params.filename,
                size=len(file_content),
                media_type=sample_file_params.media_type,
            )

            file = file_service.create(None, params, temp_file)

            assert file.id.startswith("file_")
            assert file.filename == params.filename
            assert file.size == params.size
            assert file.media_type == params.media_type
            # created_at is a datetime, compare with timezone-aware datetime
            from datetime import datetime, timezone

            assert isinstance(file.created_at, datetime)
            assert file.created_at > datetime(2020, 1, 1, tzinfo=timezone.utc)

            # Verify static file was moved
            static_path = file_service._get_static_file_path(file)
            assert static_path.exists()

        finally:
            temp_file.unlink(missing_ok=True)

    def test_create_file_without_filename(self, file_service: FileService) -> None:
        """Test file creation without filename."""
        temp_file = Path(tempfile.mktemp())
        file_content = b"test content"
        temp_file.write_bytes(file_content)

        params = FileCreate(
            filename=None, size=len(file_content), media_type="text/plain"
        )

        try:
            file = file_service.create(None, params, temp_file)

            # Should auto-generate filename with extension
            assert file.filename.endswith(".txt")
            assert file.filename.startswith("file_")

        finally:
            temp_file.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_write_to_temp_file_success(self, file_service: FileService) -> None:
        """Test successful writing to temporary file."""
        file_content = b"test file content"
        mock_upload_file = AsyncMock(spec=UploadFile)
        mock_upload_file.content_type = "text/plain"
        mock_upload_file.filename = None
        mock_upload_file.read.side_effect = [
            file_content,
            b"",
        ]  # Read content, then empty

        params, temp_path = await file_service._write_to_temp_file(mock_upload_file)

        assert params.filename is None  # No filename provided
        assert params.size == len(file_content)
        assert params.media_type == "text/plain"
        assert temp_path.exists()
        assert temp_path.read_bytes() == file_content

        # Cleanup
        temp_path.unlink()

    @pytest.mark.asyncio
    async def test_write_to_temp_file_large_size(
        self, file_service: FileService
    ) -> None:
        """Test writing to temporary file with size exceeding limit."""
        # Create content larger than 20MB
        large_content = b"x" * (21 * 1024 * 1024)
        mock_upload_file = AsyncMock(spec=UploadFile)
        mock_upload_file.content_type = "text/plain"
        mock_upload_file.filename = "test.txt"
        mock_upload_file.read.side_effect = [
            large_content,  # Read all content at once
        ]

        with pytest.raises(FileTooLargeError):
            await file_service._write_to_temp_file(mock_upload_file)

    @pytest.mark.asyncio
    async def test_write_to_temp_file_no_content_type(
        self, file_service: FileService
    ) -> None:
        """Test writing to temporary file without content type."""
        file_content = b"test content"
        mock_upload_file = AsyncMock(spec=UploadFile)
        mock_upload_file.content_type = None
        mock_upload_file.filename = "test.txt"
        mock_upload_file.read.side_effect = [file_content, b""]

        params, temp_path = await file_service._write_to_temp_file(mock_upload_file)

        assert params.media_type == "application/octet-stream"  # Default fallback

        # Cleanup
        temp_path.unlink()

    @pytest.mark.asyncio
    async def test_upload_file_success(self, file_service: FileService) -> None:
        """Test successful file upload."""
        file_content = b"test file content"
        mock_upload_file = AsyncMock(spec=UploadFile)
        mock_upload_file.filename = "test.txt"
        mock_upload_file.content_type = "text/plain"
        mock_upload_file.read.side_effect = [file_content, b""]

        file = await file_service.upload_file(None, mock_upload_file)

        assert file.filename == "test.txt"
        assert file.size == len(file_content)
        assert file.media_type == "text/plain"
        assert file.id.startswith("file_")

        # Verify static file was created
        static_path = file_service._get_static_file_path(file)
        assert static_path.exists()

    @pytest.mark.asyncio
    async def test_upload_file_upload_failure(self, file_service: FileService) -> None:
        """Test file upload when writing fails."""
        mock_upload_file = AsyncMock(spec=UploadFile)
        mock_upload_file.filename = "test.txt"
        mock_upload_file.content_type = "text/plain"
        mock_upload_file.read.side_effect = Exception("Simulated upload failure")

        with pytest.raises(Exception, match="Simulated upload failure"):
            await file_service.upload_file(None, mock_upload_file)
