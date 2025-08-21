from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import anyio
from pydantic import BaseModel

from askui.chat.api.models import AssistantId, RunId, ThreadId
from askui.chat.api.repositories.interfaces import RunRepository
from askui.chat.api.runs.models import Run, RunStatus
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

    def __init__(self, repository: RunRepository, base_dir: str) -> None:
        self._repository = repository
        self._base_dir = base_dir  # Still needed for Runner

    async def _create_run(self, thread_id: ThreadId, request: CreateRunRequest) -> Run:
        run = Run(thread_id=thread_id, assistant_id=request.assistant_id)
        return await self._repository.create(run)

    async def create(
        self, thread_id: ThreadId, request: CreateRunRequest
    ) -> tuple[Run, AsyncGenerator[Events, None]]:
        run = await self._create_run(thread_id, request)
        send_stream, receive_stream = anyio.create_memory_object_stream[Events]()
        # Runner still needs base_dir - this will be refactored later
        from pathlib import Path

        runner = Runner(run, Path(self._base_dir))

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

    async def find_one(self, thread_id: ThreadId, run_id: RunId) -> Run:
        """Retrieve a run by ID."""
        return await self._repository.find_one(run_id=run_id, thread_id=thread_id)

    async def find(self, thread_id: ThreadId, query: ListQuery) -> ListResponse[Run]:
        """List runs for a thread."""
        return await self._repository.find(query=query, thread_id=thread_id)

    async def cancel(self, run_id: RunId) -> Run:
        """Cancel a run."""
        run = await self._repository.find_one(run_id, thread_id=None)
        run.status = RunStatus.CANCELED
        run.ended_at = datetime.now(timezone.utc)
        return await self._repository.update(run)
