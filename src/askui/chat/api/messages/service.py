from datetime import datetime, timezone
from typing import Literal

from pydantic import Field

from askui.chat.api.models import AssistantId, MessageId, RunId, ThreadId
from askui.chat.api.repositories.interfaces import MessageRepository
from askui.models.shared.agent_message_param import MessageParam
from askui.utils.api_utils import ListQuery, ListResponse
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
    def __init__(self, repository: MessageRepository) -> None:
        """Initialize message service.

        Args:
            repository: Message repository for data persistence
        """
        self._repository = repository

    async def create(
        self, thread_id: ThreadId, request: MessageCreateRequest
    ) -> Message:
        new_message = Message(
            **request.model_dump(),
            thread_id=thread_id,
        )
        return await self._repository.create(new_message)

    async def delete(self, thread_id: ThreadId, message_id: MessageId) -> None:
        await self._repository.delete(message_id, thread_id)

    async def find(
        self, thread_id: ThreadId, query: ListQuery
    ) -> ListResponse[Message]:
        """List messages for a thread."""
        return await self._repository.find(query=query, thread_id=thread_id)

    async def find_one(self, thread_id: ThreadId, message_id: MessageId) -> Message:
        """Retrieve a message by ID."""
        return await self._repository.find_one(
            message_id=message_id, thread_id=thread_id
        )
