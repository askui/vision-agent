"""API router for scheduled jobs."""

from typing import Annotated

from fastapi import APIRouter, Header, status

from askui.chat.api.dependencies import ListQueryDep
from askui.chat.api.models import ScheduledJobId, WorkspaceId
from askui.chat.api.scheduled_jobs.dependencies import ScheduledJobServiceDep
from askui.chat.api.scheduled_jobs.models import (
    MessageRerunnerData,
    ScheduledJob,
    ScheduledJobCreate,
)
from askui.chat.api.scheduled_jobs.service import ScheduledJobService
from askui.utils.api_utils import ListQuery, ListResponse

router = APIRouter(prefix="/scheduled-jobs", tags=["scheduled-jobs"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_scheduled_job(
    askui_workspace: Annotated[WorkspaceId, Header()],
    params: ScheduledJobCreate,
    scheduled_job_service: ScheduledJobService = ScheduledJobServiceDep,
) -> ScheduledJob:
    """Create a new scheduled job."""
    # Inject workspace_id into the data
    data = MessageRerunnerData(
        workspace_id=askui_workspace,
        thread_id=params.data.thread_id,
        assistant_id=params.data.assistant_id,
        model=params.data.model,
        message=params.data.message,
    )

    return await scheduled_job_service.create(
        workspace_id=askui_workspace,
        next_fire_time=params.next_fire_time,
        data=data,
    )


@router.get("")
async def list_scheduled_jobs(
    askui_workspace: Annotated[WorkspaceId, Header()],
    query: ListQuery = ListQueryDep,
    scheduled_job_service: ScheduledJobService = ScheduledJobServiceDep,
) -> ListResponse[ScheduledJob]:
    """List scheduled jobs with optional status filter."""
    return await scheduled_job_service.list_(
        workspace_id=askui_workspace,
        query=query,
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_scheduled_job(
    askui_workspace: Annotated[WorkspaceId, Header()],
    job_id: ScheduledJobId,
    scheduled_job_service: ScheduledJobService = ScheduledJobServiceDep,
) -> None:
    """
    Cancel a scheduled job.

    Only works for jobs with status 'pending'. Removes the job from the scheduler.
    Cancelled jobs have no history (they are simply removed).

    Raises:
        NotFoundError: If the job is not found or already executed.
    """
    await scheduled_job_service.cancel(
        workspace_id=askui_workspace,
        job_id=job_id,
    )
