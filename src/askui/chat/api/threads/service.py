from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from pydantic import AwareDatetime, BaseModel, Field

from askui.chat.api.utils import generate_time_ordered_id


class Thread(BaseModel):
    """A chat thread/session."""

    id: str = Field(default_factory=lambda: generate_time_ordered_id("thread"))
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    object: str = "thread"


class ThreadListResponse(BaseModel):
    """Response model for listing threads."""

    object: str = "list"
    data: Sequence[Thread]
    first_id: str | None = None
    last_id: str | None = None
    has_more: bool = False


class ThreadService:
    """Service for managing chat threads/sessions."""

    def __init__(self, base_dir: Path) -> None:
        """Initialize thread service.

        Args:
            base_dir: Base directory to store thread data
        """
        self._base_dir = base_dir
        self._threads_dir = base_dir / "threads"

    def list_(self, limit: int | None = None) -> ThreadListResponse:
        """List all available threads.

        Args:
            limit: Optional maximum number of threads to return

        Returns:
            ThreadListResponse containing threads sorted by creation date (newest first)
        """
        if not self._threads_dir.exists():
            return ThreadListResponse(data=[])

        thread_files = list(self._threads_dir.glob("*.jsonl"))
        threads: list[Thread] = []
        for f in thread_files:
            thread_id = f.stem
            created_at = datetime.fromtimestamp(f.stat().st_ctime, tz=timezone.utc)
            threads.append(
                Thread(
                    id=thread_id,
                    created_at=created_at,
                )
            )

        # Sort by creation date, newest first
        threads = sorted(threads, key=lambda t: t.created_at, reverse=True)

        # Apply limit if specified
        if limit is not None:
            threads = threads[:limit]

        return ThreadListResponse(
            data=threads,
            first_id=threads[0].id if threads else None,
            last_id=threads[-1].id if threads else None,
            has_more=len(thread_files) > (limit or len(thread_files)),
        )

    def create(self) -> Thread:
        """Create a new thread.

        Returns:
            Created thread object
        """
        thread = Thread()
        thread_file = self._threads_dir / f"{thread.id}.jsonl"
        self._threads_dir.mkdir(parents=True, exist_ok=True)
        thread_file.touch()
        return thread

    def retrieve(self, thread_id: str) -> Thread:
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

    def delete(self, thread_id: str) -> None:
        """Delete a thread and all its associated files.

        Args:
            thread_id: ID of thread to delete

        Raises:
            FileNotFoundError: If thread doesn't exist
        """
        thread_file = self._threads_dir / f"{thread_id}.jsonl"
        if not thread_file.exists():
            error_msg = f"Thread {thread_id} not found"
            raise FileNotFoundError(error_msg)

        # Delete thread file
        thread_file.unlink()
