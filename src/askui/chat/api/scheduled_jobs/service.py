"""Service for managing scheduled jobs."""

import logging
from datetime import timedelta
from typing import Any
from uuid import UUID

from apscheduler import AsyncScheduler, Schedule
from apscheduler.triggers.date import DateTrigger

from askui.chat.api.models import ScheduledJobId, WorkspaceId
from askui.chat.api.scheduled_jobs.executor import execute_job
from askui.chat.api.scheduled_jobs.models import ScheduledJob, ScheduledJobCreate
from askui.utils.api_utils import ListResponse, NotFoundError

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
        workspace_id: WorkspaceId,
        params: ScheduledJobCreate,
    ) -> ScheduledJob:
        """
        Create a new scheduled job.

        Args:
            workspace_id (WorkspaceId): The workspace this job belongs to.
            params (ScheduledJobCreate): The job creation parameters.

        Returns:
            ScheduledJob: The created scheduled job.
        """
        job = ScheduledJob.create(
            workspace_id=workspace_id,
            params=params,
        )

        # Prepare kwargs for the job callback

        logger.info(
            "Creating scheduled job: id=%s, type=%s, next_fire_time=%s",
            job.id,
            job.data.type,
            job.next_fire_time,
        )

        await self._scheduler.add_schedule(
            func_or_task_id=execute_job,
            trigger=DateTrigger(run_time=job.next_fire_time),
            id=job.id,
            kwargs=job.data.model_dump(mode="json"),
            misfire_grace_time=timedelta(minutes=10),
            job_result_expiration_time=timedelta(weeks=30000),  # Never expire
        )

        logger.info("Scheduled job created: %s", job.id)
        return job

    async def list_(
        self,
        workspace_id: WorkspaceId,
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

        schedules: list[Schedule] = await self._scheduler.data_store.get_schedules(
            {job_id}
        )

        if not schedules:
            msg = f"Scheduled job {job_id} not found"
            raise NotFoundError(msg)

        scheduled_job = ScheduledJob.from_schedule(schedules[0])
        if scheduled_job.data.workspace_id != workspace_id:
            msg = f"Scheduled job {job_id} not found in workspace {workspace_id}"
            raise NotFoundError(msg)

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
