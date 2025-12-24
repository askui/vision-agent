"""Service for managing scheduled jobs."""

import logging
from datetime import timedelta
from typing import Any
from uuid import UUID

from apscheduler import AsyncScheduler, Schedule
from apscheduler.triggers.date import DateTrigger

from askui.chat.api.models import ScheduledJobId, WorkspaceId
from askui.chat.api.scheduled_jobs.executor import execute_job
from askui.chat.api.scheduled_jobs.models import ScheduledJob, ScheduledJobData
from askui.utils.api_utils import ListQuery, ListResponse, NotFoundError
from askui.utils.datetime_utils import UnixDatetime

logger = logging.getLogger(__name__)


class ScheduledJobService:
    """
    Service for managing scheduled jobs using APScheduler.

    This service provides methods to create, list, and cancel scheduled jobs.
    Job data is stored in APScheduler's SQLAlchemy data store.

    Args:
        scheduler (Any): The APScheduler `AsyncScheduler` instance to use.
    """

    def __init__(self, scheduler: AsyncScheduler) -> None:
        self._scheduler: AsyncScheduler = scheduler

    async def create(
        self,
        workspace_id: WorkspaceId,  # noqa: ARG002
        next_fire_time: UnixDatetime,
        data: ScheduledJobData,
    ) -> ScheduledJob:
        """
        Create a new scheduled job.

        Args:
            workspace_id (WorkspaceId): The workspace this job belongs to.
            next_fire_time (UnixDatetime): When the job should execute.
            data (ScheduledJobData): Type-specific job data.

        Returns:
            ScheduledJob: The created scheduled job.
        """
        job = ScheduledJob.create(
            next_fire_time=next_fire_time,
            data=data,
        )

        # Prepare kwargs for the job callback

        logger.info(
            "Creating scheduled job: id=%s, type=%s, next_fire_time=%s",
            job.id,
            data.type,
            next_fire_time,
        )

        await self._scheduler.add_schedule(
            func_or_task_id=execute_job,
            trigger=DateTrigger(run_time=next_fire_time),
            id=job.id,
            kwargs=data.model_dump(mode="json"),
            misfire_grace_time=timedelta(minutes=10),
            job_result_expiration_time=timedelta(weeks=30000),  # Never expire
        )

        logger.info("Scheduled job created: %s", job.id)
        return job

    async def list_(
        self,
        workspace_id: WorkspaceId,
        query: ListQuery,  # noqa: ARG002
    ) -> ListResponse[ScheduledJob]:
        """
        List pending scheduled jobs.

        Args:
            workspace_id (WorkspaceId): Filter by workspace.
            query (ListQuery): Query parameters.

        Returns:
            ListResponse[ScheduledJob]: Paginated list of pending scheduled jobs.
        """
        jobs = await self._get_pending_jobs(workspace_id)

        # TODO(scheduled-jobs): Implement pagination
        # TODO(scheduled-jobs): Implement sorting

        return ListResponse(
            data=jobs,
            has_more=False,
            first_id=jobs[0].id if jobs else None,
            last_id=jobs[-1].id if jobs else None,
        )

    async def cancel(
        self,
        workspace_id: WorkspaceId,
        job_id: ScheduledJobId,
    ) -> None:
        """
        Cancel a scheduled job.

        This removes the schedule from APScheduler. Only works for pending jobs.

        Args:
            workspace_id (WorkspaceId): The workspace the job belongs to.
            job_id (ScheduledJobId): The job ID to cancel.

        Raises:
            NotFoundError: If the job is not found or already executed.
        """
        logger.info("Canceling scheduled job: %s", job_id)

        schedules: list[Any] = await self._scheduler.data_store.get_schedules({job_id})

        if not schedules:
            error_msg = f"Scheduled job {job_id} not found"
            raise NotFoundError(error_msg)

        schedule: Any = schedules[0]
        kwargs: dict[str, Any] = schedule.kwargs or {}
        schedule_workspace_id: str | None = kwargs.get("workspace_id")
        if schedule_workspace_id is None or UUID(schedule_workspace_id) != workspace_id:
            error_msg = f"Scheduled job {job_id} not found"
            raise NotFoundError(error_msg)

        await self._scheduler.data_store.remove_schedules([job_id])
        logger.info("Scheduled job canceled: %s", job_id)

    async def _get_pending_jobs(self, workspace_id: WorkspaceId) -> list[ScheduledJob]:
        """Get pending jobs from APScheduler schedules."""
        scheduled_jobs: list[ScheduledJob] = []

        schedules: list[Schedule] = await self._scheduler.data_store.get_schedules()

        for schedule in schedules:
            scheduled_job = ScheduledJob.from_schedule(schedule)
            if scheduled_job.data.workspace_id != workspace_id:
                continue
            scheduled_jobs.append(scheduled_job)

        return scheduled_jobs
