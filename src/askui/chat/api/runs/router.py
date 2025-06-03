from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path
from pydantic import BaseModel

from .dependencies import RunServiceDep
from .service import Run, RunListResponse, RunService


class CreateRunRequest(BaseModel):
    stream: bool = False


router = APIRouter(prefix="/threads/{thread_id}/runs", tags=["runs"])


@router.post("")
def create_run(
    thread_id: Annotated[str, Path(...)],
    request: Annotated[CreateRunRequest, Body(...)],
    run_service: RunService = RunServiceDep,
) -> Run:
    """
    Create a new run for a given thread.
    """
    return run_service.create(thread_id, request.stream)


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
