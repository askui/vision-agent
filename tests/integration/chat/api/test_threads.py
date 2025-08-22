"""Integration tests for the threads API endpoints."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

from fastapi import status
from fastapi.testclient import TestClient

from askui.chat.api.threads.models import Thread
from askui.chat.api.threads.service import ThreadService


class TestThreadsAPI:
    """Test suite for the threads API endpoints."""

    def test_list_threads_empty(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test listing threads when no threads exist."""
        response = test_client.get("/v1/threads", headers=test_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["object"] == "list"
        assert data["data"] == []
        assert data["has_more"] is False

    def test_list_threads_with_threads(self, test_headers: dict[str, str]) -> None:
        """Test listing threads when threads exist."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock thread
        mock_thread = Thread(
            id="thread_test123",
            object="thread",
            created_at=1234567890,
            name="Test Thread",
        )
        (threads_dir / "thread_test123.json").write_text(mock_thread.model_dump_json())

        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        # Mock the dependencies
        mock_message_service = Mock()
        mock_run_service = Mock()

        def override_thread_service() -> ThreadService:
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                response = client.get("/v1/threads", headers=test_headers)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["object"] == "list"
                assert len(data["data"]) == 1
                assert data["data"][0]["id"] == "thread_test123"
                assert data["data"][0]["name"] == "Test Thread"
        finally:
            app.dependency_overrides.clear()

    def test_list_threads_with_pagination(self, test_headers: dict[str, str]) -> None:
        """Test listing threads with pagination parameters."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)

        # Create multiple mock threads
        for i in range(5):
            mock_thread = Thread(
                id=f"thread_test{i}",
                object="thread",
                created_at=1234567890 + i,
                name=f"Test Thread {i}",
            )
            (threads_dir / f"thread_test{i}.json").write_text(
                mock_thread.model_dump_json()
            )

        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        # Mock the dependencies
        mock_message_service = Mock()
        mock_run_service = Mock()

        def override_thread_service() -> ThreadService:
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                response = client.get("/v1/threads?limit=3", headers=test_headers)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data["data"]) == 3
                assert data["has_more"] is True
        finally:
            app.dependency_overrides.clear()

    def test_create_thread(self, test_headers: dict[str, str]) -> None:
        """Test creating a new thread."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        # Mock the dependencies
        mock_message_service = Mock()
        mock_run_service = Mock()

        def override_thread_service() -> ThreadService:
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                thread_data = {
                    "name": "New Test Thread",
                }
                response = client.post(
                    "/v1/threads", json=thread_data, headers=test_headers
                )

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["name"] == "New Test Thread"
                assert data["object"] == "thread"
                assert "id" in data
                assert "created_at" in data
        finally:
            app.dependency_overrides.clear()

    def test_create_thread_minimal(self, test_headers: dict[str, str]) -> None:
        """Test creating a thread with minimal data."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        # Mock the dependencies
        mock_message_service = Mock()
        mock_run_service = Mock()

        def override_thread_service() -> ThreadService:
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                response = client.post("/v1/threads", json={}, headers=test_headers)

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["object"] == "thread"
                assert data["name"] is None
        finally:
            app.dependency_overrides.clear()

    def test_retrieve_thread(self, test_headers: dict[str, str]) -> None:
        """Test retrieving an existing thread."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)

        mock_thread = Thread(
            id="thread_test123",
            object="thread",
            created_at=1234567890,
            name="Test Thread",
        )
        (threads_dir / "thread_test123.json").write_text(mock_thread.model_dump_json())

        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        # Mock the dependencies
        mock_message_service = Mock()
        mock_run_service = Mock()

        def override_thread_service() -> ThreadService:
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/v1/threads/thread_test123", headers=test_headers
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["id"] == "thread_test123"
                assert data["name"] == "Test Thread"
        finally:
            app.dependency_overrides.clear()

    def test_retrieve_thread_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test retrieving a non-existent thread."""
        response = test_client.get(
            "/v1/threads/thread_nonexistent123", headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

    def test_modify_thread(self, test_headers: dict[str, str]) -> None:
        """Test modifying an existing thread."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)

        mock_thread = Thread(
            id="thread_test123",
            object="thread",
            created_at=1234567890,
            name="Original Name",
        )
        (threads_dir / "thread_test123.json").write_text(mock_thread.model_dump_json())

        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        # Mock the dependencies
        mock_message_service = Mock()
        mock_run_service = Mock()

        def override_thread_service() -> ThreadService:
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                modify_data = {
                    "name": "Modified Name",
                }
                response = client.post(
                    "/v1/threads/thread_test123", json=modify_data, headers=test_headers
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["name"] == "Modified Name"
                assert data["id"] == "thread_test123"
                assert data["created_at"] == 1234567890
        finally:
            app.dependency_overrides.clear()

    def test_modify_thread_partial(self, test_headers: dict[str, str]) -> None:
        """Test modifying a thread with partial data."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)

        mock_thread = Thread(
            id="thread_test123",
            object="thread",
            created_at=1234567890,
            name="Original Name",
        )
        (threads_dir / "thread_test123.json").write_text(mock_thread.model_dump_json())

        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        # Mock the dependencies
        mock_message_service = Mock()
        mock_run_service = Mock()

        def override_thread_service() -> ThreadService:
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                modify_data = {"name": "Only Name Modified"}
                response = client.post(
                    "/v1/threads/thread_test123", json=modify_data, headers=test_headers
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["name"] == "Only Name Modified"
        finally:
            app.dependency_overrides.clear()

    def test_modify_thread_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test modifying a non-existent thread."""
        modify_data = {"name": "Modified Name"}
        response = test_client.post(
            "/v1/threads/thread_nonexistent123", json=modify_data, headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_thread(self, test_headers: dict[str, str]) -> None:
        """Test deleting an existing thread."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)

        # Create the directories that the delete operation will try to remove
        messages_dir = workspace_path / "messages" / "thread_test123"
        messages_dir.mkdir(parents=True, exist_ok=True)
        runs_dir = workspace_path / "runs" / "thread_test123"
        runs_dir.mkdir(parents=True, exist_ok=True)

        mock_thread = Thread(
            id="thread_test123",
            object="thread",
            created_at=1234567890,
            name="Test Thread",
        )
        (threads_dir / "thread_test123.json").write_text(mock_thread.model_dump_json())

        from askui.chat.api.app import app
        from askui.chat.api.threads.dependencies import get_thread_service

        # Mock the dependencies with proper return values
        mock_message_service = Mock()
        mock_message_service.get_messages_dir.return_value = messages_dir
        mock_run_service = Mock()
        mock_run_service.get_runs_dir.return_value = runs_dir

        def override_thread_service() -> ThreadService:
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        app.dependency_overrides[get_thread_service] = override_thread_service

        try:
            with TestClient(app) as client:
                response = client.delete(
                    "/v1/threads/thread_test123", headers=test_headers
                )

                assert response.status_code == status.HTTP_204_NO_CONTENT
                assert response.content == b""
        finally:
            app.dependency_overrides.clear()

    def test_delete_thread_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test deleting a non-existent thread."""
        response = test_client.delete(
            "/v1/threads/thread_nonexistent123", headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
