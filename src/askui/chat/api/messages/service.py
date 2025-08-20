from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError

from askui.chat.api.models import AssistantId, MessageId, RunId, ThreadId
from askui.models.shared.agent_message_param import MessageParam
from askui.utils.api_utils import ListQuery, ListResponse, list_resource_paths
from askui.utils.datetime_utils import UnixDatetime
from askui.utils.id_utils import generate_time_ordered_id


class MessageBase(MessageParam):
    assistant_id: AssistantId | None = None
    object: Literal["thread.message"] = "thread.message"
    role: Literal["user", "assistant"]
    run_id: RunId | None = None


class Message(MessageBase):
    id: MessageId = Field(default_factory=lambda: generate_time_ordered_id("msg"))
    thread_id: ThreadId
    created_at: UnixDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )


class MessageCreateRequest(MessageBase):
    pass


class MessageService:
    def __init__(self, base_dir: Path) -> None:
        """Initialize message service.

        Args:
            base_dir: Base directory to store message data
        """
        self._base_dir = base_dir
        self._base_messages_dir = base_dir / "messages"

    def create(self, thread_id: ThreadId, request: MessageCreateRequest) -> Message:
        new_message = Message(
            **request.model_dump(),
            thread_id=thread_id,
        )
        self._save(new_message)
        return new_message

    def delete(self, thread_id: ThreadId, message_id: MessageId) -> None:
        message_file = self._get_message_path(thread_id, message_id)
        if not message_file.exists():
            error_msg = f"Message {message_id} not found in thread {thread_id}"
            raise ValueError(error_msg)
        message_file.unlink()

    def list_(self, thread_id: ThreadId, query: ListQuery) -> ListResponse[Message]:
        messages_dir = self.get_thread_messages_dir(thread_id)
        if not messages_dir.exists():
            return ListResponse(data=[])

        message_paths = list_resource_paths(messages_dir, query)
        messages: list[Message] = []
        for message_file in message_paths:
            try:
                msg = Message.model_validate_json(message_file.read_text())
                messages.append(msg)
            except ValidationError:  # noqa: PERF203
                continue
        has_more = len(messages) > query.limit
        messages = messages[: query.limit]
        return ListResponse(
            data=messages,
            first_id=messages[0].id if messages else None,
            last_id=messages[-1].id if messages else None,
            has_more=has_more,
        )

    def get_thread_messages_dir(self, thread_id: ThreadId) -> Path:
        """Get the directory path for a specific message."""
        return self._base_messages_dir / thread_id

    def _get_message_path(self, thread_id: ThreadId, message_id: MessageId) -> Path:
        """Get the file path for a specific message."""
        return self.get_thread_messages_dir(thread_id) / f"{message_id}.json"

    def _save(self, message: Message) -> None:
        """Save a single message to its own JSON file."""
        messages_dir = self.get_thread_messages_dir(message.thread_id)
        messages_dir.mkdir(parents=True, exist_ok=True)
        message_file = self._get_message_path(message.thread_id, message.id)
        message_file.write_text(message.model_dump_json(), encoding="utf-8")
