import json
import shutil
from pathlib import Path
from typing import Any

import aiofiles
from pydantic import ValidationError

from askui.chat.api.messages.service import Message
from askui.chat.api.models import MessageId, RunId, ThreadId
from askui.utils.api_utils import (
    ConflictError,
    ListQuery,
    ListResponse,
    NotFoundError,
    list_resource_paths,
)

from .interfaces import MessageRepository, RunRepository, ThreadRepository


class FileMessageRepository(MessageRepository):
    """File-based repository for messages."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def _get_messages_dir(self, thread_id: ThreadId) -> Path:
        return self._base_dir / "threads" / thread_id / "messages"

    def _get_message_path(self, thread_id: ThreadId, message_id: MessageId) -> Path:
        return self._get_messages_dir(thread_id) / f"{message_id}.json"

    async def find_one(self, message_id: MessageId, thread_id: ThreadId) -> Any:
        """Retrieve a message by ID and thread ID."""
        message_file = self._get_message_path(message_id, thread_id)
        if not message_file.exists():
            error_msg = f"Message {message_id} not found in thread {thread_id}"
            raise FileNotFoundError(error_msg)

        async with aiofiles.open(message_file, "r", encoding="utf-8") as f:
            return json.loads(await f.read())

    async def create(self, message: Any) -> Any:
        """Create a new message."""
        message_file = self._get_message_path(message["id"], message["thread_id"])
        message_file.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(message_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(message, indent=2, default=str))
        return message

    async def update(self, message: Any) -> Any:
        """Update an existing message."""
        message_file = self._get_message_path(message["id"], message["thread_id"])
        if not message_file.exists():
            error_msg = (
                f"Message {message['id']} not found in thread {message['thread_id']}"
            )
            raise FileNotFoundError(error_msg)

        async with aiofiles.open(message_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(message, indent=2, default=str))
        return message

    async def delete(self, message_id: MessageId, thread_id: ThreadId) -> None:
        """Delete a message by ID and thread ID."""
        message_file = self._get_message_path(message_id, thread_id)
        if message_file.exists():
            message_file.unlink()

    async def find(self, query: ListQuery, thread_id: ThreadId) -> ListResponse[Any]:
        """List messages for a thread with optional filtering."""
        thread_dir = self._get_messages_dir(thread_id)
        if not thread_dir.exists():
            return ListResponse(data=[])

        message_files = list(thread_dir.glob("*.json"))
        messages: list[Any] = []
        for f in message_files:
            async with aiofiles.open(f, "r", encoding="utf-8") as file:
                messages.append(json.loads(await file.read()))

        # Sort by creation date
        messages = sorted(
            messages, key=lambda m: m["created_at"], reverse=(query.order == "desc")
        )

        # Apply before/after filters
        if query.after:
            messages = [m for m in messages if m["id"] > query.after]
        if query.before:
            messages = [m for m in messages if m["id"] < query.before]

        # Apply limit
        messages = messages[: query.limit]

        return ListResponse(
            data=messages,
            first_id=messages[0]["id"] if messages else None,
            last_id=messages[-1]["id"] if messages else None,
            has_more=len(message_files) > query.limit,
        )

    async def exists(self, message_id: MessageId, thread_id: ThreadId) -> bool:
        """Check if message exists."""
        message_path = self._get_message_path(thread_id, message_id)
        return message_path.exists()


class FileThreadRepository(ThreadRepository):
    """File-based repository for threads."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._threads_dir = base_dir / "threads"

    def _get_thread_path(self, thread_id: ThreadId) -> Path:
        return self._threads_dir / f"{thread_id}.json"

    async def create(self, thread: Any) -> Any:
        """Create a new thread."""
        self._threads_dir.mkdir(parents=True, exist_ok=True)

        thread_path = self._get_thread_path(thread.id)
        if thread_path.exists():
            raise ConflictError(f"Thread {thread.id} already exists")

        async with aiofiles.open(thread_path, "w", encoding="utf-8") as f:
            await f.write(thread.model_dump_json())
        return thread

    async def find_one(self, thread_id: ThreadId) -> Any:
        """Retrieve a thread by ID."""
        from askui.chat.api.threads.service import Thread

        thread_path = self._get_thread_path(thread_id)
        if not thread_path.exists():
            raise NotFoundError(f"Thread {thread_id} not found")

        async with aiofiles.open(thread_path, "r", encoding="utf-8") as f:
            content = await f.read()
        return Thread.model_validate_json(content)

    async def update(self, thread: Any) -> Any:
        """Update an existing thread."""
        thread_path = self._get_thread_path(thread.id)
        if not thread_path.exists():
            raise NotFoundError(f"Thread {thread.id} not found")

        async with aiofiles.open(thread_path, "w", encoding="utf-8") as f:
            await f.write(thread.model_dump_json())
        return thread

    async def delete(self, thread_id: ThreadId) -> None:
        """Delete a thread and its associated data."""
        thread_path = self._get_thread_path(thread_id)
        if not thread_path.exists():
            raise NotFoundError(f"Thread {thread_id} not found")

        # Delete associated messages and runs
        thread_dir = self._base_dir / "threads" / thread_id
        if thread_dir.exists():
            shutil.rmtree(thread_dir)

        # Delete thread file
        thread_path.unlink()

    async def find(self, query: ListQuery) -> ListResponse[Any]:
        """List threads."""
        from askui.chat.api.threads.service import Thread

        if not self._threads_dir.exists():
            return ListResponse(data=[])

        thread_files = list(self._threads_dir.glob("*.json"))
        threads: list[Thread] = []

        for f in thread_files:
            try:
                async with aiofiles.open(f, "r", encoding="utf-8") as file:
                    content = await file.read()
                thread = Thread.model_validate_json(content)
                threads.append(thread)
            except (ValidationError, json.JSONDecodeError):
                continue

        # Sort by creation date
        threads = sorted(
            threads, key=lambda t: t.created_at, reverse=(query.order == "desc")
        )

        # Apply before/after filters
        if query.after:
            threads = [t for t in threads if t.id > query.after]
        if query.before:
            threads = [t for t in threads if t.id < query.before]

        # Calculate has_more before limiting
        has_more = len(threads) > query.limit
        threads = threads[: query.limit]

        return ListResponse(
            data=threads,
            first_id=threads[0].id if threads else None,
            last_id=threads[-1].id if threads else None,
            has_more=has_more,
        )

    async def exists(self, thread_id: ThreadId) -> bool:
        """Check if thread exists."""
        thread_path = self._get_thread_path(thread_id)
        return thread_path.exists()


