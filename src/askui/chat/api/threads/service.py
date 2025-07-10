from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from askui.chat.api.messages.service import MessageCreateRequest, MessageService
from askui.chat.api.models import (
    DoNotPatch,
    ListQuery,
    ListResponse,
    ThreadId,
    UnixDatetime,
)
from askui.chat.api.utils import generate_time_ordered_id


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
        base_dir: Path,
        message_service: MessageService,
    ) -> None:
        """Initialize thread service.

        Args:
            base_dir: Base directory to store thread data
        """
        self._base_dir = base_dir
        self._threads_dir = base_dir / "threads"
        self._message_service = message_service

    def create(self, request: ThreadCreateRequest) -> Thread:
        """Create a new thread.

        Returns:
            Created thread object
        """
        thread = Thread(name=request.name)
        self._threads_dir.mkdir(parents=True, exist_ok=True)
        thread_file = self._threads_dir / f"{thread.id}.json"
        thread_file.write_text(thread.model_dump_json())
        thread_messages_file = self._threads_dir / f"{thread.id}.jsonl"
        thread_messages_file.touch()
        if request.messages:
            for message in request.messages:
                self._message_service.create(
                    thread_id=thread.id,
                    request=message,
                )
        return thread

    def list_(self, query: ListQuery) -> ListResponse[Thread]:
        """List all available threads.

        Args:
            query (ListQuery): Query parameters for listing threads

        Returns:
            ListResponse[Thread]: ListResponse containing threads sorted by creation
                date
        """
        if not self._threads_dir.exists():
            return ListResponse(data=[])

        thread_files = list(self._threads_dir.glob("*.json"))
        threads: list[Thread] = []
        for f in thread_files:
            thread = Thread.model_validate_json(f.read_text())
            threads.append(thread)

        # Sort by creation date
        threads = sorted(
            threads, key=lambda t: t.created_at, reverse=(query.order == "desc")
        )

        # Apply before/after filters
        if query.after:
            threads = [t for t in threads if t.id > query.after]
        if query.before:
            threads = [t for t in threads if t.id < query.before]

        # Apply limit
        threads = threads[: query.limit]

        return ListResponse(
            data=threads,
            first_id=threads[0].id if threads else None,
            last_id=threads[-1].id if threads else None,
            has_more=len(thread_files) > query.limit,
        )

    def retrieve(self, thread_id: ThreadId) -> Thread:
        """Retrieve a thread by ID.

        Args:
            thread_id: ID of thread to retrieve

        Returns:
            Thread object

        Raises:
            FileNotFoundError: If thread doesn't exist
        """
        thread_file = self._threads_dir / f"{thread_id}.json"
        if not thread_file.exists():
            error_msg = f"Thread {thread_id} not found"
            raise FileNotFoundError(error_msg)
        return Thread.model_validate_json(thread_file.read_text())

    def delete(self, thread_id: ThreadId) -> None:
        """Delete a thread and all its associated files.

        Args:
            thread_id (ThreadId): ID of thread to delete

        Raises:
            FileNotFoundError: If thread doesn't exist
        """
        thread_file = self._threads_dir / f"{thread_id}.json"
        if not thread_file.exists():
            error_msg = f"Thread {thread_id} not found"
            raise FileNotFoundError(error_msg)
        thread_messages_file = self._threads_dir / f"{thread_id}.jsonl"
        if thread_messages_file.exists():
            thread_messages_file.unlink()
        thread_file.unlink()

    def modify(self, thread_id: ThreadId, request: ThreadModifyRequest) -> Thread:
        """Modify a thread.

        Args:
            thread_id (ThreadId): ID of thread to modify
            request (ThreadModifyRequest): Request containing the new name
        """
        thread = self.retrieve(thread_id)
        if not isinstance(request.name, DoNotPatch):
            thread.name = request.name
        thread_file = self._threads_dir / f"{thread_id}.json"
        thread_file.write_text(thread.model_dump_json())
        return thread
