"""Integration tests for the messages API endpoints."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

from fastapi import status
from fastapi.testclient import TestClient

from askui.chat.api.messages.models import Message
from askui.chat.api.messages.service import MessageService
from askui.chat.api.threads.models import Thread
from askui.chat.api.threads.service import ThreadService


class TestMessagesAPI:
    """Test suite for the messages API endpoints."""

    def test_list_messages_empty(self, test_headers: dict[str, str]) -> None:
        """Test listing messages when no messages exist."""
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
        from askui.chat.api.messages.dependencies import get_message_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_message_service() -> MessageService:
            return MessageService(workspace_path)

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_message_service] = override_message_service

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/v1/threads/thread_test123/messages", headers=test_headers
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["object"] == "list"
                assert data["data"] == []
                assert data["has_more"] is False
        finally:
            app.dependency_overrides.clear()

    def test_list_messages_with_messages(self, test_headers: dict[str, str]) -> None:
        """Test listing messages when messages exist."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)
        messages_dir = workspace_path / "messages" / "thread_test123"
        messages_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock thread
        mock_thread = Thread(
            id="thread_test123",
            object="thread",
            created_at=1234567890,
            name="Test Thread",
        )
        (threads_dir / "thread_test123.json").write_text(mock_thread.model_dump_json())

        # Create a mock message
        mock_message = Message(
            id="msg_test123",
            object="thread.message",
            created_at=1234567890,
            thread_id="thread_test123",
            role="user",
            content="Hello, this is a test message",
            metadata={"key": "value"},
        )
        (messages_dir / "msg_test123.json").write_text(mock_message.model_dump_json())

        from askui.chat.api.app import app
        from askui.chat.api.messages.dependencies import get_message_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_message_service() -> MessageService:
            return MessageService(workspace_path)

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_message_service] = override_message_service

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/v1/threads/thread_test123/messages", headers=test_headers
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["object"] == "list"
                assert len(data["data"]) == 1
                assert data["data"][0]["id"] == "msg_test123"
                assert data["data"][0]["content"] == "Hello, this is a test message"
                assert data["data"][0]["role"] == "user"
        finally:
            app.dependency_overrides.clear()

    def test_list_messages_with_pagination(self, test_headers: dict[str, str]) -> None:
        """Test listing messages with pagination parameters."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)
        messages_dir = workspace_path / "messages" / "thread_test123"
        messages_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock thread
        mock_thread = Thread(
            id="thread_test123",
            object="thread",
            created_at=1234567890,
            name="Test Thread",
        )
        (threads_dir / "thread_test123.json").write_text(mock_thread.model_dump_json())

        # Create multiple mock messages
        for i in range(5):
            mock_message = Message(
                id=f"msg_test{i}",
                object="thread.message",
                created_at=1234567890 + i,
                thread_id="thread_test123",
                role="user" if i % 2 == 0 else "assistant",
                content=f"Test message {i}",
            )
            (messages_dir / f"msg_test{i}.json").write_text(
                mock_message.model_dump_json()
            )

        from askui.chat.api.app import app
        from askui.chat.api.messages.dependencies import get_message_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_message_service() -> MessageService:
            return MessageService(workspace_path)

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_message_service] = override_message_service

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/v1/threads/thread_test123/messages?limit=3", headers=test_headers
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data["data"]) == 3
                assert data["has_more"] is True
        finally:
            app.dependency_overrides.clear()

    def test_create_message(self, test_headers: dict[str, str]) -> None:
        """Test creating a new message."""
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
        from askui.chat.api.messages.dependencies import get_message_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_message_service() -> MessageService:
            return MessageService(workspace_path)

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_message_service] = override_message_service

        try:
            with TestClient(app) as client:
                message_data = {
                    "role": "user",
                    "content": "Hello, this is a new message",
                    "metadata": {"key": "value", "number": 42},
                }
                response = client.post(
                    "/v1/threads/thread_test123/messages",
                    json=message_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["role"] == "user"
                assert data["content"] == "Hello, this is a new message"

                assert data["object"] == "thread.message"
                assert data["thread_id"] == "thread_test123"
                assert "id" in data
                assert "created_at" in data
        finally:
            app.dependency_overrides.clear()

    def test_create_message_minimal(self, test_headers: dict[str, str]) -> None:
        """Test creating a message with minimal data."""
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
        from askui.chat.api.messages.dependencies import get_message_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_message_service() -> MessageService:
            return MessageService(workspace_path)

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_message_service] = override_message_service

        try:
            with TestClient(app) as client:
                message_data = {"role": "user", "content": "Minimal message"}
                response = client.post(
                    "/v1/threads/thread_test123/messages",
                    json=message_data,
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["object"] == "thread.message"
                assert data["role"] == "user"
                assert data["content"] == "Minimal message"

        finally:
            app.dependency_overrides.clear()

    def test_create_message_invalid_thread(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test creating a message in a non-existent thread."""
        message_data = {"role": "user", "content": "Test message"}
        response = test_client.post(
            "/v1/threads/thread_nonexistent123/messages",
            json=message_data,
            headers=test_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_message(self, test_headers: dict[str, str]) -> None:
        """Test retrieving an existing message."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)
        messages_dir = workspace_path / "messages" / "thread_test123"
        messages_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock thread
        mock_thread = Thread(
            id="thread_test123",
            object="thread",
            created_at=1234567890,
            name="Test Thread",
        )
        (threads_dir / "thread_test123.json").write_text(mock_thread.model_dump_json())

        # Create a mock message
        mock_message = Message(
            id="msg_test123",
            object="thread.message",
            created_at=1234567890,
            thread_id="thread_test123",
            role="user",
            content="Test message content",
            metadata={"key": "value"},
        )
        (messages_dir / "msg_test123.json").write_text(mock_message.model_dump_json())

        from askui.chat.api.app import app
        from askui.chat.api.messages.dependencies import get_message_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_message_service() -> MessageService:
            return MessageService(workspace_path)

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_message_service] = override_message_service

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/v1/threads/thread_test123/messages/msg_test123",
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["id"] == "msg_test123"
                assert data["content"] == "Test message content"
                assert data["role"] == "user"
                assert data["thread_id"] == "thread_test123"
        finally:
            app.dependency_overrides.clear()

    def test_retrieve_message_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test retrieving a non-existent message."""
        response = test_client.get(
            "/v1/threads/thread_test123/messages/msg_nonexistent123",
            headers=test_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

    def test_delete_message(self, test_headers: dict[str, str]) -> None:
        """Test deleting an existing message."""
        temp_dir = tempfile.mkdtemp()
        workspace_path = Path(temp_dir)
        threads_dir = workspace_path / "threads"
        threads_dir.mkdir(parents=True, exist_ok=True)
        messages_dir = workspace_path / "messages" / "thread_test123"
        messages_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock thread
        mock_thread = Thread(
            id="thread_test123",
            object="thread",
            created_at=1234567890,
            name="Test Thread",
        )
        (threads_dir / "thread_test123.json").write_text(mock_thread.model_dump_json())

        # Create a mock message
        mock_message = Message(
            id="msg_test123",
            object="thread.message",
            created_at=1234567890,
            thread_id="thread_test123",
            role="user",
            content="Test message to delete",
        )
        (messages_dir / "msg_test123.json").write_text(mock_message.model_dump_json())

        from askui.chat.api.app import app
        from askui.chat.api.messages.dependencies import get_message_service
        from askui.chat.api.threads.dependencies import get_thread_service

        def override_thread_service() -> ThreadService:
            from askui.chat.api.threads.service import ThreadService

            mock_message_service = Mock()
            mock_run_service = Mock()
            return ThreadService(workspace_path, mock_message_service, mock_run_service)

        def override_message_service() -> MessageService:
            return MessageService(workspace_path)

        app.dependency_overrides[get_thread_service] = override_thread_service
        app.dependency_overrides[get_message_service] = override_message_service

        try:
            with TestClient(app) as client:
                response = client.delete(
                    "/v1/threads/thread_test123/messages/msg_test123",
                    headers=test_headers,
                )

                assert response.status_code == status.HTTP_204_NO_CONTENT
                assert response.content == b""
        finally:
            app.dependency_overrides.clear()

    def test_delete_message_not_found(
        self, test_client: TestClient, test_headers: dict[str, str]
    ) -> None:
        """Test deleting a non-existent message."""
        response = test_client.delete(
            "/v1/threads/thread_test123/messages/msg_nonexistent123",
            headers=test_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
