from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from askui.chat.api.messages.message_persisted_service import (
    MessagePersisted,
    MessagePersistedService,
)
from askui.chat.api.messages.service import MessageCreateRequest, MessageService
from askui.chat.api.models import ListQuery, ListResponse, ThreadId, UnixDatetime
from askui.chat.api.utils import generate_time_ordered_id


class Thread(BaseModel):
    """A chat thread/session."""

    id: ThreadId = Field(default_factory=lambda: generate_time_ordered_id("thread"))
    created_at: UnixDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    object: Literal["thread"] = "thread"


class ThreadCreateRequest(BaseModel):
    messages: list[MessagePersisted] | None = None


class ThreadService:
    """Service for managing chat threads/sessions."""

    def __init__(
        self,
        base_dir: Path,
        message_service: MessagePersistedService,
    ) -> None:
        """Initialize thread service.

        Args:
            base_dir: Base directory to store thread data
        """
        self._base_dir = base_dir
        self._threads_dir = base_dir / "threads"
        self._message_service = message_service

    def list_(self, query: ListQuery) -> ListResponse[Thread]:
        """List all available threads.

        Args:
            query (ListQuery): Query parameters for listing threads

        Returns:
            ListResponse[Thread]: ListResponse containing threads sorted by creation date
        """
        if not self._threads_dir.exists():
            return ListResponse(data=[])

        thread_files = list(self._threads_dir.glob("*.jsonl"))
        threads: list[Thread] = []
        for f in thread_files:
            thread_id = f.stem
            created_at = datetime.fromtimestamp(
                f.stat().st_ctime, tz=timezone.utc
            )  # TODO Check how we save the created time and that it is consistent and correct
            threads.append(
                Thread(
                    id=thread_id,
                    created_at=created_at,
                )
            )

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

    def create(self, request: ThreadCreateRequest) -> Thread:
        """Create a new thread.

        Returns:
            Created thread object
        """
        thread = Thread()
        thread_file = self._threads_dir / f"{thread.id}.jsonl"
        self._threads_dir.mkdir(parents=True, exist_ok=True)
        thread_file.touch()
        if request.messages:
            for message in request.messages:
                self._message_service.create(
                    thread_id=thread.id,
                    message=message,
                )
        return thread

    def retrieve(self, thread_id: ThreadId) -> Thread:
        """Retrieve a thread by ID.

        Args:
            thread_id: ID of thread to retrieve

        Returns:
            Thread object

        Raises:
            FileNotFoundError: If thread doesn't exist
        """
        thread_file = self._threads_dir / f"{thread_id}.jsonl"
        if not thread_file.exists():
            error_msg = f"Thread {thread_id} not found"
            raise FileNotFoundError(error_msg)

        created_at = datetime.fromtimestamp(
            thread_file.stat().st_ctime, tz=timezone.utc
        )
        return Thread(
            id=thread_id,
            created_at=created_at,
        )

    def delete(self, thread_id: ThreadId) -> None:
        """Delete a thread and all its associated files.

        Args:
            thread_id (ThreadId): ID of thread to delete

        Raises:
            FileNotFoundError: If thread doesn't exist
        """
        thread_file = self._threads_dir / f"{thread_id}.jsonl"
        if not thread_file.exists():
            error_msg = f"Thread {thread_id} not found"
            raise FileNotFoundError(error_msg)

        # Delete thread file
        thread_file.unlink()
