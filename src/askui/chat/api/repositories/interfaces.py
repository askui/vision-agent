from abc import ABC, abstractmethod
from typing import Any

from askui.chat.api.models import MessageId, RunId, ThreadId
from askui.utils.api_utils import ListQuery, ListResponse


class MessageRepository(ABC):
    """Repository interface for message operations."""

    @abstractmethod
    async def find_one(self, message_id: MessageId, thread_id: ThreadId) -> Any:
        """Retrieve a message by ID and thread ID."""

    @abstractmethod
    async def create(self, message: Any) -> Any:
        """Create a new message."""

    @abstractmethod
    async def update(self, message: Any) -> Any:
        """Update an existing message."""

    @abstractmethod
    async def delete(self, message_id: MessageId, thread_id: ThreadId) -> None:
        """Delete a message by ID and thread ID."""

    @abstractmethod
    async def find(self, query: ListQuery, thread_id: ThreadId) -> ListResponse[Any]:
        """List messages for a thread with optional filtering."""


class ThreadRepository(ABC):
    """Repository interface for thread operations."""

    @abstractmethod
    async def find_one(self, thread_id: ThreadId) -> Any:
        """Retrieve a thread by ID."""

    @abstractmethod
    async def create(self, thread: Any) -> Any:
        """Create a new thread."""

    @abstractmethod
    async def update(self, thread: Any) -> Any:
        """Update an existing thread."""

    @abstractmethod
    async def delete(self, thread_id: ThreadId) -> None:
        """Delete a thread by ID."""

    @abstractmethod
    async def find(self, query: ListQuery) -> ListResponse[Any]:
        """List threads with optional filtering."""


class RunRepository(ABC):
    """Repository interface for run operations."""

    @abstractmethod
    async def find_one(self, run_id: RunId, thread_id: ThreadId | None = None) -> Any:
        """Retrieve a run by ID and optionally thread ID."""

    @abstractmethod
    async def create(self, run: Any) -> Any:
        """Create a new run."""

    @abstractmethod
    async def update(self, run: Any) -> Any:
        """Update an existing run."""

    @abstractmethod
    async def delete(self, run_id: RunId, thread_id: ThreadId | None = None) -> None:
        """Delete a run by ID and optionally thread ID."""

    @abstractmethod
    async def find(self, query: ListQuery, thread_id: ThreadId) -> ListResponse[Any]:
        """List runs for a thread with optional filtering."""
