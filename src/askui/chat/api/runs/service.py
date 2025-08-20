from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from pathlib import Path

import anyio
from pydantic import BaseModel

from askui.chat.api.models import AssistantId, RunId, ThreadId
from askui.chat.api.runs.models import Run
from askui.chat.api.runs.runner.events import Events
from askui.chat.api.runs.runner.events.done_events import DoneEvent
from askui.chat.api.runs.runner.events.error_events import ErrorEvent
from askui.chat.api.runs.runner.events.run_events import RunEvent
from askui.chat.api.runs.runner.runner import Runner
from askui.utils.api_utils import ListQuery, ListResponse


class CreateRunRequest(BaseModel):
    assistant_id: AssistantId
    stream: bool = True


class RunService:
    """
    Service for managing runs. Handles creation, retrieval, listing, and
    cancellation of runs.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._runs_dir = base_dir / "runs"

    def _run_path(self, thread_id: ThreadId, run_id: RunId) -> Path:
        return self._runs_dir / f"{thread_id}__{run_id}.json"

    def _create_run(self, thread_id: ThreadId, request: CreateRunRequest) -> Run:
        run = Run(thread_id=thread_id, assistant_id=request.assistant_id)
        self._runs_dir.mkdir(parents=True, exist_ok=True)
        self._update_run_file(run)
        return run

    async def create(
        self, thread_id: ThreadId, request: CreateRunRequest
    ) -> tuple[Run, AsyncGenerator[Events, None]]:
        run = self._create_run(thread_id, request)
        send_stream, receive_stream = anyio.create_memory_object_stream[Events]()
        runner = Runner(run, self._base_dir)

        async def event_generator() -> AsyncGenerator[Events, None]:
            try:
                yield RunEvent(
                    # run already in progress instead of queued which is
                    # different from OpenAI
                    data=run,
                    event="thread.run.created",
                )
                yield RunEvent(
                    # run already in progress instead of queued which is
                    # different from OpenAI
                    data=run,
                    event="thread.run.queued",
                )

                # Start the runner in a background task
                async def run_runner() -> None:
                    try:
                        await runner.run(send_stream)  # type: ignore[arg-type]
                    finally:
                        await send_stream.aclose()

                # Create a task group to manage the runner and event processing
                async with anyio.create_task_group() as tg:
                    # Start the runner in the background
                    tg.start_soon(run_runner)

                    # Process events from the stream
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

    def _update_run_file(self, run: Run) -> None:
        run_file = self._run_path(run.thread_id, run.id)
        with run_file.open("w", encoding="utf-8") as f:
            f.write(run.model_dump_json())

    def retrieve(self, run_id: RunId) -> Run:
        # Find the file by run_id
        for f in self._runs_dir.glob(f"*__{run_id}.json"):
            with f.open("r", encoding="utf-8") as file:
                return Run.model_validate_json(file.read())
        error_msg = f"Run {run_id} not found"
        raise FileNotFoundError(error_msg)

    def list_(self, thread_id: ThreadId, query: ListQuery) -> ListResponse[Run]:
        """List runs, optionally filtered by thread.

        Args:
            thread_id (ThreadId): ID of thread to filter runs by
            query (ListQuery): Query parameters for listing runs

        Returns:
            ListResponse[Run]: ListResponse containing runs sorted by creation date
        """
        if not self._runs_dir.exists():
            return ListResponse(data=[])

        run_files = list(self._runs_dir.glob(f"{thread_id}__*.json"))

        runs: list[Run] = []
        for f in run_files:
            with f.open("r", encoding="utf-8") as file:
                runs.append(Run.model_validate_json(file.read()))

        # Sort by creation date
        runs = sorted(
            runs,
            key=lambda r: r.created_at,
            reverse=(query.order == "desc"),
        )

        # Apply before/after filters
        if query.after:
            runs = [r for r in runs if r.id > query.after]
        if query.before:
            runs = [r for r in runs if r.id < query.before]

        # Apply limit
        runs = runs[: query.limit]

        return ListResponse(
            data=runs,
            first_id=runs[0].id if runs else None,
            last_id=runs[-1].id if runs else None,
            has_more=len(run_files) > query.limit,
        )

    def cancel(self, run_id: RunId) -> Run:
        run = self.retrieve(run_id)
        if run.status in ("cancelled", "cancelling", "completed", "failed", "expired"):
            return run
        run.tried_cancelling_at = datetime.now(tz=timezone.utc)
        for f in self._runs_dir.glob(f"*__{run_id}.json"):
            with f.open("w", encoding="utf-8") as file:
                file.write(run.model_dump_json())
            return run
        # Find the file by run_id
        error_msg = f"Run {run_id} not found"
        raise FileNotFoundError(error_msg)
