from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Annotated, cast

from fastapi import APIRouter, Body, HTTPException, Path, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from askui.chat.api.models import ListQuery, ListQueryDep, ListResponse, RunId, ThreadId
from askui.chat.api.runs.service import CreateRunRequest

from .dependencies import RunServiceDep
from .models import Run
from .service import RunService

if TYPE_CHECKING:
    from .runner.events import Events


router = APIRouter(prefix="/threads/{thread_id}/runs", tags=["runs"])


@router.post("")
def create_run(
    thread_id: Annotated[ThreadId, Path(...)],
    request: Annotated[CreateRunRequest, Body(...)],
    run_service: RunService = RunServiceDep,
) -> Response:
    """
    Create a new run for a given thread.
    """
    stream = request.stream
    run_or_async_generator = run_service.create(thread_id, stream, request)
    if stream:
        async_generator = cast(
            "AsyncGenerator[Events, None]",
            run_or_async_generator,
        )

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
    run = cast("Run", run_or_async_generator)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=run.model_dump())


@router.get("/{run_id}")
def retrieve_run(
    run_id: Annotated[RunId, Path(...)],
    run_service: RunService = RunServiceDep,
) -> Run:
    """
    Retrieve a run by its ID.
    """
    try:
        return run_service.retrieve(run_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("")
def list_runs(
    thread_id: Annotated[ThreadId, Path(...)],
    query: ListQuery = ListQueryDep,
    run_service: RunService = RunServiceDep,
) -> ListResponse[Run]:
    """
    List runs, optionally filtered by thread.
    """
    return run_service.list_(thread_id, query=query)


@router.post("/{run_id}/cancel")
def cancel_run(
    run_id: Annotated[RunId, Path(...)],
    run_service: RunService = RunServiceDep,
) -> Run:
    """
    Cancel a run by its ID.
    """
    try:
        return run_service.cancel(run_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
