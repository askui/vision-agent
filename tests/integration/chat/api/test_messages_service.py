"""Integration tests for the MessageService with JSON file persistence."""

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from askui.chat.api.messages.service import MessageCreateRequest, MessageService
from askui.chat.api.models import ThreadId
from askui.chat.api.repositories.file_repositories import FileMessageRepository


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
def thread_id() -> ThreadId:
    """Create a test thread ID."""
    return "thread_test123"


class TestMessageServiceJSONPersistence:
    """Test MessageService with JSON file persistence."""

    @pytest.mark.asyncio
    async def test_create_message_creates_individual_json_file(
        self, message_service: MessageService, thread_id: ThreadId, temp_base_dir: Path
    ) -> None:
        """Test that creating a message creates an individual JSON file."""
        request = MessageCreateRequest(role="user", content="Hello, world!")

        message = await message_service.create(thread_id, request)

        # Check that the message directory was created
        messages_dir = temp_base_dir / "threads" / thread_id / "messages"
        assert messages_dir.exists()

        # Check that the message file was created
        message_file = messages_dir / f"{message.id}.json"
        assert message_file.exists()

        # Verify the file contains the correct JSON data
        with message_file.open("r") as f:
            data = json.load(f)
            assert data["role"] == "user"
            assert data["content"] == "Hello, world!"
            assert data["id"] == message.id
            assert data["thread_id"] == thread_id

    @pytest.mark.asyncio
    async def test_list_messages_reads_from_json_files(
        self, message_service: MessageService, thread_id: ThreadId
    ) -> None:
        """Test that listing messages reads from individual JSON files."""
        # Create multiple messages
        messages = []
        for i in range(3):
            request = MessageCreateRequest(
                role="user" if i % 2 == 0 else "assistant", content=f"Message {i}"
            )
            message = await message_service.create(thread_id, request)
            messages.append(message)

        # List messages
        from askui.utils.api_utils import ListQuery

        query = ListQuery(limit=10, order="asc")
        # Test listing messages
        response = await message_service.find(thread_id, query)

        # Verify all messages were found
        assert len(response.data) == 3

        # Verify messages are sorted by creation time
        assert response.data[0].created_at <= response.data[1].created_at
        assert response.data[1].created_at <= response.data[2].created_at

    @pytest.mark.asyncio
    async def test_delete_message_removes_json_file(
        self, message_service: MessageService, thread_id: ThreadId, temp_base_dir: Path
    ) -> None:
        """Test that deleting a message removes its JSON file."""
        request = MessageCreateRequest(role="user", content="Delete me")

        message = await message_service.create(thread_id, request)
        message_file = (
            temp_base_dir / "threads" / thread_id / "messages" / f"{message.id}.json"
        )
        assert message_file.exists()

        # Delete the message
        await message_service.delete(thread_id, message.id)

        # Verify the file was removed
        assert not message_file.exists()

    @pytest.mark.asyncio
    async def test_directory_structure_is_correct(
        self, message_service: MessageService, thread_id: ThreadId, temp_base_dir: Path
    ) -> None:
        """Test that the directory structure follows the expected pattern."""
        request = MessageCreateRequest(role="user", content="Test message")

        await message_service.create(thread_id, request)

        # Check directory structure - messages are stored in base_dir/threads/thread_id/messages/
        messages_dir = temp_base_dir / "threads" / thread_id / "messages"

        assert messages_dir.exists()

        # Check that there's a JSON file in the messages directory
        json_files = list(messages_dir.glob("*.json"))
        assert len(json_files) == 1
        assert json_files[0].suffix == ".json"
