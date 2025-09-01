import shutil
from pathlib import Path

from askui.chat.api.messages.service import MessageService
from askui.chat.api.models import ThreadId
from askui.chat.api.runs.service import RunService
from askui.chat.api.threads.models import Thread, ThreadCreateParams, ThreadModifyParams
from askui.utils.api_utils import (
    ConflictError,
    ListQuery,
    ListResponse,
    NotFoundError,
    list_resources,
)


class ThreadService:
    """Service for managing Thread resources with filesystem persistence."""

    def __init__(
        self, base_dir: Path, message_service: MessageService, run_service: RunService
    ) -> None:
        self._base_dir = base_dir
        self._threads_dir = base_dir / "threads"
        self._message_service = message_service
        self._run_service = run_service

    def _get_thread_path(self, thread_id: ThreadId, new: bool = False) -> Path:
        thread_path = self._threads_dir / f"{thread_id}.json"
        exists = thread_path.exists()
        if new and exists:
            error_msg = f"Thread {thread_id} already exists"
            raise ConflictError(error_msg)
        if not new and not exists:
            error_msg = f"Thread {thread_id} not found"
            raise NotFoundError(error_msg)
        return thread_path

    def list_(self, query: ListQuery) -> ListResponse[Thread]:
        return list_resources(self._threads_dir, query, Thread)

    def retrieve(self, thread_id: ThreadId) -> Thread:
        try:
            thread_path = self._get_thread_path(thread_id)
            return Thread.model_validate_json(thread_path.read_text())
        except FileNotFoundError as e:
            error_msg = f"Thread {thread_id} not found"
            raise NotFoundError(error_msg) from e

    def create(self, params: ThreadCreateParams) -> Thread:
        thread = Thread.create(params)
        self._save(thread, new=True)

        if params.messages:
            for message in params.messages:
                self._message_service.create(
                    thread_id=thread.id,
                    params=message,
                )
        return thread

    def modify(self, thread_id: ThreadId, params: ThreadModifyParams) -> Thread:
        thread = self.retrieve(thread_id)
        modified = thread.modify(params)
        self._save(modified)
        return modified

    def delete(self, thread_id: ThreadId) -> None:
        try:
            shutil.rmtree(
                self._message_service.get_messages_dir(thread_id), ignore_errors=True
            )
            shutil.rmtree(self._run_service.get_runs_dir(thread_id), ignore_errors=True)
            self._get_thread_path(thread_id).unlink()
        except FileNotFoundError as e:
            error_msg = f"Thread {thread_id} not found"
            raise NotFoundError(error_msg) from e

    def _save(self, thread: Thread, new: bool = False) -> None:
        self._threads_dir.mkdir(parents=True, exist_ok=True)
        thread_file = self._get_thread_path(thread.id, new=new)
        thread_file.write_text(thread.model_dump_json(), encoding="utf-8")
