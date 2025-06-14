from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

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
from askui.models.shared.computer_agent_message_param import (
    ContentBlockParam,
    MessageParam,
    TextBlockParam,
)


class MessageBase(BaseModel):
    id: MessageId = Field(default_factory=lambda: generate_time_ordered_id("msg"))
    assistant_id: AssistantId | None = None
    thread_id: ThreadId
    created_at: UnixDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    object: Literal["thread.message"] = "thread.message"
    role: Literal["user", "assistant"]
    run_id: RunId | None = None


class MessagePersisted(MessageBase, MessageParam):
    pass


class MessagePersistedService:
    def __init__(self, base_dir: Path) -> None:
        """Initialize message service.

        Args:
            base_dir: Base directory to store message data
        """
        self._base_dir = base_dir
        self._threads_dir = base_dir / "threads"

    def create(
        self, thread_id: ThreadId, message: MessagePersisted
    ) -> MessagePersisted:
        messages = self.list_(
            thread_id, ListQuery(limit=MAX_MESSAGES_PER_THREAD, order="asc")
        )
        self.save(thread_id, messages + [message])
        return message

    def delete(self, thread_id: ThreadId, message_id: MessageId) -> None:
        messages = self.list_(
            thread_id, ListQuery(limit=MAX_MESSAGES_PER_THREAD, order="asc")
        )
        filtered_messages = [m for m in messages if m.id != message_id]
        if len(filtered_messages) == len(messages):
            error_msg = f"Message {message_id} not found in thread {thread_id}"
            raise ValueError(error_msg)
        self.save(thread_id, filtered_messages)

    def list_(self, thread_id: ThreadId, query: ListQuery) -> list[MessagePersisted]:
        thread_file = self._threads_dir / f"{thread_id}.jsonl"
        if not thread_file.exists():
            error_msg = f"Thread {thread_id} not found"
            raise FileNotFoundError(error_msg)

        messages: list[MessagePersisted] = []
        with thread_file.open("r") as f:
            for line in f:
                msg = MessagePersisted.model_validate_json(line)
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

    def extend_content(
        self,
        thread_id: ThreadId,
        message_id: MessageId,
        content: str | list[ContentBlockParam],
    ) -> MessagePersisted:
        thread_path = self._get_thread_path(thread_id)
        _content = (
            content if isinstance(content, list) else [TextBlockParam(text=content)]
        )
        msg_extended: MessagePersisted | None = None
        messages: list[MessagePersisted] = []
        with thread_path.open("r") as f:
            for line in f:
                msg = MessagePersisted.model_validate_json(line)
                if msg.id == message_id:
                    match msg.content:
                        case list():
                            msg.content.extend(_content)
                        case str():
                            msg.content = [TextBlockParam(text=msg.content)]
                            msg.content.extend(_content)
                    msg_extended = msg
                messages.append(msg)
        if msg_extended:
            self.save(thread_id, messages)
            return msg_extended

        error_msg = f"Message {message_id} not found"
        raise ValueError(error_msg)

    def save(self, thread_id: ThreadId, messages: list[MessagePersisted]) -> None:
        if len(messages) > MAX_MESSAGES_PER_THREAD:
            error_msg = f"Thread {thread_id} has too many messages"
            raise ValueError(error_msg)
        messages = sorted(messages, key=lambda m: m.created_at)
        thread_path = self._get_thread_path(thread_id)
        with thread_path.open("w") as f:
            for msg in messages:
                f.write(msg.model_dump_json())
                f.write("\n")
