from pathlib import Path

from askui.chat.api.messages.models import Message, MessageCreateParams
from askui.chat.api.models import MessageId, ThreadId
from askui.utils.api_utils import (
    ConflictError,
    ListQuery,
    ListResponse,
    NotFoundError,
    list_resources,
)


class MessageService:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def get_messages_dir(self, thread_id: ThreadId) -> Path:
        return self._base_dir / "messages" / thread_id

    def _get_message_path(
        self, thread_id: ThreadId, message_id: MessageId, new: bool = False
    ) -> Path:
        message_path = self.get_messages_dir(thread_id) / f"{message_id}.json"
        exists = message_path.exists()
        if new and exists:
            error_msg = f"Message {message_id} already exists in thread {thread_id}"
            raise ConflictError(error_msg)
        if not new and not exists:
            error_msg = f"Message {message_id} not found in thread {thread_id}"
            raise NotFoundError(error_msg)
        return message_path

    def create(self, thread_id: ThreadId, params: MessageCreateParams) -> Message:
        new_message = Message.create(thread_id, params)
        self._save(new_message, new=True)
        return new_message

    def list_(self, thread_id: ThreadId, query: ListQuery) -> ListResponse[Message]:
        messages_dir = self.get_messages_dir(thread_id)
        return list_resources(messages_dir, query, Message)

    def retrieve(self, thread_id: ThreadId, message_id: MessageId) -> Message:
        try:
            message_file = self._get_message_path(thread_id, message_id)
            return Message.model_validate_json(message_file.read_text(encoding="utf-8"))
        except FileNotFoundError as e:
            error_msg = f"Message {message_id} not found in thread {thread_id}"
            raise NotFoundError(error_msg) from e

    def delete(self, thread_id: ThreadId, message_id: MessageId) -> None:
        try:
            self._get_message_path(thread_id, message_id).unlink()
        except FileNotFoundError as e:
            error_msg = f"Message {message_id} not found in thread {thread_id}"
            raise NotFoundError(error_msg) from e

    def _save(self, message: Message, new: bool = False) -> None:
        messages_dir = self.get_messages_dir(message.thread_id)
        messages_dir.mkdir(parents=True, exist_ok=True)
        message_file = self._get_message_path(message.thread_id, message.id, new=new)
        message_file.write_text(message.model_dump_json(), encoding="utf-8")
