"""Integration tests for the runs API endpoints."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

from fastapi import status
from fastapi.testclient import TestClient

from askui.chat.api.assistants.service import AssistantService
from askui.chat.api.runs.models import Run
from askui.chat.api.runs.service import RunService
from askui.chat.api.threads.models import Thread
from askui.chat.api.threads.service import ThreadService


def create_mock_mcp_client_manager_manager() -> Mock:
    """Create a properly configured mock MCP config service."""
    mock_service = Mock()
    # Configure mock to return proper data structure
    mock_service.get_mcp_client_manager.return_value = None
    return mock_service


class TestRunsAPI:
    """Test suite for the runs API endpoints."""

    def test_list_runs_empty(self, test_headers: dict[str, str]) -> None:
        """Test listing runs when no runs exist."""
        # First create a thread
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
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_assistant_service = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            mock_message_service = Mock()
            mock_message_translator = Mock()
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/v1/threads/thread_test123/runs", headers=test_headers
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["object"] == "list"
                assert data["data"] == []
                assert data["has_more"] is False
        finally:
            app.dependency_overrides.clear()

    def test_list_runs_with_runs(self, test_headers: dict[str, str]) -> None:
        """Test listing runs when runs exist."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)
        runs_dir = workspace_path / "runs" / "thread_test123"
        runs_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock thread
        mock_thread = Thread(
            id="thread_test123",
            object="thread",
            created_at=1234567890,
            name="Test Thread",
        )
        (threads_dir / "thread_test123.json").write_text(mock_thread.model_dump_json())

        # Create a mock run
        mock_run = Run(
            id="run_test123",
            object="thread.run",
            created_at=1234567890,
            thread_id="thread_test123",
            assistant_id="asst_test123",
            expires_at=1755846718,  # 10 minutes later
            started_at=1234567890,
            completed_at=1234567900,
        )
        (runs_dir / "run_test123.json").write_text(mock_run.model_dump_json())

        from askui.chat.api.app import app
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_assistant_service = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            mock_message_service = Mock()
            mock_message_translator = Mock()
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/v1/threads/thread_test123/runs", headers=test_headers
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["object"] == "list"
                assert len(data["data"]) == 1
                assert data["data"][0]["id"] == "run_test123"
                assert data["data"][0]["status"] == "completed"
                assert data["data"][0]["assistant_id"] == "asst_test123"
        finally:
            app.dependency_overrides.clear()

    def test_list_runs_with_pagination(self, test_headers: dict[str, str]) -> None:
        """Test listing runs with pagination parameters."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)
        runs_dir = workspace_path / "runs" / "thread_test123"
        runs_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock thread
        mock_thread = Thread(
            id="thread_test123",
            object="thread",
            created_at=1234567890,
            name="Test Thread",
        )
        (threads_dir / "thread_test123.json").write_text(mock_thread.model_dump_json())

        # Create multiple mock runs
        for i in range(5):
            mock_run = Run(
                id=f"run_test{i}",
                object="thread.run",
                created_at=1234567890 + i,
                thread_id="thread_test123",
                assistant_id=f"asst_test{i}",
                expires_at=1234567890 + i + 600,  # 10 minutes later
            )
            (runs_dir / f"run_test{i}.json").write_text(mock_run.model_dump_json())

        from askui.chat.api.app import app
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_assistant_service = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            mock_message_service = Mock()
            mock_message_translator = Mock()
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/v1/threads/thread_test123/runs?limit=3", headers=test_headers
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data["data"]) == 3
                assert data["has_more"] is True
        finally:
            app.dependency_overrides.clear()

    def test_create_run(self, test_headers: dict[str, str]) -> None:
        """Test creating a new run."""
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
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_assistant_service = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            mock_message_service = Mock()
            mock_message_translator = Mock()
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service

        try:
            with TestClient(app) as client:
                run_data = {
                    "assistant_id": "asst_test123",
                    "stream": False,
                    "metadata": {"key": "value", "number": 42},
                }
                response = client.post(
                    "/v1/threads/thread_test123/runs",
                    json=run_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["assistant_id"] == "asst_test123"
                assert data["thread_id"] == "thread_test123"
                assert data["object"] == "thread.run"
                assert "id" in data
                assert "created_at" in data
        finally:
            app.dependency_overrides.clear()

    def test_create_run_minimal(self, test_headers: dict[str, str]) -> None:
        """Test creating a run with minimal data."""
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
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_assistant_service = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            mock_message_service = Mock()
            mock_message_translator = Mock()
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service

        try:
            with TestClient(app) as client:
                run_data = {"assistant_id": "asst_test123"}
                response = client.post(
                    "/v1/threads/thread_test123/runs",
                    json=run_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["object"] == "thread.run"
                assert data["assistant_id"] == "asst_test123"
                # stream field is not returned in the response
        finally:
            app.dependency_overrides.clear()

    def test_create_run_streaming(self, test_headers: dict[str, str]) -> None:
        """Test creating a streaming run."""
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
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_assistant_service = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            mock_message_service = Mock()
            mock_message_translator = Mock()
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service

        try:
            with TestClient(app) as client:
                run_data = {
                    "assistant_id": "asst_test123",
                    "stream": True,
                }
                response = client.post(
                    "/v1/threads/thread_test123/runs",
                    json=run_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_201_CREATED
                assert "text/event-stream" in response.headers["content-type"]
        finally:
            app.dependency_overrides.clear()

    def test_create_thread_and_run(self, test_headers: dict[str, str]) -> None:
        """Test creating a thread and run in one request."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        from askui.chat.api.app import app
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_assistant_service = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            mock_message_service = Mock()
            mock_message_translator = Mock()
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service

        try:
            with TestClient(app) as client:
                thread_and_run_data = {
                    "assistant_id": "asst_test123",
                    "stream": False,
                    "thread": {
                        "name": "Test Thread",
                        "messages": [
                            {"role": "user", "content": "Hello, how are you?"}
                        ],
                    },
                    "metadata": {"key": "value", "number": 42},
                }
                response = client.post(
                    "/v1/runs",
                    json=thread_and_run_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["assistant_id"] == "asst_test123"
                assert data["object"] == "thread.run"
                assert "id" in data
                assert "created_at" in data
                assert "thread_id" in data
        finally:
            app.dependency_overrides.clear()

    def test_create_thread_and_run_minimal(self, test_headers: dict[str, str]) -> None:
        """Test creating a thread and run with minimal data."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        from askui.chat.api.app import app
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_assistant_service = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            mock_message_service = Mock()
            mock_message_translator = Mock()
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service

        try:
            with TestClient(app) as client:
                thread_and_run_data = {"assistant_id": "asst_test123", "thread": {}}
                response = client.post(
                    "/v1/runs",
                    json=thread_and_run_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["object"] == "thread.run"
                assert data["assistant_id"] == "asst_test123"
                assert "id" in data
                assert "thread_id" in data
        finally:
            app.dependency_overrides.clear()

    def test_create_thread_and_run_streaming(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test creating a streaming thread and run."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        from askui.chat.api.app import app
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_assistant_service = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            mock_message_service = Mock()
            mock_message_translator = Mock()
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service

        try:
            with TestClient(app) as client:
                thread_and_run_data = {
                    "assistant_id": "asst_test123",
                    "stream": True,
                    "thread": {
                        "name": "Streaming Thread",
                        "messages": [{"role": "user", "content": "Tell me a story"}],
                    },
                }
                response = client.post(
                    "/v1/runs",
                    json=thread_and_run_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_201_CREATED
                assert "text/event-stream" in response.headers["content-type"]
        finally:
            app.dependency_overrides.clear()

    def test_create_thread_and_run_with_messages(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test creating a thread and run with initial messages."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        from askui.chat.api.app import app
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_assistant_service = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            mock_message_service = Mock()
            mock_message_translator = Mock()
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service

        try:
            with TestClient(app) as client:
                thread_and_run_data = {
                    "assistant_id": "asst_test123",
                    "stream": False,
                    "thread": {
                        "name": "Conversation Thread",
                        "messages": [
                            {"role": "user", "content": "What is the weather like?"},
                            {
                                "role": "assistant",
                                "content": (
                                    "I don't have access to real-time weather data."
                                ),
                            },
                            {"role": "user", "content": "Can you help me plan my day?"},
                        ],
                    },
                }
                response = client.post(
                    "/v1/runs",
                    json=thread_and_run_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["assistant_id"] == "asst_test123"
                assert data["object"] == "thread.run"
                assert "id" in data
                assert "thread_id" in data
        finally:
            app.dependency_overrides.clear()

    def test_create_thread_and_run_validation_error(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test creating thread and run with invalid data."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        from askui.chat.api.app import app
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_assistant_service = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            mock_message_service = Mock()
            mock_message_translator = Mock()
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service

        try:
            with TestClient(app) as client:
                # Missing required assistant_id
                invalid_data = {"thread": {}}  # type: ignore[var-annotated]
                response = client.post(
                    "/v1/runs",
                    json=invalid_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
                data = response.json()
                assert "detail" in data
        finally:
            app.dependency_overrides.clear()

    def test_create_thread_and_run_empty_thread(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test creating thread and run with completely empty thread object."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)

        from askui.chat.api.app import app
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_assistant_service = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            mock_message_service = Mock()
            mock_message_translator = Mock()
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service

        try:
            with TestClient(app) as client:
                thread_and_run_data = {"assistant_id": "asst_test123", "thread": {}}
                response = client.post(
                    "/v1/runs",
                    json=thread_and_run_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["assistant_id"] == "asst_test123"
                assert "thread_id" in data
        finally:
            app.dependency_overrides.clear()

    def test_create_run_invalid_thread(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test creating a run in a non-existent thread."""
        run_data = {"assistant_id": "asst_test123"}
        response = test_client.post(
            "/v1/threads/thread_nonexistent123/runs",
            json=run_data,
            headers=test_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_run(self, test_headers: dict[str, str]) -> None:
        """Test retrieving an existing run."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)
        runs_dir = workspace_path / "runs" / "thread_test123"
        runs_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock thread
        mock_thread = Thread(
            id="thread_test123",
            object="thread",
            created_at=1234567890,
            name="Test Thread",
        )
        (threads_dir / "thread_test123.json").write_text(mock_thread.model_dump_json())

        # Create a mock run
        mock_run = Run(
            id="run_test123",
            object="thread.run",
            created_at=1234567890,
            thread_id="thread_test123",
            assistant_id="asst_test123",
            expires_at=1755846718,  # 10 minutes later
            started_at=1234567890,
            completed_at=1234567900,
        )
        (runs_dir / "run_test123.json").write_text(mock_run.model_dump_json())

        from askui.chat.api.app import app
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_assistant_service = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            mock_message_service = Mock()
            mock_message_translator = Mock()
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/v1/threads/thread_test123/runs/run_test123", headers=test_headers
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["id"] == "run_test123"
                assert data["status"] == "completed"
                assert data["assistant_id"] == "asst_test123"
                assert data["thread_id"] == "thread_test123"
        finally:
            app.dependency_overrides.clear()

    def test_retrieve_run_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test retrieving a non-existent run."""
        response = test_client.get(
            "/v1/threads/thread_test123/runs/run_nonexistent123", headers=test_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

    def test_cancel_run(self, test_headers: dict[str, str]) -> None:
        """Test canceling an existing run."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)
        runs_dir = workspace_path / "runs" / "thread_test123"
        runs_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock thread
        mock_thread = Thread(
            id="thread_test123",
            object="thread",
            created_at=1234567890,
            name="Test Thread",
        )
        (threads_dir / "thread_test123.json").write_text(mock_thread.model_dump_json())

        # Create a mock run
        import time

        current_time = int(time.time())
        mock_run = Run(
            id="run_test123",
            object="thread.run",
            created_at=current_time,
            thread_id="thread_test123",
            assistant_id="asst_test123",
            expires_at=current_time + 600,  # 10 minutes later
        )
        (runs_dir / "run_test123.json").write_text(mock_run.model_dump_json())

        from askui.chat.api.app import app
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_assistant_service = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            mock_message_service = Mock()
            mock_message_translator = Mock()
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service

        try:
            with TestClient(app) as client:
                response = client.post(
                    "/v1/threads/thread_test123/runs/run_test123/cancel",
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["id"] == "run_test123"
                # The cancel operation sets tried_cancelling_at, making status
                # "cancelling"
                assert data["status"] == "cancelling"
        finally:
            app.dependency_overrides.clear()

    def test_cancel_run_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test canceling a non-existent run."""
        response = test_client.post(
            "/v1/threads/thread_test123/runs/run_nonexistent123/cancel",
            headers=test_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_run_with_custom_assistant(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test creating a run with a custom assistant."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)
        assistants_dir = workspace_path / "assistants"
        assistants_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock thread
        mock_thread = Thread(
            id="thread_test123",
            object="thread",
            created_at=1234567890,
            name="Test Thread",
        )
        (threads_dir / "thread_test123.json").write_text(mock_thread.model_dump_json())

        # Create a mock custom assistant
        from askui.chat.api.assistants.models import Assistant

        mock_assistant = Assistant(
            id="asst_custom123",
            object="assistant",
            created_at=1234567890,
            name="Custom Assistant",
            tools=["tool1", "tool2"],
            system="You are a custom assistant.",
        )
        (assistants_dir / "asst_custom123.json").write_text(
            mock_assistant.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_message_service = Mock()
            mock_message_translator = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            from askui.chat.api.assistants.service import AssistantService

            return RunService(
                base_dir=workspace_path,
                assistant_service=AssistantService(workspace_path),
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        def override_assistant_service() -> AssistantService:
            from askui.chat.api.assistants.service import AssistantService

            return AssistantService(workspace_path)

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service
        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                response = client.post(
                    "/v1/threads/thread_test123/runs",
                    headers=test_headers,
                    json={"assistant_id": "asst_custom123"},
                )

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["assistant_id"] == "asst_custom123"
                assert data["thread_id"] == "thread_test123"
                assert data["status"] == "queued"
                assert "id" in data
                assert "created_at" in data
        finally:
            app.dependency_overrides.clear()

    def test_create_run_with_custom_assistant_empty_tools(
        self, test_headers: dict[str, str]
    ) -> None:
        """Test creating a run with a custom assistant that has empty tools."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)
        assistants_dir = workspace_path / "assistants"
        assistants_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock thread
        mock_thread = Thread(
            id="thread_test123",
            object="thread",
            created_at=1234567890,
            name="Test Thread",
        )
        (threads_dir / "thread_test123.json").write_text(mock_thread.model_dump_json())

        # Create a mock custom assistant with empty tools
        from askui.chat.api.assistants.models import Assistant

        mock_assistant = Assistant(
            id="asst_customempty123",
            object="assistant",
            created_at=1234567890,
            name="Empty Tools Assistant",
            tools=[],
            system="You are a assistant with no tools.",
        )
        (assistants_dir / "asst_customempty123.json").write_text(
            mock_assistant.model_dump_json()
        )

        from askui.chat.api.app import app
        from askui.chat.api.assistants.dependencies import get_assistant_service
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            mock_message_service = Mock()
            mock_message_translator = Mock()
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            from askui.chat.api.assistants.service import AssistantService

            return RunService(
                base_dir=workspace_path,
                assistant_service=AssistantService(workspace_path),
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                message_service=mock_message_service,
                message_translator=mock_message_translator,
            )

        def override_assistant_service() -> AssistantService:
            from askui.chat.api.assistants.service import AssistantService

            return AssistantService(workspace_path)

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service
        app.dependency_overrides[get_assistant_service] = override_assistant_service

        try:
            with TestClient(app) as client:
                response = client.post(
                    "/v1/threads/thread_test123/runs",
                    headers=test_headers,
                    json={"assistant_id": "asst_customempty123"},
                )

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["assistant_id"] == "asst_customempty123"
                assert data["thread_id"] == "thread_test123"
                assert data["status"] == "queued"
                assert "id" in data
                assert "created_at" in data
        finally:
            app.dependency_overrides.clear()
