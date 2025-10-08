from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import anyio
from askui.chat.api.assistants.service import AssistantService
from askui.chat.api.db.query_builder import QueryBuilder
from askui.chat.api.mcp_clients.manager import McpClientManagerManager
from askui.chat.api.messages.chat_history_manager import ChatHistoryManager
from askui.chat.api.models import RunId, ThreadId, WorkspaceId
from askui.chat.api.runs.events.events import DoneEvent, ErrorEvent, Event, RunEvent
from askui.chat.api.runs.events.service import EventService
from askui.chat.api.runs.models import RunModel
from askui.chat.api.runs.runner.runner import Runner, RunnerRunService
from askui.chat.api.runs.schemas import Run, RunCreateParams, RunListQuery
from askui.chat.api.settings import Settings
from askui.utils.api_utils import ConflictError, ListQuery, ListResponse, NotFoundError
from sqlalchemy.orm import Session
from typing_extensions import override


class RunService(RunnerRunService):
    """Service for managing Run resources with SQLAlchemy persistence."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        assistant_service: AssistantService,
        mcp_client_manager_manager: McpClientManagerManager,
        chat_history_manager: ChatHistoryManager,
        settings: Settings,
    ) -> None:
        self._session_factory = session_factory
        self._assistant_service = assistant_service
        self._mcp_client_manager_manager = mcp_client_manager_manager
        self._chat_history_manager = chat_history_manager
        self._settings = settings
        self._event_service = EventService(Path.cwd() / "chat", self)

    def _to_pydantic(self, db_model: RunModel) -> Run:
        """Convert SQLAlchemy model to Pydantic model."""
        return db_model.to_pydantic()

    def _create(self, thread_id: ThreadId, params: RunCreateParams) -> Run:
        with self._session_factory() as session:
            db_run = RunModel.from_create_params(params, thread_id)
            session.add(db_run)
            session.commit()
            session.refresh(db_run)
            return self._to_pydantic(db_run)

    async def create(
        self,
        workspace_id: WorkspaceId,
        thread_id: ThreadId,
        params: RunCreateParams,
    ) -> tuple[Run, AsyncGenerator[Event, None]]:
        assistant = self._assistant_service.retrieve(
            workspace_id=workspace_id, assistant_id=params.assistant_id
        )
        run = self._create(thread_id, params)
        send_stream, receive_stream = anyio.create_memory_object_stream[Event]()
        runner = Runner(
            workspace_id=workspace_id,
            assistant=assistant,
            run=run,
            chat_history_manager=self._chat_history_manager,
            mcp_client_manager_manager=self._mcp_client_manager_manager,
            run_service=self,
            settings=self._settings,
        )

        async def event_generator() -> AsyncGenerator[Event, None]:
            try:
                async with self._event_service.create_writer(
                    thread_id, run.id
                ) as event_writer:
                    run_created_event = RunEvent(
                        data=run,
                        event="thread.run.created",
                    )
                    await event_writer.write_event(run_created_event)
                    yield run_created_event
                    run_queued_event = RunEvent(
                        data=run,
                        event="thread.run.queued",
                    )
                    await event_writer.write_event(run_queued_event)
                    yield run_queued_event

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
                                await event_writer.write_event(event)
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
        with self._session_factory() as session:
            db_run = (
                session.query(RunModel)
                .filter(
                    RunModel.id == run_id,
                    RunModel.thread_id == thread_id,
                )
                .first()
            )
            if not db_run:
                error_msg = f"Run {run_id} not found in thread {thread_id}"
                raise NotFoundError(error_msg)
            return self._to_pydantic(db_run)

    async def retrieve_stream(
        self, thread_id: ThreadId, run_id: RunId
    ) -> AsyncGenerator[Event, None]:
        async with self._event_service.create_reader(thread_id, run_id) as event_reader:
            async for event in event_reader.read_events():
                yield event

    def list_(self, query: RunListQuery) -> ListResponse[Run]:
        with self._session_factory() as session:
            q = session.query(RunModel)

            # Filter by thread if specified
            if query.thread:
                q = q.filter(RunModel.thread_id == query.thread)

            # Filter by status if specified
            if query.status:
                q = q.filter(RunModel.status.in_(query.status))

            # Convert to ListQuery for QueryBuilder
            list_query = ListQuery(
                limit=query.limit,
                order=query.order,
                after=query.after,
                before=query.before,
            )

            # Apply list query parameters
            q = QueryBuilder.apply_list_query(
                q, RunModel, list_query, RunModel.created_at, RunModel.id
            )

            # Apply limit
            limit = query.limit or 20
            q = q.limit(limit + 1)  # +1 to check if there are more

            results = q.all()
            return QueryBuilder.build_list_response(results, limit, self._to_pydantic)

    def cancel(self, thread_id: ThreadId, run_id: RunId) -> Run:
        with self._session_factory() as session:
            db_run = (
                session.query(RunModel)
                .filter(
                    RunModel.id == run_id,
                    RunModel.thread_id == thread_id,
                )
                .first()
            )
            if not db_run:
                error_msg = f"Run {run_id} not found in thread {thread_id}"
                raise NotFoundError(error_msg)

            run = self._to_pydantic(db_run)
            if run.status in (
                "cancelled",
                "cancelling",
                "completed",
                "failed",
                "expired",
            ):
                return run

            db_run.tried_cancelling_at = datetime.now(tz=timezone.utc)
            session.commit()
            session.refresh(db_run)
            return self._to_pydantic(db_run)

    @override
    def save(self, run: Run, new: bool = False) -> None:
        with self._session_factory() as session:
            if new:
                # Check if run already exists
                existing_run = (
                    session.query(RunModel)
                    .filter(
                        RunModel.id == run.id,
                        RunModel.thread_id == run.thread_id,
                    )
                    .first()
                )
                if existing_run:
                    error_msg = f"Run {run.id} already exists in thread {run.thread_id}"
                    raise ConflictError(error_msg)

                db_run = RunModel.from_pydantic(run)
                session.add(db_run)
            else:
                db_run = (
                    session.query(RunModel)
                    .filter(
                        RunModel.id == run.id,
                        RunModel.thread_id == run.thread_id,
                    )
                    .first()
                )
                if not db_run:
                    error_msg = f"Run {run.id} not found in thread {run.thread_id}"
                    raise NotFoundError(error_msg)

                # Update fields
                db_run.status = run.status
                db_run.instructions = run.instructions
                db_run.tools = run.tools
                db_run.metadata = run.metadata
                db_run.tried_cancelling_at = run.tried_cancelling_at
                db_run.started_at = run.started_at
                db_run.completed_at = run.completed_at
                db_run.failed_at = run.failed_at
                db_run.expired_at = run.expired_at
                db_run.cancelled_at = run.cancelled_at
                db_run.last_error = run.last_error
                db_run.usage = run.usage

            session.commit()
