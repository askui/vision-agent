"""Integration tests for the FileService class."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import UploadFile

from askui.chat.api.files.models import File, FileCreateParams
from askui.chat.api.files.service import FileService
from askui.chat.api.models import FileId
from askui.utils.api_utils import ConflictError, FileTooLargeError, NotFoundError


class TestFileService:
    """Test suite for the FileService class."""

    @pytest.fixture
    def temp_workspace_dir(self) -> Path:
        """Create a temporary workspace directory for testing."""
        temp_dir = tempfile.mkdtemp()
        return Path(temp_dir)

    @pytest.fixture
    def file_service(self, temp_workspace_dir: Path) -> FileService:
        """Create a FileService instance with temporary workspace."""
        return FileService(temp_workspace_dir)

    @pytest.fixture
    def sample_file_params(self) -> FileCreateParams:
        """Create sample file creation parameters."""
        return FileCreateParams(filename="test.txt", size=32, media_type="text/plain")

    def test_get_file_path_new_file(self, file_service: FileService) -> None:
        """Test getting file path for a new file."""
        file_id = FileId("file_test123")
        file_path = file_service._get_file_path(file_id, new=True)

        expected_path = file_service._files_dir / "file_test123.json"
        assert file_path == expected_path

    def test_get_file_path_existing_file(self, file_service: FileService) -> None:
        """Test getting file path for an existing file."""
        file_id = FileId("file_test123")

        # Create the file first
        file_path = file_service._files_dir / "file_test123.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text('{"id": "file_test123"}')

        result_path = file_service._get_file_path(file_id, new=False)
        assert result_path == file_path

    def test_get_file_path_new_file_conflict(self, file_service: FileService) -> None:
        """Test that getting path for new file raises ConflictError if file exists."""
        file_id = FileId("file_test123")

        # Create the file first
        file_path = file_service._files_dir / "file_test123.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text('{"id": "file_test123"}')

        with pytest.raises(ConflictError):
            file_service._get_file_path(file_id, new=True)

    def test_get_file_path_existing_file_not_found(
        self, file_service: FileService
    ) -> None:
        """Test that getting path for existing file raises NotFoundError if file
        doesn't exist."""
        file_id = FileId("file_test123")

        with pytest.raises(NotFoundError):
            file_service._get_file_path(file_id, new=False)

    def test_get_static_file_path(self, file_service: FileService) -> None:
        """Test getting static file path based on file extension."""
        file = File(
            id="file_test123",
            object="file",
            created_at=1234567890,
            filename="test.txt",
            size=32,
            media_type="text/plain",
        )

        static_path = file_service._get_static_file_path(file)
        expected_path = file_service._static_dir / "file_test123.txt"
        assert static_path == expected_path

    def test_get_static_file_path_no_extension(self, file_service: FileService) -> None:
        """Test getting static file path when MIME type has no extension."""
        file = File(
            id="file_test123",
            object="file",
            created_at=1234567890,
            filename="test",
            size=32,
            media_type="application/octet-stream",
        )

        static_path = file_service._get_static_file_path(file)
        expected_path = file_service._static_dir / "file_test123"
        assert static_path == expected_path

    def test_list_files_empty(self, file_service: FileService) -> None:
        """Test listing files when no files exist."""
        from askui.utils.api_utils import ListQuery

        query = ListQuery()
        result = file_service.list_(query)

        assert result.object == "list"
        assert result.data == []
        assert result.has_more is False

    def test_list_files_with_files(
        self, file_service: FileService, sample_file_params: FileCreateParams
    ) -> None:
        """Test listing files when files exist."""
        from askui.utils.api_utils import ListQuery

        # Create a file first
        temp_file = Path(tempfile.mktemp())
        file_content = b"test content"
        temp_file.write_bytes(file_content)

        # Update the size to match the actual file content
        params = FileCreateParams(
            filename=sample_file_params.filename,
            size=len(file_content),
            media_type=sample_file_params.media_type,
        )

        try:
            file = file_service.create(params, temp_file)

            query = ListQuery()
            result = file_service.list_(query)

            assert result.object == "list"
            assert len(result.data) == 1
            assert result.data[0].id == file.id
            assert result.data[0].filename == file.filename
        finally:
            temp_file.unlink(missing_ok=True)

    def test_retrieve_file_success(
        self, file_service: FileService, sample_file_params: FileCreateParams
    ) -> None:
        """Test successful file retrieval."""
        # Create a file first
        temp_file = Path(tempfile.mktemp())
        file_content = b"test content"
        temp_file.write_bytes(file_content)

        # Update the size to match the actual file content
        params = FileCreateParams(
            filename=sample_file_params.filename,
            size=len(file_content),
            media_type=sample_file_params.media_type,
        )

        try:
            file = file_service.create(params, temp_file)

            retrieved_file = file_service.retrieve(file.id)

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
            file_service.retrieve(file_id)

    def test_delete_file_success(
        self, file_service: FileService, sample_file_params: FileCreateParams
    ) -> None:
        """Test successful file deletion."""
        # Create a file first
        temp_file = Path(tempfile.mktemp())
        file_content = b"test content"
        temp_file.write_bytes(file_content)

        # Update the size to match the actual file content
        params = FileCreateParams(
            filename=sample_file_params.filename,
            size=len(file_content),
            media_type=sample_file_params.media_type,
        )

        try:
            file = file_service.create(params, temp_file)

            # Verify file exists by retrieving it
            retrieved_file = file_service.retrieve(file.id)
            assert retrieved_file.id == file.id

            # Delete the file
            file_service.delete(file.id)

            # Verify file is deleted by trying to retrieve it
            # (should raise NotFoundError)
            with pytest.raises(NotFoundError):
                file_service.retrieve(file.id)
        finally:
            temp_file.unlink(missing_ok=True)

    def test_delete_file_not_found(self, file_service: FileService) -> None:
        """Test file deletion when file doesn't exist."""
        file_id = FileId("file_nonexistent123")

        with pytest.raises(NotFoundError):
            file_service.delete(file_id)

    def test_retrieve_file_content_success(
        self, file_service: FileService, sample_file_params: FileCreateParams
    ) -> None:
        """Test successful file content retrieval."""
        # Create a file first
        temp_file = Path(tempfile.mktemp())
        file_content = b"test content"
        temp_file.write_bytes(file_content)

        # Update the size to match the actual file content
        params = FileCreateParams(
            filename=sample_file_params.filename,
            size=len(file_content),
            media_type=sample_file_params.media_type,
        )

        try:
            file = file_service.create(params, temp_file)

            retrieved_file, file_path = file_service.retrieve_file_content(file.id)

            assert retrieved_file.id == file.id
            assert file_path.exists()
        finally:
            temp_file.unlink(missing_ok=True)

    def test_retrieve_file_content_not_found(self, file_service: FileService) -> None:
        """Test file content retrieval when file doesn't exist."""
        file_id = FileId("file_nonexistent123")

        with pytest.raises(NotFoundError):
            file_service.retrieve_file_content(file_id)

    def test_create_file_success(
        self, file_service: FileService, sample_file_params: FileCreateParams
    ) -> None:
        """Test successful file creation."""
        temp_file = Path(tempfile.mktemp())
        file_content = b"test content"
        temp_file.write_bytes(file_content)

        try:
            # Update the size to match the actual file content
            params = FileCreateParams(
                filename=sample_file_params.filename,
                size=len(file_content),
                media_type=sample_file_params.media_type,
            )

            file = file_service.create(params, temp_file)

            assert file.id.startswith("file_")
            assert file.filename == params.filename
            assert file.size == params.size
            assert file.media_type == params.media_type
            # created_at is a datetime, compare with timezone-aware datetime
            from datetime import datetime, timezone

            assert isinstance(file.created_at, datetime)
            assert file.created_at > datetime(2020, 1, 1, tzinfo=timezone.utc)

            # Verify metadata file was created
            metadata_path = file_service._get_file_path(file.id, new=False)
            assert metadata_path.exists()

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

        params = FileCreateParams(
            filename=None, size=len(file_content), media_type="text/plain"
        )

        try:
            file = file_service.create(params, temp_file)

            # Should auto-generate filename with extension
            assert file.filename.endswith(".txt")
            assert file.filename.startswith("file_")

        finally:
            temp_file.unlink(missing_ok=True)

    def test_save_file_new(
        self, file_service: FileService, sample_file_params: FileCreateParams
    ) -> None:
        """Test saving a new file."""
        file = File.create(sample_file_params)

        file_service._save(file, new=True)

        # Verify file was saved
        saved_path = file_service._get_file_path(file.id, new=False)
        assert saved_path.exists()

        # Verify content is correct
        saved_content = saved_path.read_text()
        saved_file = File.model_validate_json(saved_content)
        assert saved_file.id == file.id
        assert saved_file.filename == file.filename

    def test_save_file_existing(
        self, file_service: FileService, sample_file_params: FileCreateParams
    ) -> None:
        """Test saving an existing file."""
        file = File.create(sample_file_params)

        # Save file first time
        file_service._save(file, new=True)

        # Modify and save again
        file.filename = "modified.txt"
        file_service._save(file, new=False)

        # Verify changes were saved
        saved_path = file_service._get_file_path(file.id, new=False)
        saved_content = saved_path.read_text()
        saved_file = File.model_validate_json(saved_content)
        assert saved_file.filename == "modified.txt"

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

        file = await file_service.upload_file(mock_upload_file)

        assert file.filename == "test.txt"
        assert file.size == len(file_content)
        assert file.media_type == "text/plain"
        assert file.id.startswith("file_")

        # Verify files were created
        metadata_path = file_service._get_file_path(file.id, new=False)
        static_path = file_service._get_static_file_path(file)
        assert metadata_path.exists()
        assert static_path.exists()

    @pytest.mark.asyncio
    async def test_upload_file_upload_failure(self, file_service: FileService) -> None:
        """Test file upload when writing fails."""
        mock_upload_file = AsyncMock(spec=UploadFile)
        mock_upload_file.filename = "test.txt"
        mock_upload_file.content_type = "text/plain"
        mock_upload_file.read.side_effect = Exception("Simulated upload failure")

        with pytest.raises(Exception, match="Simulated upload failure"):
            await file_service.upload_file(mock_upload_file)
