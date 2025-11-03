"""Integration tests for the files API endpoints."""

import io
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from askui.chat.api.files.models import File
from askui.chat.api.files.orms import FileOrm
from askui.chat.api.files.service import FileService
from askui.chat.api.models import FileId
from askui.utils.api_utils import NotFoundError


class TestFilesAPI:
    """Test suite for the files API endpoints."""

    def _add_file_to_db(self, file: File, test_db_session: Session) -> None:
        """Add a file to the test database."""
        file_orm = FileOrm.from_model(file)
        test_db_session.add(file_orm)
        test_db_session.commit()

    def test_list_files_empty(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test listing files when no files exist."""
        response = test_client.get("/v1/files", headers=test_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["object"] == "list"
        assert data["data"] == []
        assert data["has_more"] is False

    def test_list_files_with_files(
        self,
        test_headers: dict[str, str],
        test_db_session: Session,
    ) -> None:
        """Test listing files when files exist."""
        # Create a mock file in the temporary workspace
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        files_dir = workspace_path / "files"
        files_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock file
        workspace_id = UUID(test_headers["askui-workspace"])
        mock_file = File(
            id="file_test123",
            object="file",
            created_at=datetime.fromtimestamp(1234567890, tz=timezone.utc),
            filename="test.txt",
            size=32,
            media_type="text/plain",
            workspace_id=workspace_id,
        )
        (files_dir / "file_test123.json").write_text(mock_file.model_dump_json())

        # Add file to database
        self._add_file_to_db(mock_file, test_db_session)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(test_db_session, workspace_path)

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service

        try:
            with TestClient(app) as client:
                response = client.get("/v1/files", headers=test_headers)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["object"] == "list"
                assert len(data["data"]) == 1
                assert data["data"][0]["id"] == "file_test123"
                assert data["data"][0]["filename"] == "test.txt"
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_list_files_with_pagination(
        self, test_headers: dict[str, str], test_db_session: Session
    ) -> None:
        """Test listing files with pagination parameters."""
        # Create multiple mock files in the temporary workspace
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        files_dir = workspace_path / "files"
        files_dir.mkdir(parents=True, exist_ok=True)

        # Create multiple mock files
        workspace_id = UUID(test_headers["askui-workspace"])
        for i in range(5):
            mock_file = File(
                id=f"file_test{i}",
                object="file",
                created_at=datetime.fromtimestamp(1234567890 + i, tz=timezone.utc),
                filename=f"test{i}.txt",
                size=32,
                media_type="text/plain",
                workspace_id=workspace_id,
            )
            (files_dir / f"file_test{i}.json").write_text(mock_file.model_dump_json())
            # Add file to database
            self._add_file_to_db(mock_file, test_db_session)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(test_db_session, workspace_path)

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service

        try:
            with TestClient(app) as client:
                response = client.get("/v1/files?limit=2", headers=test_headers)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data["data"]) == 2
                assert data["has_more"] is True
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_upload_file_success(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test successful file upload."""
        file_content = b"test file content"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}

        response = test_client.post("/v1/files", files=files, headers=test_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["object"] == "file"
        assert data["filename"] == "test.txt"
        assert data["size"] == len(file_content)
        assert data["media_type"] == "text/plain"
        assert "id" in data
        assert "created_at" in data

    def test_upload_file_without_filename(
        self, test_headers: dict[str, str], test_db_session: Session
    ) -> None:
        """Test file upload with simple filename."""
        file_content = b"test file content"
        # Test with a simple filename
        files = {"file": ("test", io.BytesIO(file_content), "text/plain")}

        # Create a test app with overridden dependencies
        from .conftest import create_test_app_with_overrides

        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        test_app = create_test_app_with_overrides(test_db_session, workspace_path)

        with TestClient(test_app) as client:
            response = client.post("/v1/files", files=files, headers=test_headers)

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["object"] == "file"
            # Should use the provided filename
            assert data["filename"] == "test"
            assert data["size"] == len(file_content)
            assert data["media_type"] == "text/plain"

    def test_upload_file_large_size(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test file upload with file exceeding size limit."""
        # Create a file larger than 20MB
        large_content = b"x" * (21 * 1024 * 1024)
        files = {"file": ("large.txt", io.BytesIO(large_content), "text/plain")}

        response = test_client.post("/v1/files", files=files, headers=test_headers)

        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        data = response.json()
        assert "detail" in data

    def test_retrieve_file_success(
        self, test_headers: dict[str, str], test_db_session: Session
    ) -> None:
        """Test successful file retrieval."""
        # Create a mock file in the temporary workspace
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        files_dir = workspace_path / "files"
        files_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock file
        workspace_id = UUID(test_headers["askui-workspace"])
        mock_file = File(
            id="file_test123",
            object="file",
            created_at=datetime.fromtimestamp(1234567890, tz=timezone.utc),
            filename="test.txt",
            size=32,
            media_type="text/plain",
            workspace_id=workspace_id,
        )
        (files_dir / "file_test123.json").write_text(mock_file.model_dump_json())

        # Add file to database
        self._add_file_to_db(mock_file, test_db_session)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(test_db_session, workspace_path)

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service

        try:
            with TestClient(app) as client:
                response = client.get("/v1/files/file_test123", headers=test_headers)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["id"] == "file_test123"
                assert data["filename"] == "test.txt"
                assert data["size"] == 32
                assert data["media_type"] == "text/plain"
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_retrieve_file_not_found(
        self, test_headers: dict[str, str], test_db_session: Session
    ) -> None:
        """Test file retrieval when file doesn't exist."""
        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service

        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(test_db_session, workspace_path)

        def override_set_env_from_headers() -> None:
            # No-op for testing
            pass

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service
        app.dependency_overrides[SetEnvFromHeadersDep] = override_set_env_from_headers

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/v1/files/file_nonexistent123", headers=test_headers
                )

                assert response.status_code == status.HTTP_404_NOT_FOUND
                data = response.json()
                assert "detail" in data
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_download_file_success(
        self, test_headers: dict[str, str], test_db_session: Session
    ) -> None:
        """Test successful file download."""
        # Create a mock file in the temporary workspace
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        files_dir = workspace_path / "files"
        workspace_id = UUID(test_headers["askui-workspace"])
        static_dir = workspace_path / "workspaces" / str(workspace_id) / "static"
        files_dir.mkdir(parents=True, exist_ok=True)
        static_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock file
        mock_file = File(
            id="file_test123",
            object="file",
            created_at=datetime.fromtimestamp(1234567890, tz=timezone.utc),
            filename="test.txt",
            size=32,
            media_type="text/plain",
            workspace_id=workspace_id,
        )
        (files_dir / "file_test123.json").write_text(mock_file.model_dump_json())

        # Create the actual file content
        file_content = b"test file content"
        (static_dir / "file_test123.txt").write_bytes(file_content)

        # Add file to database
        self._add_file_to_db(mock_file, test_db_session)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(test_db_session, workspace_path)

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/v1/files/file_test123/content", headers=test_headers
                )

                assert response.status_code == status.HTTP_200_OK
                assert response.content == file_content
                assert response.headers["content-type"].startswith("text/plain")
                assert (
                    response.headers["content-disposition"]
                    == 'attachment; filename="test.txt"'
                )
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_download_file_not_found(
        self, test_headers: dict[str, str], test_db_session: Session
    ) -> None:
        """Test file download when file doesn't exist."""
        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service

        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(test_db_session, workspace_path)

        def override_set_env_from_headers() -> None:
            # No-op for testing
            pass

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service
        app.dependency_overrides[SetEnvFromHeadersDep] = override_set_env_from_headers

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/v1/files/file_nonexistent123/content", headers=test_headers
                )

                assert response.status_code == status.HTTP_404_NOT_FOUND
                data = response.json()
                assert "detail" in data
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_delete_file_success(
        self, test_headers: dict[str, str], test_db_session: Session
    ) -> None:
        """Test successful file deletion."""
        # Create a mock file in the temporary workspace
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        files_dir = workspace_path / "files"
        workspace_id = UUID(test_headers["askui-workspace"])
        static_dir = workspace_path / "workspaces" / str(workspace_id) / "static"
        files_dir.mkdir(parents=True, exist_ok=True)
        static_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock file
        mock_file = File(
            id="file_test123",
            object="file",
            created_at=datetime.fromtimestamp(1234567890, tz=timezone.utc),
            filename="test.txt",
            size=32,
            media_type="text/plain",
            workspace_id=workspace_id,
        )
        (files_dir / "file_test123.json").write_text(mock_file.model_dump_json())

        # Create the actual file content
        file_content = b"test file content"
        (static_dir / "file_test123.txt").write_bytes(file_content)

        # Add file to database
        self._add_file_to_db(mock_file, test_db_session)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service

        def override_workspace_dir() -> Path:
            return workspace_path

        file_service_override = FileService(test_db_session, workspace_path)

        def override_file_service() -> FileService:
            return file_service_override

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service

        try:
            with TestClient(app) as client:
                response = client.delete("/v1/files/file_test123", headers=test_headers)

                assert response.status_code == status.HTTP_204_NO_CONTENT

                # Verify static file is deleted (JSON files are no longer used)
                assert not (static_dir / "file_test123.txt").exists()

                # Verify file is deleted from database
                with pytest.raises(NotFoundError):
                    file_service_override.retrieve(workspace_id, FileId("file_test123"))
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_delete_file_not_found(
        self, test_headers: dict[str, str], test_db_session: Session
    ) -> None:
        """Test file deletion when file doesn't exist."""
        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service

        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(test_db_session, workspace_path)

        def override_set_env_from_headers() -> None:
            # No-op for testing
            pass

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service
        app.dependency_overrides[SetEnvFromHeadersDep] = override_set_env_from_headers

        try:
            with TestClient(app) as client:
                response = client.delete(
                    "/v1/files/file_nonexistent123", headers=test_headers
                )

                assert response.status_code == status.HTTP_404_NOT_FOUND
                data = response.json()
                assert "detail" in data
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_upload_different_file_types(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test uploading different file types."""
        # Test JSON file
        json_content = b'{"key": "value"}'
        json_files = {
            "file": ("data.json", io.BytesIO(json_content), "application/json")
        }

        response = test_client.post("/v1/files", files=json_files, headers=test_headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["media_type"] == "application/json"
        assert data["filename"] == "data.json"

        # Test PDF file
        pdf_content = b"%PDF-1.4\ntest pdf content"
        pdf_files = {
            "file": ("document.pdf", io.BytesIO(pdf_content), "application/pdf")
        }

        response = test_client.post("/v1/files", files=pdf_files, headers=test_headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["media_type"] == "application/pdf"
        assert data["filename"] == "document.pdf"

    def test_upload_file_without_content_type(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test file upload without content type."""
        file_content = b"test file content"
        files = {"file": ("test.txt", io.BytesIO(file_content), None)}

        response = test_client.post("/v1/files", files=files, headers=test_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        # FastAPI might infer content type from filename, so we just check it's not None
        assert data["media_type"] is not None
        assert data["media_type"] != ""

    def test_list_files_with_filtering(
        self, test_headers: dict[str, str], test_db_session: Session
    ) -> None:
        """Test listing files with filtering parameters."""
        # Create multiple mock files in the temporary workspace
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        files_dir = workspace_path / "files"
        files_dir.mkdir(parents=True, exist_ok=True)

        # Create multiple mock files with different timestamps
        workspace_id = UUID(test_headers["askui-workspace"])
        for i in range(3):
            mock_file = File(
                id=f"file_test{i}",
                object="file",
                created_at=datetime.fromtimestamp(1234567890 + i, tz=timezone.utc),
                filename=f"test{i}.txt",
                size=32,
                media_type="text/plain",
                workspace_id=workspace_id,
            )
            (files_dir / f"file_test{i}.json").write_text(mock_file.model_dump_json())
            # Add file to database
            self._add_file_to_db(mock_file, test_db_session)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(test_db_session, workspace_path)

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service

        try:
            with TestClient(app) as client:
                # Test with after parameter
                response = client.get(
                    "/v1/files?after=file_test0", headers=test_headers
                )
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                # In descending lexicographic order, file_test0 is the last file,
                # so there are no files "after" it
                assert len(data["data"]) == 0

                # Test with before parameter
                response = client.get(
                    "/v1/files?before=file_test2", headers=test_headers
                )
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                # In descending lexicographic order, file_test2 is the first file,
                # so there are no files "before" it
                assert len(data["data"]) == 0
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()
