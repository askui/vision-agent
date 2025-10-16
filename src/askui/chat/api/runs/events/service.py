import asyncio
import logging
import types
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, AsyncIterator, Type

import aiofiles

if TYPE_CHECKING:
    from aiofiles.threadpool.text import AsyncTextIOWrapper

from askui.chat.api.models import RunId, ThreadId
from askui.chat.api.runs.events.done_events import DoneEvent
from askui.chat.api.runs.events.error_events import (
    ErrorEvent,
    ErrorEventData,
    ErrorEventDataError,
)
from askui.chat.api.runs.events.events import Event, EventAdapter
from askui.chat.api.runs.events.run_events import RunEvent
from askui.chat.api.runs.models import Run

logger = logging.getLogger(__name__)


class EventFileManager:
    """Manages the lifecycle of a single event file with reference counting."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.readers_count = 0
        self.writer_active = False
        self._lock = asyncio.Lock()
        self._file_created_event = asyncio.Event()
        self._new_event_event = asyncio.Event()

    async def add_reader(self) -> None:
        """Add a reader reference."""
        async with self._lock:
            self.readers_count += 1

    async def remove_reader(self) -> None:
        """Remove a reader reference and cleanup if no refs remain."""
        async with self._lock:
            self.readers_count -= 1
            await self._cleanup_if_needed()

    async def set_writer_active(self, active: bool) -> None:
        """Set writer active status."""
        async with self._lock:
            self.writer_active = active
            if not active:
                await self._cleanup_if_needed()

    async def _cleanup_if_needed(self) -> None:
        """Delete file if no active connections remain."""
        if not self.writer_active and self.readers_count == 0:
            try:
                if self.file_path.exists():
                    self.file_path.unlink()
                    # we keep the parent directory
            except FileNotFoundError:
                pass  # Already deleted

    async def notify_file_created(self) -> None:
        """Signal that the file has been created."""
        self._file_created_event.set()

    async def wait_for_file(self, timeout: float = 30.0) -> None:
        """Wait for the file to be created.

        Args:
            timeout: Timeout in seconds.

        Raises:
            TimeoutError: If the file is not created within the timeout.
        """
        await asyncio.wait_for(self._file_created_event.wait(), timeout)

    async def notify_new_event(self) -> None:
        """Signal that a new event has been written to the file."""
        self._new_event_event.set()

    async def wait_for_new_event(
        self, timeout: float = 30.0, clear: bool = False
    ) -> None:
        """Wait for a new event to be written to the file."""
        await asyncio.wait_for(self._new_event_event.wait(), timeout)
        if clear:
            self._new_event_event.clear()


class RetrieveRunService(ABC):
    @abstractmethod
    def retrieve(self, thread_id: ThreadId, run_id: RunId) -> Run:
        raise NotImplementedError


class EventWriter:
    """Writer for appending events to a JSONL file."""

    def __init__(self, manager: EventFileManager):
        self._manager = manager
        self._file: "AsyncTextIOWrapper | None" = None

    async def write_event(self, event: Event) -> None:
        """Write an event to the file."""
        if self._file is None:
            self._file = await aiofiles.open(
                self._manager.file_path, "a", encoding="utf-8"
            ).__aenter__()
            await self._manager.notify_file_created()

        event_json = event.model_dump_json()
        await self._file.write(f"{event_json}\n")
        await self._file.flush()
        await self._manager.notify_new_event()

    async def __aenter__(self) -> "EventWriter":
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        if self._file:
            await self._file.close()


class EventReader:
    """Reader for streaming events from a JSONL file."""

    def __init__(
        self,
        manager: EventFileManager,
        run_service: RetrieveRunService,
        start_index: int,
        thread_id: ThreadId,
        run_id: RunId,
    ):
        self._manager = manager
        self._run_service = run_service
        self._start_index = start_index
        self._thread_id = thread_id
        self._run_id = run_id

    async def _iter_final_events(self, run: Run) -> AsyncIterator[Event]:
        match run.status:
            case "completed":
                yield RunEvent(data=run, event="thread.run.completed")
                yield DoneEvent()
            case "failed":
                yield ErrorEvent(
                    data=ErrorEventData(
                        error=ErrorEventDataError(
                            message=run.last_error.message
                            if run.last_error
                            else "Unknown error"
                        )
                    )
                )
            case "cancelled":
                yield RunEvent(data=run, event="thread.run.cancelled")
                yield DoneEvent()
            case "expired":
                yield RunEvent(data=run, event="thread.run.expired")
                yield DoneEvent()
            case _:
                pass

    async def read_events(self) -> AsyncIterator[Event]:  # noqa: C901
        """
        Stream events from the file starting at the specified index.
        Continues reading until a terminal event (DoneEvent or ErrorEvent) is found.

        Yields:
            Event objects parsed from the JSONL file.
        """
        while True:
            try:
                await self._manager.wait_for_file()
                break
            except asyncio.exceptions.TimeoutError:
                logger.warning(
                    "Timeout waiting for file %s to be created",
                    self._manager.file_path,
                )
                if run := self._run_service.retrieve(self._thread_id, self._run_id):
                    if run.status not in ("queued", "in_progress"):
                        async for event in self._iter_final_events(run):
                            yield event
                        return

        line_index = -1
        current_position = 0
        async with aiofiles.open(
            self._manager.file_path, "r", encoding="utf-8"
        ) as file:
            while True:
                if await file.tell() != current_position:
                    await file.seek(current_position)
                async for line in file:
                    line_index += 1
                    if line_index < self._start_index:
                        continue

                    if stripped_line := line.strip():
                        event = EventAdapter.validate_json(stripped_line)
                        yield event
                        if isinstance(event, (DoneEvent, ErrorEvent)):
                            return
                        await asyncio.sleep(0.25)
                current_position = await file.tell()
                while True:
                    try:
                        await self._manager.wait_for_new_event(clear=True)
                        break
                    except asyncio.exceptions.TimeoutError:
                        logger.warning(
                            "Timeout waiting for file %s to have a new event",
                            self._manager.file_path,
                        )
                        if run := self._run_service.retrieve(
                            self._thread_id, self._run_id
                        ):
                            if run.status not in (
                                "queued",
                                "in_progress",
                                "cancelling",
                            ):
                                async for event in self._iter_final_events(run):
                                    yield event
                                return


class EventService:
    """
    Service for managing event files with concurrent read/write access.

    Features:
    - Single writer, multiple readers per file
    - Automatic file cleanup when all connections close
    - Thread-safe operations
    - Performant streaming reads
    """

    _file_managers: dict[RunId, EventFileManager] = {}
    _lock = asyncio.Lock()

    def __init__(self, base_dir: Path, run_service: RetrieveRunService) -> None:
        self._base_dir = base_dir
        self._run_service = run_service

    def _get_event_path(self, thread_id: ThreadId, run_id: RunId) -> Path:
        """Get the file path for an event."""
        return self._base_dir / "events" / thread_id / f"{run_id}.jsonl"

    async def _get_or_create_manager(
        self, thread_id: ThreadId, run_id: RunId
    ) -> EventFileManager:
        """Get or create a file manager for the session."""
        async with self._lock:
            if run_id not in self._file_managers:
                events_file = self._get_event_path(thread_id, run_id)
                events_file.parent.mkdir(parents=True, exist_ok=True)
                self._file_managers[run_id] = EventFileManager(events_file)
            return self._file_managers[run_id]

    @asynccontextmanager
    async def create_writer(
        self, thread_id: ThreadId, run_id: RunId
    ) -> AsyncIterator["EventWriter"]:
        """
        Create a writer context manager for appending events to a file.

        Args:
            thread_id: Thread ID of the file to write.
            run_id: Run ID of the file to write.

        Yields:
            EventWriter instance for writing events.
        """
        manager = await self._get_or_create_manager(thread_id, run_id)
        await manager.set_writer_active(True)

        try:
            writer = EventWriter(manager)
            yield writer
        finally:
            await manager.set_writer_active(False)
            # Cleanup manager reference if file was deleted
            async with self._lock:
                if not manager.file_path.exists():
                    self._file_managers.pop(run_id, None)

    @asynccontextmanager
    async def create_reader(
        self, thread_id: ThreadId, run_id: RunId, start_index: int = 0
    ) -> AsyncIterator["EventReader"]:
        """
        Create a reader context manager for reading events from a file.

        Args:
            thread_id: Thread ID of the file to read.
            run_id: Run ID of the file to read.
            start_index: Index to start reading from (0-based).

        Yields:
            EventReader instance for reading events.
        """
        manager = await self._get_or_create_manager(thread_id, run_id)
        await manager.add_reader()

        try:
            reader = EventReader(
                manager=manager,
                run_service=self._run_service,
                start_index=start_index,
                thread_id=thread_id,
                run_id=run_id,
            )
            yield reader
        finally:
            await manager.remove_reader()
            # Cleanup manager reference if file was deleted
            async with self._lock:
                if not manager.file_path.exists():
                    self._file_managers.pop(run_id, None)
