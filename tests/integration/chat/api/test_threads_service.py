"""Integration tests for the ThreadService with JSON file persistence."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from askui.chat.api.messages.models import MessageCreateParams
from askui.chat.api.messages.service import MessageService
from askui.chat.api.threads.service import ThreadCreateParams, ThreadService


@pytest.fixture
def temp_base_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def message_service(temp_base_dir: Path) -> MessageService:
    """Create a MessageService instance with temporary storage."""
    return MessageService(temp_base_dir)


@pytest.fixture
def thread_service(
    temp_base_dir: Path, message_service: MessageService
) -> ThreadService:
    """Create a ThreadService instance with temporary storage."""
    return ThreadService(temp_base_dir, message_service)


class TestThreadServiceJSONPersistence:
    """Test ThreadService with JSON file persistence."""

    def test_create_thread_creates_directory_structure(
        self, thread_service: ThreadService
    ) -> None:
        """Test that creating a thread creates the proper directory structure."""
        request = ThreadCreateParams(name="Test Thread")

        thread = thread_service.create(request)

        # Check that thread metadata file was created
        thread_file = thread_service._base_dir / "threads" / f"{thread.id}.json"
        assert thread_file.exists()

        # Check that messages directory was created (by creating a message)
        # The ThreadService doesn't create the messages directory until a message is
        # added
        message_request = MessageCreateParams(role="user", content="Test message")
        thread_service._message_service.create(thread.id, message_request)

        thread_messages_dir = thread_service._message_service.get_messages_dir(
            thread.id
        )
        assert thread_messages_dir.exists()

        # Verify thread metadata content
        with thread_file.open("r") as f:
            import json

            data = json.load(f)
            assert data["name"] == "Test Thread"
            assert data["id"] == thread.id

    def test_create_thread_with_messages(self, thread_service: ThreadService) -> None:
        """Test that creating a thread with messages works correctly."""
        messages = [
            MessageCreateParams(role="user", content="Hello"),
            MessageCreateParams(role="assistant", content="Hi there!"),
        ]
        request = ThreadCreateParams(name="Thread with Messages", messages=messages)

        thread = thread_service.create(request)

        # Check that messages were created
        thread_messages_dir = thread_service._message_service.get_messages_dir(
            thread.id
        )
        json_files = list(thread_messages_dir.glob("*.json"))
        assert len(json_files) == 2

        # Verify message content
        for json_file in json_files:
            with json_file.open("r") as f:
                import json

                data = json.load(f)
                assert data["thread_id"] == thread.id
                assert data["role"] in ["user", "assistant"]

    def test_delete_thread_removes_all_files(
        self, thread_service: ThreadService
    ) -> None:
        """Test that deleting a thread removes all associated files."""
        request = ThreadCreateParams(
            name="Thread to Delete",
            messages=[MessageCreateParams(role="user", content="Test message")],
        )
        thread = thread_service.create(request)

        # Verify files exist
        thread_file = thread_service._base_dir / "threads" / f"{thread.id}.json"
        assert thread_file.exists()

        # The thread directory itself doesn't exist, only the messages directory
        messages_dir = thread_service._message_service.get_messages_dir(thread.id)
        assert messages_dir.exists()

        # Delete thread
        thread_service.delete(thread.id)

        # Verify all files were removed
        assert not thread_file.exists()
        assert not messages_dir.exists()
