from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from askui.chat.api.models import ListQuery, ListQueryDep, ListResponse, RunId, ThreadId

from .dependencies import RunStepServiceDep
from .models import RunStep, RunStepId
from .service import RunStepService

router = APIRouter(
    prefix="/threads/{thread_id}/runs/{run_id}/steps", tags=["run-steps"]
)


@router.get("")
def list_run_steps(
    thread_id: Annotated[ThreadId, Path(...)],
    run_id: Annotated[RunId, Path(...)],
    query: ListQuery = ListQueryDep,
    run_step_service: RunStepService = RunStepServiceDep,
) -> ListResponse[RunStep]:
    """List run steps for a run.

    Args:
        thread_id (ThreadId): ID of the thread
        run_id (RunId): ID of the run
        query (ListQuery): Query parameters for listing steps
        run_step_service (RunStepService): Run step service

    Returns:
        ListResponse[RunStep]: List of run steps
    """
    try:
        return run_step_service.list_(
            thread_id=thread_id,
            run_id=run_id,
            query=query,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{step_id}")
def retrieve_run_step(
    thread_id: Annotated[ThreadId, Path(...)],
    run_id: Annotated[RunId, Path(...)],
    step_id: Annotated[RunStepId, Path(...)],
    run_step_service: RunStepService = RunStepServiceDep,
) -> RunStep:
    """Retrieve a run step.

    Args:
        thread_id (ThreadId): ID of the thread
        run_id (RunId): ID of the run
        step_id (RunStepId): ID of the step
        run_step_service (RunStepService): Run step service

    Returns:
        RunStep: Run step

    Raises:
        HTTPException: If step doesn't exist
    """
    try:
        return run_step_service.retrieve(
            thread_id=thread_id,
            run_id=run_id,
            step_id=step_id,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
