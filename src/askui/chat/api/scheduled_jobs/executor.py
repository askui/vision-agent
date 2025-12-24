"""Executor for scheduled job callbacks."""

import logging
from typing import Any

from sqlalchemy.orm import Session

from askui.chat.api.db.engine import engine
from askui.chat.api.messages.dependencies import get_message_service
from askui.chat.api.runs.dependencies import create_run_service
from askui.chat.api.runs.models import RunCreate
from askui.chat.api.scheduled_jobs.models import scheduled_job_data_adapter

_logger = logging.getLogger(__name__)


async def execute_job(
    **_kwargs: Any,
) -> None:
    """
    APScheduler callback that creates fresh services and executes the job.

    This function is called by APScheduler when a job fires. It creates fresh
    database sessions and service instances to avoid stale connections.

    Args:
        workspace_id (str): The workspace ID (as string from JSON serialization).
        thread_id (str): The thread ID for the message.
        assistant_id (str): The assistant ID to run.
        model (str): The model to use for the run.
        message (dict[str, Any]): The message data to create.
        **_kwargs (Any): Additional keyword arguments (ignored).

    Returns:
        dict[str, Any]: Result containing the `run_id`.
    """

    # Validates and returns the correct concrete type based on the `type` discriminator
    job_data = scheduled_job_data_adapter.validate_python(_kwargs)

    _logger.info(
        "Executing scheduled job: workspace=%s, thread=%s",
        job_data.workspace_id,
        job_data.thread_id,
    )

    # Create fresh session for this job execution
    with Session(engine) as session:
        message_service = get_message_service(session)
        run_service = create_run_service(session, job_data.workspace_id)

        # Create message
        message_service.create(
            workspace_id=job_data.workspace_id,
            thread_id=job_data.thread_id,
            params=job_data.message,
        )

        # Create and execute run
        _logger.debug("Creating run with assistant %s", job_data.assistant_id)
        run, generator = await run_service.create(
            workspace_id=job_data.workspace_id,
            thread_id=job_data.thread_id,
            params=RunCreate(assistant_id=job_data.assistant_id, model=job_data.model),
        )

        # Consume generator to completion
        _logger.debug("Waiting for run %s to complete", run.id)
        async for _event in generator:
            pass

        _logger.info("Scheduled job completed: run_id=%s", run.id)
