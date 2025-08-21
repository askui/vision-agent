from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from askui.chat.api.messages.service import MessageCreateRequest, MessageService
from askui.chat.api.models import DoNotPatch, ThreadId
from askui.chat.api.repositories.interfaces import ThreadRepository
from askui.utils.api_utils import ListQuery, ListResponse
from askui.utils.datetime_utils import UnixDatetime
from askui.utils.id_utils import generate_time_ordered_id


class Thread(BaseModel):
    """A chat thread/session."""

    id: ThreadId = Field(default_factory=lambda: generate_time_ordered_id("thread"))
    created_at: UnixDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    name: str | None = None
    object: Literal["thread"] = "thread"


class ThreadCreateRequest(BaseModel):
    name: str | None = None
    messages: list[MessageCreateRequest] | None = None


class ThreadModifyRequest(BaseModel):
    name: str | None | DoNotPatch = DoNotPatch()


class ThreadService:
    """Service for managing chat threads/sessions."""

    def __init__(
        self,
        repository: ThreadRepository,
        message_service: MessageService,
    ) -> None:
        """Initialize thread service.

        Args:
            repository: Thread repository for data persistence
            message_service: Message service for creating initial messages
        """
        self._repository = repository
        self._message_service = message_service

    async def find(self, query: ListQuery) -> ListResponse[Thread]:
        """List threads."""
        return await self._repository.find(query=query)

    async def create(self, request: CreateThreadRequest) -> Thread:
        """Create a new thread."""
        thread = Thread(
            title=request.title,
            metadata=request.metadata,
        )
        return await self._repository.create(thread)

    async def find_one(self, thread_id: ThreadId) -> Thread:
        """Retrieve a thread by ID."""
        return await self._repository.find_one(thread_id=thread_id)

    async def delete(self, thread_id: ThreadId) -> None:
        """Delete a thread and its associated data."""
        thread = await self.find_one(thread_id=thread_id)
        await self._repository.delete(thread_id=thread_id)
        await self._message_service.delete_all(thread_id=thread_id)
        await self._run_service.delete_all(thread_id=thread_id)

    async def modify(self, thread_id: ThreadId, request: ThreadModifyRequest) -> Thread:
        """Modify a thread.

        Args:
            thread_id (ThreadId): ID of thread to modify
            request (ThreadModifyRequest): Request containing the new name
        """
        thread = await self.find_one(thread_id)
        if not isinstance(request.name, DoNotPatch):
            thread.name = request.name
        return await self._repository.update(thread)
