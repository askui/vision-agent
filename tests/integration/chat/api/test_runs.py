"""Integration tests for the runs API endpoints."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock
from uuid import UUID

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from askui.chat.api.assistants.models import Assistant
from askui.chat.api.assistants.orms import AssistantOrm
from askui.chat.api.assistants.service import AssistantService
from askui.chat.api.models import WorkspaceId
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

    def _create_test_assistant(
        self,
        assistant_id: str,
        workspace_id: WorkspaceId | None = None,
        name: str = "Test Assistant",
        description: str = "A test assistant",
        avatar: str | None = None,
        created_at: datetime | None = None,
        tools: list[str] | None = None,
        system: str | None = None,
    ) -> Assistant:
        """Create a test assistant model."""
        if created_at is None:
            created_at = datetime.fromtimestamp(1234567890, tz=timezone.utc)
        if tools is None:
            tools = []
        return Assistant(
            id=assistant_id,
            object="assistant",
            created_at=created_at,
            name=name,
            description=description,
            avatar=avatar,
            workspace_id=workspace_id,
            tools=tools,
            system=system,
        )

    def _add_assistant_to_db(
        self, assistant: Assistant, test_db_session: Session
    ) -> None:
        """Add an assistant to the test database."""
        assistant_orm = AssistantOrm.from_model(assistant)
        test_db_session.add(assistant_orm)
        test_db_session.commit()

    def _create_test_workspace(self) -> Path:
        """Create a temporary workspace directory for testing."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)
        return workspace_path

    def _create_test_thread(
        self, workspace_path: Path, thread_id: str = "thread_test123"
    ) -> None:
        """Create a test thread in the workspace."""
        threads_dir = workspace_path / "threads"
        mock_thread = Thread(
            id=thread_id,
            object="thread",
            created_at=1234567890,
            name="Test Thread",
        )
        (threads_dir / f"{thread_id}.json").write_text(mock_thread.model_dump_json())

    def _create_test_run(
        self,
        workspace_path: Path,
        thread_id: str = "thread_test123",
        run_id: str = "run_test123",
    ) -> None:
        """Create a test run in the workspace."""
        runs_dir = workspace_path / "runs" / thread_id
        runs_dir.mkdir(parents=True, exist_ok=True)

        mock_run = Run(
            id=run_id,
            object="thread.run",
            created_at=1234567890,
            thread_id=thread_id,
            assistant_id="asst_test123",
            expires_at=1755846718,  # 10 minutes later
            started_at=1234567890,
            completed_at=1234567900,
        )
        (runs_dir / f"{run_id}.json").write_text(mock_run.model_dump_json())

    def _setup_runs_dependencies(
        self, workspace_path: Path, test_db_session: Session
    ) -> None:
        """Set up dependency overrides for runs and threads services."""
        from askui.chat.api.app import app
        from askui.chat.api.runs.dependencies import get_runs_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_runs_service() -> RunService:
            assistant_service = AssistantService(test_db_session)
            mock_mcp_client_manager_manager = create_mock_mcp_client_manager_manager()
            return RunService(
                base_dir=workspace_path,
                assistant_service=assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                chat_history_manager=Mock(),
                settings=Mock(),
            )

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_runs_service] = override_runs_service

    def _create_multiple_test_runs(
        self, workspace_path: Path, thread_id: str = "thread_test123", count: int = 5
    ) -> None:
        """Create multiple test runs in the workspace."""
        runs_dir = workspace_path / "runs" / thread_id
        runs_dir.mkdir(parents=True, exist_ok=True)

        for i in range(count):
            mock_run = Run(
                id=f"run_test{i}",
                object="thread.run",
                created_at=1234567890 + i,
                thread_id=thread_id,
                assistant_id=f"asst_test{i}",
                expires_at=1234567890 + i + 600,  # 10 minutes later
            )
            (runs_dir / f"run_test{i}.json").write_text(mock_run.model_dump_json())

    def _cleanup_dependencies(self) -> None:
        """Clean up dependency overrides."""
        from askui.chat.api.app import app

        app.dependency_overrides.clear()

    def test_list_runs_empty(
        self,
        test_headers: dict[str, str],
        test_client: TestClient,
        test_db_session: Session,
    ) -> None:
        """Test listing runs when no runs exist."""
        workspace_path = self._create_test_workspace()
        self._create_test_thread(workspace_path)

        self._setup_runs_dependencies(workspace_path, test_db_session)

        try:
            response = test_client.get(
                "/v1/runs?thread=thread_test123", headers=test_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["object"] == "list"
            assert data["data"] == []
            assert data["has_more"] is False
        finally:
            self._cleanup_dependencies()

    def test_list_runs_with_runs(
        self,
        test_headers: dict[str, str],
        test_client: TestClient,
        test_db_session: Session,
    ) -> None:
        """Test listing runs when runs exist."""
        workspace_path = self._create_test_workspace()
        self._create_test_thread(workspace_path)
        self._create_test_run(workspace_path)

        self._setup_runs_dependencies(workspace_path, test_db_session)

        try:
            response = test_client.get(
                "/v1/runs?thread=thread_test123", headers=test_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["object"] == "list"
            assert len(data["data"]) == 1
            assert data["data"][0]["id"] == "run_test123"
            assert data["data"][0]["status"] == "completed"
            assert data["data"][0]["assistant_id"] == "asst_test123"
        finally:
            self._cleanup_dependencies()

    def test_list_runs_with_pagination(
        self,
        test_headers: dict[str, str],
        test_client: TestClient,
        test_db_session: Session,
    ) -> None:
        """Test listing runs with pagination parameters."""
        workspace_path = self._create_test_workspace()
        self._create_test_thread(workspace_path)
        self._create_multiple_test_runs(workspace_path)

        self._setup_runs_dependencies(workspace_path, test_db_session)

        try:
            response = test_client.get(
                "/v1/runs?thread=thread_test123&limit=3", headers=test_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["data"]) == 3
            assert data["has_more"] is True
        finally:
            self._cleanup_dependencies()

    def test_create_run(
        self,
        test_headers: dict[str, str],
        test_client: TestClient,
        test_db_session: Session,
    ) -> None:
        """Test creating a new run."""
        workspace_path = self._create_test_workspace()
        self._create_test_thread(workspace_path)
        self._setup_runs_dependencies(workspace_path, test_db_session)
        self._add_assistant_to_db(
            self._create_test_assistant(assistant_id="asst_test123"), test_db_session
        )

        try:
            run_data = {
                "assistant_id": "asst_test123",
                "stream": False,
                "metadata": {"key": "value", "number": 42},
            }
            response = test_client.post(
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
            self._cleanup_dependencies()

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
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                chat_history_manager=Mock(),
                settings=Mock(),
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
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                chat_history_manager=Mock(),
                settings=Mock(),
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
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                chat_history_manager=Mock(),
                settings=Mock(),
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
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                chat_history_manager=Mock(),
                settings=Mock(),
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
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                chat_history_manager=Mock(),
                settings=Mock(),
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
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                chat_history_manager=Mock(),
                settings=Mock(),
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
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                chat_history_manager=Mock(),
                settings=Mock(),
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
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                chat_history_manager=Mock(),
                settings=Mock(),
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
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                chat_history_manager=Mock(),
                settings=Mock(),
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
            return RunService(
                base_dir=workspace_path,
                assistant_service=mock_assistant_service,
                mcp_client_manager_manager=mock_mcp_client_manager_manager,
                chat_history_manager=Mock(),
                settings=Mock(),
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
        self,
        test_headers: dict[str, str],
        test_db_session: Session,
        test_client: TestClient,
    ) -> None:
        """Test creating a run with a custom assistant."""
        workspace_path = self._create_test_workspace()
        self._create_test_thread(workspace_path)

        # Create a custom assistant in the database
        workspace_id = UUID(test_headers["askui-workspace"])
        custom_assistant = self._create_test_assistant(
            "asst_custom123",
            workspace_id=workspace_id,
            name="Custom Assistant",
            tools=["tool1", "tool2"],
            system="You are a custom assistant.",
        )
        self._add_assistant_to_db(custom_assistant, test_db_session)

        self._setup_runs_dependencies(workspace_path, test_db_session)

        try:
            response = test_client.post(
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
            self._cleanup_dependencies()

    def test_create_run_with_custom_assistant_empty_tools(
        self,
        test_headers: dict[str, str],
        test_db_session: Session,
        test_client: TestClient,
    ) -> None:
        """Test creating a run with a custom assistant that has empty tools."""
        workspace_path = self._create_test_workspace()
        self._create_test_thread(workspace_path)

        # Create a custom assistant with empty tools in the database
        workspace_id = UUID(test_headers["askui-workspace"])
        empty_tools_assistant = self._create_test_assistant(
            "asst_customempty123",
            workspace_id=workspace_id,
            name="Empty Tools Assistant",
            tools=[],
            system="You are a assistant with no tools.",
        )
        self._add_assistant_to_db(empty_tools_assistant, test_db_session)

        self._setup_runs_dependencies(workspace_path, test_db_session)

        try:
            response = test_client.post(
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
            self._cleanup_dependencies()
