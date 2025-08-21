"""Integration tests for the ThreadService with JSON file persistence."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from askui.chat.api.messages.service import MessageCreateRequest, MessageService
from askui.chat.api.repositories.file_repositories import (
    FileMessageRepository,
    FileThreadRepository,
)
from askui.chat.api.threads.service import ThreadCreateRequest, ThreadService


@pytest.fixture
def temp_base_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def message_service(temp_base_dir: Path) -> MessageService:
    """Create a MessageService instance with temporary storage."""
    repository = FileMessageRepository(temp_base_dir)
    return MessageService(repository)


@pytest.fixture
def thread_service(
    temp_base_dir: Path, message_service: MessageService
) -> ThreadService:
    """Create a ThreadService instance with temporary storage."""
    repository = FileThreadRepository(temp_base_dir)
    return ThreadService(repository, message_service)


class TestThreadServiceJSONPersistence:
    """Test ThreadService with JSON file persistence."""

    @pytest.mark.asyncio
    async def test_create_thread_creates_directory_structure(
        self, thread_service: ThreadService, temp_base_dir: Path
    ) -> None:
        """Test that creating a thread creates the proper directory structure."""
        request = ThreadCreateRequest(name="Test Thread")

        thread = await thread_service.create(request)

        # Check that thread metadata file was created
        thread_file = temp_base_dir / "threads" / f"{thread.id}.json"
        assert thread_file.exists()

        # Check that messages directory was created (by creating a message)
        # Create a message separately to verify the directory structure
        message_service = thread_service._message_service
        message_request = MessageCreateRequest(role="user", content="Test message")
        await message_service.create(thread.id, message_request)

        thread_messages_dir = temp_base_dir / "threads" / thread.id / "messages"
        assert thread_messages_dir.exists()

        # Verify thread metadata content
        with thread_file.open("r") as f:
            import json

            data = json.load(f)
            assert data["name"] == "Test Thread"
            assert data["id"] == thread.id

    @pytest.mark.asyncio
    async def test_create_thread_with_messages(self, thread_service: ThreadService, temp_base_dir: Path) -> None:
        """Test that creating a thread with messages works correctly."""
        messages = [
            MessageCreateRequest(role="user", content="Hello"),
            MessageCreateRequest(role="assistant", content="Hi there!"),
        ]
        request = ThreadCreateRequest(name="Thread with Messages", messages=messages)

        thread = await thread_service.create(request)

        # Check that messages were created
        thread_messages_dir = temp_base_dir / "threads" / thread.id / "messages"
        json_files = list(thread_messages_dir.glob("*.json"))
        assert len(json_files) == 2

        # Verify message content
        for json_file in json_files:
            with json_file.open("r") as f:
                import json

                data = json.load(f)
                assert data["thread_id"] == thread.id
                assert data["role"] in ["user", "assistant"]

    @pytest.mark.asyncio
    async def test_delete_thread_removes_all_files(
        self, thread_service: ThreadService, temp_base_dir: Path
    ) -> None:
        """Test that deleting a thread removes all associated files."""
        request = ThreadCreateRequest(name="Thread to Delete")
        thread = await thread_service.create(request)

        # Add a message
        message_service = thread_service._message_service
        message_request = MessageCreateRequest(role="user", content="Test message")
        await message_service.create(thread.id, message_request)

        # Verify files exist
        thread_file = temp_base_dir / "threads" / f"{thread.id}.json"
        assert thread_file.exists()

        # The thread directory itself doesn't exist, only the messages directory
        messages_dir = temp_base_dir / "threads" / thread.id / "messages"
        assert messages_dir.exists()

        # Delete thread
        await thread_service.delete(thread.id)

        # Verify all files were removed
        assert not thread_file.exists()
        assert not messages_dir.exists()
