from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Annotated, cast

from fastapi import APIRouter, Body, HTTPException, Path, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

if TYPE_CHECKING:
    from askui.chat.api.messages.service import MessageEvent

from .dependencies import RunServiceDep
from .service import Run, RunEvent, RunListResponse, RunService


class CreateRunRequest(BaseModel):
    stream: bool = False


router = APIRouter(prefix="/threads/{thread_id}/runs", tags=["runs"])


@router.post("")
def create_run(
    thread_id: Annotated[str, Path(...)],
    request: Annotated[CreateRunRequest, Body(...)],
    run_service: RunService = RunServiceDep,
) -> Response:
    """
    Create a new run for a given thread.
    """
    stream = request.stream
    run_or_async_generator = run_service.create(thread_id, stream)
    if stream:
        async_generator = cast(
            "AsyncGenerator[RunEvent | MessageEvent, None]", run_or_async_generator
        )

        async def sse_event_stream() -> AsyncGenerator[str, None]:
            async for event in async_generator:
                yield f"event: {event.event}\ndata: {event.model_dump_json()}\n\n"

        return StreamingResponse(
            status_code=status.HTTP_201_CREATED,
            content=sse_event_stream(),
            media_type="text/event-stream",
        )
    run = cast("Run", run_or_async_generator)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=run.model_dump())


@router.get("/{run_id}")
def retrieve_run(
    run_id: Annotated[str, Path(...)],
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
    thread_id: Annotated[str, Path(...)],
    run_service: RunService = RunServiceDep,
) -> RunListResponse:
    """
    List runs, optionally filtered by thread.
    """
    return run_service.list_(thread_id)


@router.post("/{run_id}/cancel")
def cancel_run(
    run_id: Annotated[str, Path(...)],
    run_service: RunService = RunServiceDep,
) -> Run:
    """
    Cancel a run by its ID.
    """
    try:
        return run_service.cancel(run_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
