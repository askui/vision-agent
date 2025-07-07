from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import Field

from askui.chat.api.models import (
    MAX_MESSAGES_PER_THREAD,
    AssistantId,
    ListQuery,
    MessageId,
    RunId,
    ThreadId,
    UnixDatetime,
)
from askui.chat.api.utils import generate_time_ordered_id
from askui.models.shared.agent_message_param import MessageParam


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
        self._threads_dir = base_dir / "threads"

    def create(self, thread_id: ThreadId, request: MessageCreateRequest) -> Message:
        messages = self.list_(
            thread_id, ListQuery(limit=MAX_MESSAGES_PER_THREAD, order="asc")
        )
        new_message = Message(
            **request.model_dump(),
            thread_id=thread_id,
        )
        self.save(thread_id, messages + [new_message])
        return new_message

    def delete(self, thread_id: ThreadId, message_id: MessageId) -> None:
        messages = self.list_(
            thread_id, ListQuery(limit=MAX_MESSAGES_PER_THREAD, order="asc")
        )
        filtered_messages = [m for m in messages if m.id != message_id]
        if len(filtered_messages) == len(messages):
            error_msg = f"Message {message_id} not found in thread {thread_id}"
            raise ValueError(error_msg)
        self.save(thread_id, filtered_messages)

    def list_(self, thread_id: ThreadId, query: ListQuery) -> list[Message]:
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
        messages = sorted(
            messages, key=lambda m: m.created_at, reverse=(query.order == "desc")
        )

        # Apply before/after filters
        if query.after:
            messages = [m for m in messages if m.id > query.after]
        if query.before:
            messages = [m for m in messages if m.id < query.before]

        # Apply limit
        return messages[: query.limit]

    def _get_thread_path(self, thread_id: ThreadId) -> Path:
        thread_path = self._threads_dir / f"{thread_id}.jsonl"
        if not thread_path.exists():
            error_msg = f"Thread {thread_id} not found"
            raise FileNotFoundError(error_msg)
        return thread_path

    def save(self, thread_id: ThreadId, messages: list[Message]) -> None:
        if len(messages) > MAX_MESSAGES_PER_THREAD:
            error_msg = f"Thread {thread_id} has too many messages"
            raise ValueError(error_msg)
        messages = sorted(messages, key=lambda m: m.created_at)
        thread_path = self._get_thread_path(thread_id)
        with thread_path.open("w") as f:
            for msg in messages:
                f.write(msg.model_dump_json())
                f.write("\n")
