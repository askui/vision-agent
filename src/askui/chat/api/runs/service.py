from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import anyio
from sqlalchemy import ColumnElement, or_
from sqlalchemy.orm import Session
from typing_extensions import override

from askui.chat.api.assistants.service import AssistantService
from askui.chat.api.db.queries import list_all
from askui.chat.api.mcp_clients.manager import McpClientManagerManager
from askui.chat.api.messages.chat_history_manager import ChatHistoryManager
from askui.chat.api.models import RunId, ThreadId, WorkspaceId
from askui.chat.api.runs.events.events import DoneEvent, ErrorEvent, Event, RunEvent
from askui.chat.api.runs.events.service import EventService
from askui.chat.api.runs.models import (
    Run,
    RunCreate,
    RunListQuery,
    RunModify,
    RunStatus,
)
from askui.chat.api.runs.orms import RunOrm
from askui.chat.api.runs.runner.runner import Runner, RunnerRunService
from askui.chat.api.settings import Settings
from askui.utils.api_utils import ListResponse, NotFoundError


class RunService(RunnerRunService):
    """Service for managing Run resources with database persistence."""

    def __init__(
        self,
        session: Session,
        assistant_service: AssistantService,
        mcp_client_manager_manager: McpClientManagerManager,
        chat_history_manager: ChatHistoryManager,
        settings: Settings,
    ) -> None:
        self._session = session
        self._assistant_service = assistant_service
        self._mcp_client_manager_manager = mcp_client_manager_manager
        self._chat_history_manager = chat_history_manager
        self._settings = settings
        self._event_service = EventService(settings.data_dir, self)

    def _find_by_id(
        self, workspace_id: WorkspaceId | None, thread_id: ThreadId, run_id: RunId
    ) -> RunOrm:
        """Find run by ID."""
        run_orm: RunOrm | None = (
            self._session.query(RunOrm)
            .filter(
                RunOrm.id == run_id,
                RunOrm.thread_id == thread_id,
                RunOrm.workspace_id == workspace_id,
            )
            .first()
        )
        if run_orm is None:
            error_msg = f"Run {run_id} not found in thread {thread_id}"
            raise NotFoundError(error_msg)
        return run_orm

    def _create(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, params: RunCreate
    ) -> Run:
        """Create a new run."""
        run = Run.create(workspace_id, thread_id, params)
        run_orm = RunOrm.from_model(run)
        self._session.add(run_orm)
        self._session.commit()
        return run

    async def create(
        self,
        workspace_id: WorkspaceId,
        thread_id: ThreadId,
        params: RunCreate,
    ) -> tuple[Run, AsyncGenerator[Event, None]]:
        assistant = self._assistant_service.retrieve(
            workspace_id=workspace_id, assistant_id=params.assistant_id
        )
        run = self._create(workspace_id, thread_id, params)
        send_stream, receive_stream = anyio.create_memory_object_stream[Event]()
        runner = Runner(
            run_id=run.id,
            thread_id=thread_id,
            workspace_id=workspace_id,
            assistant=assistant,
            chat_history_manager=self._chat_history_manager,
            mcp_client_manager_manager=self._mcp_client_manager_manager,
            run_service=self,
            settings=self._settings,
            model=params.model,
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
    def modify(
        self,
        workspace_id: WorkspaceId,
        thread_id: ThreadId,
        run_id: RunId,
        params: RunModify,
    ) -> Run:
        run_orm = self._find_by_id(workspace_id, thread_id, run_id)
        run = run_orm.to_model()
        run.validate_modify(params)
        run_orm.update(params.model_dump(exclude={"type"}))
        self._session.commit()
        self._session.refresh(run_orm)
        return run_orm.to_model()

    @override
    def retrieve(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, run_id: RunId
    ) -> Run:
        """Retrieve run by ID."""
        run_orm = self._find_by_id(workspace_id, thread_id, run_id)
        return run_orm.to_model()

    async def retrieve_stream(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, run_id: RunId
    ) -> AsyncGenerator[Event, None]:
        async with self._event_service.create_reader(
            workspace_id=workspace_id, thread_id=thread_id, run_id=run_id
        ) as event_reader:
            async for event in event_reader.read_events():
                yield event

    def _build_status_condition(self, status: RunStatus) -> ColumnElement[bool]:
        match status:
            case "expired":
                return (RunOrm.status == "expired") | (
                    (RunOrm.status.in_(["queued", "in_progress", "cancelling"]))
                    & (RunOrm.expires_at < datetime.now(tz=timezone.utc))
                )
            case _:
                return RunOrm.status == status

    def list_(
        self, workspace_id: WorkspaceId, query: RunListQuery
    ) -> ListResponse[Run]:
        """List runs with pagination and filtering."""
        q = self._session.query(RunOrm).filter(RunOrm.workspace_id == workspace_id)

        if query.thread:
            q = q.filter(RunOrm.thread_id == query.thread)

        if query.status:
            status_conditions = [
                self._build_status_condition(status) for status in query.status
            ]
            q = q.filter(or_(*status_conditions))

        orms: list[RunOrm]
        orms, has_more = list_all(q, query, RunOrm.id)
        data = [orm.to_model() for orm in orms]
        return ListResponse(
            data=data,
            has_more=has_more,
            first_id=data[0].id if data else None,
            last_id=data[-1].id if data else None,
        )
