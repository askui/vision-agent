from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    Path,
    Query,
    Response,
    status,
)
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from askui.chat.api.dependencies import ListQueryDep
from askui.chat.api.models import RunId, ThreadId, WorkspaceId
from askui.chat.api.runs.models import RunCreateParams
from askui.chat.api.threads.dependencies import ThreadFacadeDep
from askui.chat.api.threads.facade import ThreadFacade
from askui.utils.api_utils import ListQuery, ListResponse

from .dependencies import RunListQueryDep, RunServiceDep
from .models import Run, RunListQuery, ThreadAndRunCreateParams
from .service import RunService

router = APIRouter(tags=["runs"])


@router.post("/threads/{thread_id}/runs")
async def create_run(
    askui_workspace: Annotated[WorkspaceId, Header()],
    thread_id: Annotated[ThreadId, Path(...)],
    params: RunCreateParams,
    background_tasks: BackgroundTasks,
    thread_facade: ThreadFacade = ThreadFacadeDep,
) -> Response:
    stream = params.stream
    run, async_generator = await thread_facade.create_run(
        workspace_id=askui_workspace, thread_id=thread_id, params=params
    )
    if stream:

        async def sse_event_stream() -> AsyncGenerator[str, None]:
            async for event in async_generator:
                data = (
                    event.data.model_dump_json()
                    if isinstance(event.data, BaseModel)
                    else event.data
                )
                yield f"event: {event.event}\ndata: {data}\n\n"

        return StreamingResponse(
            status_code=status.HTTP_201_CREATED,
            content=sse_event_stream(),
            media_type="text/event-stream",
        )

    async def _run_async_generator() -> None:
        async for _ in async_generator:
            pass

    background_tasks.add_task(_run_async_generator)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=run.model_dump())


@router.post("/runs")
async def create_thread_and_run(
    askui_workspace: Annotated[WorkspaceId, Header()],
    params: ThreadAndRunCreateParams,
    background_tasks: BackgroundTasks,
    thread_facade: ThreadFacade = ThreadFacadeDep,
) -> Response:
    stream = params.stream
    run, async_generator = await thread_facade.create_thread_and_run(
        workspace_id=askui_workspace, params=params
    )
    if stream:

        async def sse_event_stream() -> AsyncGenerator[str, None]:
            async for event in async_generator:
                data = (
                    event.data.model_dump_json()
                    if isinstance(event.data, BaseModel)
                    else event.data
                )
                yield f"event: {event.event}\ndata: {data}\n\n"

        return StreamingResponse(
            status_code=status.HTTP_201_CREATED,
            content=sse_event_stream(),
            media_type="text/event-stream",
        )

    async def _run_async_generator() -> None:
        async for _ in async_generator:
            pass

    background_tasks.add_task(_run_async_generator)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=run.model_dump())


@router.get("/threads/{thread_id}/runs/{run_id}")
async def retrieve_run(
    thread_id: Annotated[ThreadId, Path(...)],
    run_id: Annotated[RunId, Path(...)],
    stream: Annotated[bool, Query()] = False,
    run_service: RunService = RunServiceDep,
) -> Response:
    if not stream:
        return JSONResponse(
            content=run_service.retrieve(thread_id, run_id).model_dump(),
        )

    async def sse_event_stream() -> AsyncGenerator[str, None]:
        async for event in run_service.retrieve_stream(thread_id, run_id):
            data = (
                event.data.model_dump_json()
                if isinstance(event.data, BaseModel)
                else event.data
            )
            yield f"event: {event.event}\ndata: {data}\n\n"

    return StreamingResponse(
        content=sse_event_stream(),
        media_type="text/event-stream",
    )


@router.get("/runs")
async def list_runs(
    query: RunListQuery = RunListQueryDep,
    thread_facade: ThreadFacade = ThreadFacadeDep,
) -> ListResponse[Run]:
    return thread_facade.list_runs(query=query)


@router.post("/threads/{thread_id}/runs/{run_id}/cancel")
def cancel_run(
    thread_id: Annotated[ThreadId, Path(...)],
    run_id: Annotated[RunId, Path(...)],
    run_service: RunService = RunServiceDep,
) -> Run:
    return run_service.cancel(thread_id, run_id)