class FileRunRepository(RunRepository):
    """File-based repository for runs."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def _get_runs_dir(self, thread_id: ThreadId) -> Path:
        return self._base_dir / "threads" / thread_id / "runs"

    def _get_run_path(self, thread_id: ThreadId, run_id: RunId) -> Path:
        return self._get_runs_dir(thread_id) / f"{run_id}.json"

    async def create(self, run: Any) -> Any:
        """Create a new run."""
        runs_dir = self._get_runs_dir(run.thread_id)
        runs_dir.mkdir(parents=True, exist_ok=True)

        run_path = self._get_run_path(run.thread_id, run.id)
        if run_path.exists():
            raise ConflictError(
                f"Run {run.id} already exists in thread {run.thread_id}"
            )

        async with aiofiles.open(run_path, "w", encoding="utf-8") as f:
            await f.write(run.model_dump_json())
        return run

    async def find_one(self, run_id: RunId, thread_id: ThreadId | None = None) -> Any:
        """Retrieve a run by ID."""
        from askui.chat.api.runs.models import Run

        if thread_id:
            run_path = self._get_run_path(thread_id, run_id)
            if run_path.exists():
                async with aiofiles.open(run_path, "r", encoding="utf-8") as f:
                    content = await f.read()
                return Run.model_validate_json(content)
        else:
            # Search across all threads for the run_id
            threads_dir = self._base_dir / "threads"
            if threads_dir.exists():
                thread_dirs = list(threads_dir.iterdir())
                for thread_dir in thread_dirs:
                    if thread_dir.is_dir():
                        run_path = thread_dir / "runs" / f"{run_id}.json"
                        if run_path.exists():
                            async with aiofiles.open(
                                run_path, "r", encoding="utf-8"
                            ) as f:
                                content = await f.read()
                            return Run.model_validate_json(content)

        raise NotFoundError(f"Run {run_id} not found")

    async def update(self, run: Any) -> Any:
        """Update an existing run."""
        run_path = self._get_run_path(run.thread_id, run.id)
        if not run_path.exists():
            raise NotFoundError(f"Run {run.id} not found in thread {run.thread_id}")

        async with aiofiles.open(run_path, "w", encoding="utf-8") as f:
            await f.write(run.model_dump_json())
        return run

    async def delete(self, run_id: RunId, thread_id: ThreadId) -> None:
        """Delete a run by ID."""
        run_path = self._get_run_path(thread_id, run_id)
        if not run_path.exists():
            raise NotFoundError(f"Run {run_id} not found in thread {thread_id}")

        run_path.unlink()

    async def find(self, query: ListQuery, thread_id: ThreadId) -> ListResponse[Any]:
        """List runs for a thread."""
        from askui.chat.api.runs.models import Run

        runs_dir = self._get_runs_dir(thread_id)
        if not runs_dir.exists():
            return ListResponse(data=[])

        run_files = list(runs_dir.glob("*.json"))
        runs: list[Run] = []

        for f in run_files:
            try:
                async with aiofiles.open(f, "r", encoding="utf-8") as file:
                    content = await file.read()
                run = Run.model_validate_json(content)
                runs.append(run)
            except (ValidationError, json.JSONDecodeError):
                continue

        # Sort by creation date
        runs = sorted(runs, key=lambda r: r.created_at, reverse=(query.order == "desc"))

        # Apply before/after filters
        if query.after:
            runs = [r for r in runs if r.id > query.after]
        if query.before:
            runs = [r for r in runs if r.id < query.before]

        # Calculate has_more before limiting
        has_more = len(runs) > query.limit
        runs = runs[: query.limit]

        return ListResponse(
            data=runs,
            first_id=runs[0].id if runs else None,
            last_id=runs[-1].id if runs else None,
            has_more=has_more,
        )

    async def exists(self, run_id: RunId, thread_id: ThreadId) -> bool:
        """Check if run exists."""
        run_path = self._get_run_path(thread_id, run_id)
        return run_path.exists()
