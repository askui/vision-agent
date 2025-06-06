from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

from askui.chat.api.models import Event
from askui.chat.api.utils import generate_time_ordered_id
from askui.models.shared.computer_agent_message_param import MessageParam


class Message(MessageParam):
    """A message in a thread."""

    id: str = Field(default_factory=lambda: generate_time_ordered_id("msg"))
    thread_id: str
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    object: str = "message"


class MessageEvent(Event):
    data: Message
    event: Literal["message.created"]


class MessageListResponse(BaseModel):
    """Response model for listing messages."""

    object: str = "list"
    data: list[Message]
    first_id: str | None = None
    last_id: str | None = None
    has_more: bool = False


class MessageService:
    """Service for managing messages within threads."""

    def __init__(self, base_dir: Path) -> None:
        """Initialize message service.

        Args:
            base_dir: Base directory to store message data
        """
        self._base_dir = base_dir
        self._threads_dir = base_dir / "threads"

    def list_(
        self, thread_id: str, limit: int | None = None, after: str | None = None
    ) -> MessageListResponse:
        """List all messages in a thread.

        Args:
            thread_id: ID of thread to list messages from
            limit: Optional maximum number of messages to return
            after: Optional message ID after which messages are returned

        Returns:
            MessageListResponse containing messages sorted by creation date

        Raises:
            FileNotFoundError: If thread doesn't exist
        """
        thread_file = self._threads_dir / f"{thread_id}.jsonl"
        if not thread_file.exists():
            error_msg = f"Thread {thread_id} not found"
            raise FileNotFoundError(error_msg)

        messages: list[Message] = []
        with thread_file.open("r") as f:
            for line in f:
                msg = Message.model_validate_json(line)
                messages.append(msg)

        # Sort by creation date
        messages = sorted(messages, key=lambda m: m.created_at)
        if after:
            messages = [m for m in messages if m.id > after]

        # Apply limit if specified
        if limit is not None:
            messages = messages[:limit]

        return MessageListResponse(
            data=messages,
            first_id=messages[0].id if messages else None,
            last_id=messages[-1].id if messages else None,
            has_more=len(messages) > (limit or len(messages)),
        )

    def create(
        self,
        thread_id: str,
        message: MessageParam,
    ) -> Message:
        """Create a new message in a thread.

        Args:
            thread_id: ID of thread to create message in
            role: Role of message sender
            content: Message content

        Returns:
            Created message object

        Raises:
            FileNotFoundError: If thread doesn't exist
        """
        thread_file = self._threads_dir / f"{thread_id}.jsonl"
        if not thread_file.exists():
            error_msg = f"Thread {thread_id} not found"
            raise FileNotFoundError(error_msg)
        message = Message.model_construct(
            thread_id=thread_id,
            role=message.role,
            content=message.content,
        )
        with thread_file.open("a") as f:
            f.write(message.model_dump_json())
            f.write("\n")
        return message

    def retrieve(self, thread_id: str, message_id: str) -> Message:
        """Retrieve a specific message from a thread.

        Args:
            thread_id: ID of thread containing message
            message_id: ID of message to retrieve

        Returns:
            Message object

        Raises:
            FileNotFoundError: If thread or message doesn't exist
        """
        messages = self.list_(thread_id).data
        for msg in messages:
            if msg.id == message_id:
                return msg
        error_msg = f"Message {message_id} not found in thread {thread_id}"
        raise FileNotFoundError(error_msg)

    def delete(self, thread_id: str, message_id: str) -> None:
        """Delete a message from a thread.

        Args:
            thread_id: ID of thread containing message
            message_id: ID of message to delete

        Raises:
            FileNotFoundError: If thread or message doesn't exist
        """
        thread_file = self._threads_dir / f"{thread_id}.jsonl"
        if not thread_file.exists():
            error_msg = f"Thread {thread_id} not found"
            raise FileNotFoundError(error_msg)

        # Read all messages
        messages: list[Message] = []
        with thread_file.open("r") as f:
            for line in f:
                msg = Message.model_validate_json(line)
                if msg.id != message_id:
                    messages.append(msg)

        # Write back all messages except the deleted one
        with thread_file.open("w") as f:
            for msg in messages:
                f.write(msg.model_dump_json())
                f.write("\n")
