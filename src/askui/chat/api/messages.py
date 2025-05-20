from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Sequence, Union

from PIL import Image
from pydantic import AwareDatetime, BaseModel, Field

from askui.chat.api.utils import generate_time_ordered_id


class MessageRole(str, Enum):
    """Valid message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AI = "ai"
    UNKNOWN = "unknown"


class MessageContent(BaseModel):
    """Message content with optional image paths."""

    text: str | None = None
    image_paths: list[str] | None = None


class Message(BaseModel):
    """A message in a thread."""

    id: str = Field(default_factory=lambda: generate_time_ordered_id("msg"))
    thread_id: str
    role: MessageRole
    content: Sequence[MessageContent]
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    object: str = "message"


class MessageListResponse(BaseModel):
    """Response model for listing messages."""

    object: str = "list"
    data: Sequence[Message]
    first_id: str | None = None
    last_id: str | None = None
    has_more: bool = False


class MessagesApi:
    """API for managing messages within threads."""

    ROLE_MAP = {
        "user": MessageRole.USER,
        "anthropic computer use": MessageRole.AI,
        "agentos": MessageRole.ASSISTANT,
        "user (demonstration)": MessageRole.USER,
    }

    def __init__(self, base_dir: Path) -> None:
        """Initialize messages API.

        Args:
            base_dir: Base directory to store message data
        """
        self._base_dir = base_dir
        self._threads_dir = base_dir / "threads"
        self._images_dir = base_dir / "images"

    def list_(self, thread_id: str, limit: int | None = None) -> MessageListResponse:
        """List all messages in a thread.

        Args:
            thread_id: ID of thread to list messages from
            limit: Optional maximum number of messages to return

        Returns:
            MessageListResponse containing messages sorted by creation date

        Raises:
            FileNotFoundError: If thread doesn't exist
        """
        thread_file = self._threads_dir / f"{thread_id}.jsonl"
        if not thread_file.exists():
            error_msg = f"Thread {thread_id} not found"
            raise FileNotFoundError(error_msg)

        messages = []
        with thread_file.open("r") as f:
            for line in f:
                msg = Message.model_validate_json(line)
                messages.append(msg)

        # Sort by creation date
        messages = sorted(messages, key=lambda m: m.created_at)

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
        role: str,
        content: Union[str, dict[str, Any], list[Any]],
        image: Image.Image | list[Image.Image] | None = None,
    ) -> Message:
        """Create a new message in a thread.

        Args:
            thread_id: ID of thread to create message in
            role: Role of message sender
            content: Message content
            image: Optional image(s) to attach

        Returns:
            Created message object

        Raises:
            FileNotFoundError: If thread doesn't exist
        """
        thread_file = self._threads_dir / f"{thread_id}.jsonl"
        if not thread_file.exists():
            error_msg = f"Thread {thread_id} not found"
            raise FileNotFoundError(error_msg)

        # Save images if provided
        image_paths = []
        if image is not None:
            if isinstance(image, list):
                images = image
            else:
                images = [image]

            self._images_dir.mkdir(parents=True, exist_ok=True)
            for img in images:
                # Generate unique image ID using same format as thread/message IDs
                image_id = generate_time_ordered_id("img")
                image_path = self._images_dir / f"{image_id}.png"
                img.save(image_path)
                image_paths.append(str(image_path))

        # Create message content
        message_content = [
            MessageContent(
                text=str(content), image_paths=image_paths if image_paths else None
            )
        ]

        # Create message
        message = Message(
            thread_id=thread_id,
            role=self.ROLE_MAP.get(role.lower(), MessageRole.UNKNOWN),
            content=message_content,
        )

        # Save message
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

        # Get message and image paths before deletion
        msg_to_delete = self.retrieve(thread_id, message_id)
        image_paths = (
            msg_to_delete.content[0].image_paths if msg_to_delete.content else None
        )

        # Read all messages
        messages = []
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

        # Delete associated images if any
        if image_paths:
            for img_path in image_paths:
                try:
                    Path(img_path).unlink()
                except FileNotFoundError:
                    pass  # Image might have been deleted already
