"""Executor for scheduled job callbacks."""

import logging
import os
from typing import Any

from sqlalchemy.orm import Session

from askui.chat.api.db.engine import engine
from askui.chat.api.messages.dependencies import get_message_service
from askui.chat.api.runs.dependencies import create_run_service
from askui.chat.api.runs.models import RunCreate
from askui.chat.api.scheduled_jobs.models import (
    MessageRerunnerData,
    scheduled_job_data_adapter,
)

_logger = logging.getLogger(__name__)

_ASKUI_TOKEN_ENV_VAR = "ASKUI_TOKEN"
_AUTHORIZATION_HEADER_ENV_VAR = "ASKUI__AUTHORIZATION"


async def execute_job(
    **_kwargs: Any,
) -> None:
    """
    APScheduler callback that creates fresh services and executes the job.

    This function is called by APScheduler when a job fires. It creates fresh
    database sessions and service instances to avoid stale connections.

    Args:
        **_kwargs (Any): Additional keyword arguments (ignored).
    """
    # Validates and returns the correct concrete type based on the `type` discriminator
    job_data = scheduled_job_data_adapter.validate_python(_kwargs)

    _logger.info(
        "Executing scheduled job: workspace=%s, thread=%s",
        job_data.workspace_id,
        job_data.thread_id,
    )

    # future proofing of new job types
    if isinstance(job_data, MessageRerunnerData):  # pyright: ignore[reportUnnecessaryIsInstance]
        # Save previous ASKUI_TOKEN and AUTHORIZATION_HEADER env vars
        _previous_token = os.environ.get(_ASKUI_TOKEN_ENV_VAR)
        _previous_authorization = os.environ.get(_AUTHORIZATION_HEADER_ENV_VAR)

        # remove authorization header since it takes precedence over the token and is set when forwarding bearer token
        del os.environ[_AUTHORIZATION_HEADER_ENV_VAR]
        os.environ[_ASKUI_TOKEN_ENV_VAR] = job_data.askui_token

        await _execute_message_rerunner_job(job_data)

        # Restore previous ASKUI_TOKEN and AUTHORIZATION_HEADER env vars
        if _previous_token is not None:
            os.environ[_ASKUI_TOKEN_ENV_VAR] = _previous_token
        if _previous_authorization is not None:
            os.environ[_AUTHORIZATION_HEADER_ENV_VAR] = _previous_authorization


async def _execute_message_rerunner_job(
    job_data: MessageRerunnerData,
) -> None:
    """
    Execute a message rerunner job.

    Args:
        job_data: The job data.
    """
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
