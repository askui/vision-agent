"""FastAPI dependencies for scheduled jobs."""

from typing import Any

from fastapi import Depends

from askui.chat.api.scheduled_jobs.scheduler import scheduler
from askui.chat.api.scheduled_jobs.service import ScheduledJobService


def get_scheduled_job_service() -> ScheduledJobService:
    """Get ScheduledJobService instance with the singleton scheduler."""
    return ScheduledJobService(scheduler=scheduler)


ScheduledJobServiceDep = Depends(get_scheduled_job_service)
