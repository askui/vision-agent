from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    HTTPException,
    Path,
    Response,
    status,
)
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from askui.chat.api.models import ListQueryDep, RunId, ThreadId
from askui.chat.api.runs.service import CreateRunRequest
from askui.utils.api_utils import ListQuery, ListResponse

from .dependencies import RunServiceDep
from .models import Run
from .service import RunService

router = APIRouter(prefix="/threads/{thread_id}/runs", tags=["runs"])


@router.post("")
async def create_run(
    thread_id: Annotated[ThreadId, Path(...)],
    request: Annotated[CreateRunRequest, Body(...)],
    background_tasks: BackgroundTasks,
    run_service: RunService = RunServiceDep,
) -> Response:
    """
    Create a new run for a given thread.
    """
    stream = request.stream
    run, async_generator = await run_service.create(thread_id, request)
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
async def retrieve_run(
    thread_id: ThreadId,
    run_id: RunId,
    run_service: RunService = RunServiceDep,
) -> Run:
    """Get a run by ID."""
    return await run_service.find_one(thread_id=thread_id, run_id=run_id)


@router.get("")
async def list_runs(
    thread_id: ThreadId,
    query: ListQuery = ListQueryDep,
    run_service: RunService = RunServiceDep,
) -> ListResponse[Run]:
    """List runs for a thread."""
    return await run_service.find(thread_id=thread_id, query=query)


@router.post("/{run_id}/cancel")
async def cancel_run(
    run_id: Annotated[RunId, Path(...)],
    run_service: RunService = RunServiceDep,
) -> Run:
    """
    Cancel a run by its ID.
    """
    try:
        return await run_service.cancel(run_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
