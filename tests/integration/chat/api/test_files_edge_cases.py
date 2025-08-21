"""Edge case and error scenario tests for the files API endpoints."""

import io
import tempfile
from pathlib import Path

from fastapi import status
from fastapi.testclient import TestClient


class TestFilesAPIEdgeCases:
    """Test suite for edge cases and error scenarios in the files API."""

    def test_upload_empty_file(self, test_headers: dict[str, str]) -> None:
        """Test uploading an empty file."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service
        from askui.chat.api.files.service import FileService

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(workspace_path)

        def override_set_env_from_headers() -> None:
            # No-op for testing
            pass

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service
        app.dependency_overrides[SetEnvFromHeadersDep] = override_set_env_from_headers

        try:
            with TestClient(app) as client:
                empty_content = b""
                files = {"file": ("empty.txt", io.BytesIO(empty_content), "text/plain")}

                response = client.post("/v1/files", files=files, headers=test_headers)

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["size"] == 0
                assert data["filename"] == "empty.txt"
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_upload_file_with_special_characters_in_filename(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test uploading a file with special characters in the filename."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service
        from askui.chat.api.files.service import FileService

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(workspace_path)

        def override_set_env_from_headers() -> None:
            # No-op for testing
            pass

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service
        app.dependency_overrides[SetEnvFromHeadersDep] = override_set_env_from_headers

        try:
            with TestClient(app) as client:
                file_content = b"test content"
                special_filename = "file with spaces & special chars!@#$%^&*().txt"
                files = {
                    "file": (special_filename, io.BytesIO(file_content), "text/plain")
                }

                response = client.post("/v1/files", files=files, headers=test_headers)

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["filename"] == special_filename
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_upload_file_with_very_long_filename(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test uploading a file with a very long filename."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service
        from askui.chat.api.files.service import FileService

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(workspace_path)

        def override_set_env_from_headers() -> None:
            # No-op for testing
            pass

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service
        app.dependency_overrides[SetEnvFromHeadersDep] = override_set_env_from_headers

        try:
            with TestClient(app) as client:
                file_content = b"test content"
                long_filename = "a" * 255 + ".txt"  # Very long filename
                files = {
                    "file": (long_filename, io.BytesIO(file_content), "text/plain")
                }

                response = client.post("/v1/files", files=files, headers=test_headers)

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["filename"] == long_filename
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_upload_file_with_unknown_mime_type(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test uploading a file with an unknown MIME type."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service
        from askui.chat.api.files.service import FileService

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(workspace_path)

        def override_set_env_from_headers() -> None:
            # No-op for testing
            pass

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service
        app.dependency_overrides[SetEnvFromHeadersDep] = override_set_env_from_headers

        try:
            with TestClient(app) as client:
                file_content = b"test content"
                unknown_mime = "application/unknown-type"
                files = {"file": ("test.xyz", io.BytesIO(file_content), unknown_mime)}

                response = client.post("/v1/files", files=files, headers=test_headers)

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["media_type"] == unknown_mime
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_upload_file_with_binary_content(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test uploading a file with binary content."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service
        from askui.chat.api.files.service import FileService

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(workspace_path)

        def override_set_env_from_headers() -> None:
            # No-op for testing
            pass

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service
        app.dependency_overrides[SetEnvFromHeadersDep] = override_set_env_from_headers

        try:
            with TestClient(app) as client:
                # Create binary content (PNG header)
                binary_content = b"\x89PNG\r\n\x1a\n" + b"x" * 100
                files = {"file": ("test.png", io.BytesIO(binary_content), "image/png")}

                response = client.post("/v1/files", files=files, headers=test_headers)

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["media_type"] == "image/png"
                assert data["size"] == len(binary_content)
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_upload_file_without_workspace_header(
        self, test_client: TestClient
    ) -> None:
        """Test uploading a file without workspace header."""
        file_content = b"test content"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}

        response = test_client.post("/v1/files", files=files)

        # Should fail due to missing workspace header
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upload_file_with_invalid_workspace_header(
        self, test_client: TestClient
    ) -> None:
        """Test uploading a file with an invalid workspace header."""
        file_content = b"test content"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        invalid_headers = {"askui-workspace": "invalid-uuid"}

        response = test_client.post("/v1/files", files=files, headers=invalid_headers)

        # Should fail due to invalid workspace format
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upload_file_with_malformed_file_data(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test uploading with malformed file data."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service
        from askui.chat.api.files.service import FileService

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(workspace_path)

        def override_set_env_from_headers() -> None:
            # No-op for testing
            pass

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service
        app.dependency_overrides[SetEnvFromHeadersDep] = override_set_env_from_headers

        try:
            with TestClient(app) as client:
                # Send request without file data
                response = client.post("/v1/files", headers=test_headers)

                # Should fail due to missing file
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_upload_file_with_corrupted_content(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test uploading a file with corrupted content."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service
        from askui.chat.api.files.service import FileService

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(workspace_path)

        def override_set_env_from_headers() -> None:
            # No-op for testing
            pass

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service
        app.dependency_overrides[SetEnvFromHeadersDep] = override_set_env_from_headers

        try:
            with TestClient(app) as client:
                # Create a file-like object that raises an error when read
                class CorruptedFile:
                    def read(self, size: int) -> bytes:  # noqa: ARG002
                        error_msg = "Simulated corruption"
                        raise IOError(error_msg)

                files = {"file": ("corrupted.txt", CorruptedFile(), "text/plain")}

                response = client.post("/v1/files", files=files, headers=test_headers)  # type: ignore[arg-type]

                # Should fail due to corruption - FastAPI returns 400 for this case
                assert response.status_code == status.HTTP_400_BAD_REQUEST
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_list_files_with_invalid_pagination(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test listing files with invalid pagination parameters."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service
        from askui.chat.api.files.service import FileService

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(workspace_path)

        def override_set_env_from_headers() -> None:
            # No-op for testing
            pass

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service
        app.dependency_overrides[SetEnvFromHeadersDep] = override_set_env_from_headers

        try:
            with TestClient(app) as client:
                # Test with negative limit
                response = client.get("/v1/files?limit=-1", headers=test_headers)
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

                # Test with zero limit
                response = client.get("/v1/files?limit=0", headers=test_headers)
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

                # Test with very large limit
                response = client.get("/v1/files?limit=10000", headers=test_headers)
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_retrieve_file_with_invalid_id_format(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test retrieving a file with an invalid ID format."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service
        from askui.chat.api.files.service import FileService

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(workspace_path)

        def override_set_env_from_headers() -> None:
            # No-op for testing
            pass

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service
        app.dependency_overrides[SetEnvFromHeadersDep] = override_set_env_from_headers

        try:
            with TestClient(app) as client:
                # Test with empty ID - FastAPI returns 200 for this (lists files)
                response = client.get("/v1/files/", headers=test_headers)
                assert response.status_code == status.HTTP_200_OK

                # Test with ID containing invalid characters - should fail validation
                response = client.get("/v1/files/file@#$%", headers=test_headers)
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_delete_file_with_invalid_id_format(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test deleting a file with an invalid ID format."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        # Create a test app with overridden dependencies
        from askui.chat.api.app import app
        from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_workspace_dir
        from askui.chat.api.files.dependencies import get_file_service
        from askui.chat.api.files.service import FileService

        def override_workspace_dir() -> Path:
            return workspace_path

        def override_file_service() -> FileService:
            return FileService(workspace_path)

        def override_set_env_from_headers() -> None:
            # No-op for testing
            pass

        app.dependency_overrides[get_workspace_dir] = override_workspace_dir
        app.dependency_overrides[get_file_service] = override_file_service
        app.dependency_overrides[SetEnvFromHeadersDep] = override_set_env_from_headers

        try:
            with TestClient(app) as client:
                # Test with empty ID - FastAPI returns 405 Method Not Allowed for this
                response = client.delete("/v1/files/", headers=test_headers)
                assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

                # Test with ID containing invalid characters - should fail validation
                response = client.delete("/v1/files/file@#$%", headers=test_headers)
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()
