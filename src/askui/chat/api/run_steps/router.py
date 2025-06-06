from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path

from .dependencies import RunStepServiceDep
from .service import RunStep, RunStepListResponse, RunStepService

router = APIRouter(
    prefix="/threads/{thread_id}/runs/{run_id}/steps", tags=["run-steps"]
)


@router.get("")
def list_run_steps(
    thread_id: Annotated[str, Path(...)],
    run_id: Annotated[str, Path(...)],
    limit: int | None = None,
    after: str | None = None,
    before: str | None = None,
    order: Literal["asc", "desc"] = "desc",
    run_step_service: RunStepService = RunStepServiceDep,
) -> RunStepListResponse:
    """List run steps for a run.

    Args:
        thread_id: ID of the thread
        run_id: ID of the run
        limit: Optional maximum number of steps to return
        after: Optional step ID after which steps are returned
        before: Optional step ID before which steps are returned
        run_step_service: Run step service

    Returns:
        List of run steps
    """
    try:
        return run_step_service.list_(
            thread_id=thread_id,
            run_id=run_id,
            limit=limit,
            after=after,
            before=before,
            order=order,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{step_id}")
def retrieve_run_step(
    thread_id: Annotated[str, Path(...)],
    run_id: Annotated[str, Path(...)],
    step_id: Annotated[str, Path(...)],
    run_step_service: RunStepService = RunStepServiceDep,
) -> RunStep:
    """Retrieve a run step.

    Args:
        thread_id: ID of the thread
        run_id: ID of the run
        step_id: ID of the step
        run_step_service: Run step service

    Returns:
        Run step

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
