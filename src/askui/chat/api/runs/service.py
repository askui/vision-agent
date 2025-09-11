from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from pathlib import Path

import anyio
from typing_extensions import override

from askui.chat.api.assistants.service import AssistantService
from askui.chat.api.mcp_clients.manager import McpClientManagerManager
from askui.chat.api.messages.service import MessageService
from askui.chat.api.messages.translator import MessageTranslator
from askui.chat.api.models import RunId, ThreadId, WorkspaceId
from askui.chat.api.runs.models import Run, RunCreateParams
from askui.chat.api.runs.runner.events.events import (
    DoneEvent,
    ErrorEvent,
    Events,
    RunEvent,
)
from askui.chat.api.runs.runner.runner import Runner, RunnerRunService
from askui.utils.api_utils import (
    ConflictError,
    ListQuery,
    ListResponse,
    NotFoundError,
    list_resources,
)


class RunService(RunnerRunService):
    """Service for managing Run resources with filesystem persistence."""

    def __init__(
        self,
        base_dir: Path,
        assistant_service: AssistantService,
        mcp_client_manager_manager: McpClientManagerManager,
        message_service: MessageService,
        message_translator: MessageTranslator,
    ) -> None:
        self._base_dir = base_dir
        self._assistant_service = assistant_service
        self._mcp_client_manager_manager = mcp_client_manager_manager
        self._message_service = message_service
        self._message_translator = message_translator

    def get_runs_dir(self, thread_id: ThreadId) -> Path:
        return self._base_dir / "runs" / thread_id

    def _get_run_path(
        self, thread_id: ThreadId, run_id: RunId, new: bool = False
    ) -> Path:
        run_path = self.get_runs_dir(thread_id) / f"{run_id}.json"
        exists = run_path.exists()
        if new and exists:
            error_msg = f"Run {run_id} already exists in thread {thread_id}"
            raise ConflictError(error_msg)
        if not new and not exists:
            error_msg = f"Run {run_id} not found in thread {thread_id}"
            raise NotFoundError(error_msg)
        return run_path

    def _create(self, thread_id: ThreadId, params: RunCreateParams) -> Run:
        run = Run.create(thread_id, params)
        self.save(run, new=True)
        return run

    async def create(
        self,
        workspace_id: WorkspaceId,
        thread_id: ThreadId,
        params: RunCreateParams,
    ) -> tuple[Run, AsyncGenerator[Events, None]]:
        assistant = self._assistant_service.retrieve(
            workspace_id=workspace_id, assistant_id=params.assistant_id
        )
        run = self._create(thread_id, params)
        send_stream, receive_stream = anyio.create_memory_object_stream[Events]()
        runner = Runner(
            workspace_id=workspace_id,
            assistant=assistant,
            run=run,
            message_service=self._message_service,
            message_translator=self._message_translator,
            mcp_client_manager_manager=self._mcp_client_manager_manager,
            run_service=self,
        )

        async def event_generator() -> AsyncGenerator[Events, None]:
            try:
                yield RunEvent(
                    data=run,
                    event="thread.run.created",
                )
                yield RunEvent(
                    data=run,
                    event="thread.run.queued",
                )

                async def run_runner() -> None:
                    try:
                        await runner.run(send_stream)  # type: ignore[arg-type]
                    finally:
                        await send_stream.aclose()

                async with anyio.create_task_group() as tg:
                    tg.start_soon(run_runner)

                    while True:
                        try:
                            event = await receive_stream.receive()
                            yield event
                            if isinstance(event, DoneEvent) or isinstance(
                                event, ErrorEvent
                            ):
                                break
                        except anyio.EndOfStream:
                            break
            finally:
                await send_stream.aclose()

        return run, event_generator()

    @override
    def retrieve(self, thread_id: ThreadId, run_id: RunId) -> Run:
        try:
            run_file = self._get_run_path(thread_id, run_id)
            return Run.model_validate_json(run_file.read_text())
        except FileNotFoundError as e:
            error_msg = f"Run {run_id} not found in thread {thread_id}"
            raise NotFoundError(error_msg) from e

    def list_(self, thread_id: ThreadId, query: ListQuery) -> ListResponse[Run]:
        runs_dir = self.get_runs_dir(thread_id)
        return list_resources(runs_dir, query, Run)

    def cancel(self, thread_id: ThreadId, run_id: RunId) -> Run:
        run = self.retrieve(thread_id, run_id)
        if run.status in ("cancelled", "cancelling", "completed", "failed", "expired"):
            return run
        run.tried_cancelling_at = datetime.now(tz=timezone.utc)
        self.save(run)
        return run

    @override
    def save(self, run: Run, new: bool = False) -> None:
        runs_dir = self.get_runs_dir(run.thread_id)
        runs_dir.mkdir(parents=True, exist_ok=True)
        run_file = self._get_run_path(run.thread_id, run.id, new=new)
        run_file.write_text(run.model_dump_json(), encoding="utf-8")
