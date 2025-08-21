from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Body, Path, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from askui.chat.api.models import ListQueryDep, RunId, ThreadId
from askui.chat.api.runs.models import RunCreateParams
from askui.utils.api_utils import ListQuery, ListResponse

from .dependencies import RunServiceDep
from .models import Run
from .service import RunService

router = APIRouter(prefix="/threads/{thread_id}/runs", tags=["runs"])


@router.post("")
async def create_run(
    thread_id: Annotated[ThreadId, Path(...)],
    params: RunCreateParams,
    background_tasks: BackgroundTasks,
    run_service: RunService = RunServiceDep,
) -> Response:
    stream = params.stream
    run, async_generator = await run_service.create(thread_id, params)
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


@router.get("/{run_id}")
def retrieve_run(
    thread_id: Annotated[ThreadId, Path(...)],
    run_id: Annotated[RunId, Path(...)],
    run_service: RunService = RunServiceDep,
) -> Run:
    return run_service.retrieve(thread_id, run_id)


@router.get("")
def list_runs(
    thread_id: Annotated[ThreadId, Path(...)],
    query: ListQuery = ListQueryDep,
    run_service: RunService = RunServiceDep,
) -> ListResponse[Run]:
    return run_service.list_(thread_id, query=query)


@router.post("/{run_id}/cancel")
def cancel_run(
    thread_id: Annotated[ThreadId, Path(...)],
    run_id: Annotated[RunId, Path(...)],
    run_service: RunService = RunServiceDep,
) -> Run:
    return run_service.cancel(thread_id, run_id)
