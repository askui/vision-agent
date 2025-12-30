from typing import Literal, Union

from apscheduler import Schedule
from apscheduler.triggers.date import DateTrigger
from pydantic import BaseModel, Field, TypeAdapter

from askui.chat.api.messages.models import ROOT_MESSAGE_PARENT_ID, MessageCreate
from askui.chat.api.models import (
    AssistantId,
    MessageId,
    ScheduledJobId,
    ThreadId,
    WorkspaceId,
)
from askui.utils.datetime_utils import UnixDatetime
from askui.utils.id_utils import generate_time_ordered_id


class ScheduledMessageCreate(MessageCreate):
    """
    Message creation parameters for scheduled jobs.

    Extends `MessageCreate` with required `parent_id` to ensure the message
    is added to the correct branch in the conversation tree, since the thread
    state may change between scheduling and execution.

    Args:
        parent_id (MessageId): The parent message ID for branching.
            Required for scheduled messages. Use `ROOT_MESSAGE_PARENT_ID` to
            create a new root branch.
    """

    parent_id: MessageId = Field(default=ROOT_MESSAGE_PARENT_ID)  # pyright: ignore


# =============================================================================
# API Input Models (without workspace_id - injected from header)
# =============================================================================


class _BaseMessageRerunnerDataCreate(BaseModel):
    """
    API input data for the message_rerunner job type.

    This job type creates a new message in a thread and executes a run
    at the scheduled time.

    Args:
        type (ScheduledJobType): The type of the scheduled job.
        thread_id (ThreadId): The thread to add the message to.
        assistant_id (AssistantId): The assistant to run.
        model (str): The model to use for the run.
        message (ScheduledMessageCreate): The message to create.
    """

    type: Literal["message_rerunner"] = "message_rerunner"
    thread_id: ThreadId
    assistant_id: AssistantId
    model: str
    message: ScheduledMessageCreate


class ScheduledJobCreate(BaseModel):
    """
    API input data for scheduled job creation.

    Args:
        next_fire_time (UnixDatetime): The time when the job should execute.
        data (ScheduledJobData): The data for the job.
    """

    next_fire_time: UnixDatetime
    data: _BaseMessageRerunnerDataCreate


# =============================================================================
# Internal Models (with workspace_id - populated after injection)
# =============================================================================


class MessageRerunnerData(_BaseMessageRerunnerDataCreate):
    """
    Internal data for the message_rerunner job type.

    Extends `MessageRerunnerDataCreate` with required `workspace_id` that is
    injected from the request header.

    Args:
        workspace_id (WorkspaceId): The workspace this job belongs to.
    """

    workspace_id: WorkspaceId


# Discriminated union of all job data types (extensible for future types)
ScheduledJobData = Union[MessageRerunnerData]

scheduled_job_data_adapter: TypeAdapter[ScheduledJobData] = TypeAdapter(
    ScheduledJobData
)


class ScheduledJob(BaseModel):
    """
    A scheduled job that will execute at a specified time.

    Maps to APScheduler's `Schedule` structure for easy conversion.

    Args:
        id (ScheduledJobId): Unique identifier for the scheduled job.
            Maps to `Schedule.id`.
        next_fire_time (UnixDatetime): When the job is scheduled to execute.
            Maps to `Schedule.next_fire_time` or `Schedule.trigger.run_time`.
        data (ScheduledJobData): Type-specific job data. Always contains `type` and
            `workspace_id`. Maps to `Schedule.kwargs`.
        object (Literal["scheduled_job"]): Object type identifier.
    """

    id: ScheduledJobId
    object: Literal["scheduled_job"] = "scheduled_job"
    next_fire_time: UnixDatetime
    data: ScheduledJobData

    @classmethod
    def create(
        cls, workspace_id: WorkspaceId, params: ScheduledJobCreate
    ) -> "ScheduledJob":
        """Create a new ScheduledJob with a generated ID."""
        return cls(
            id=generate_time_ordered_id("schedjob"),
            next_fire_time=params.next_fire_time,
            data=MessageRerunnerData(
                workspace_id=workspace_id,
                thread_id=params.data.thread_id,
                assistant_id=params.data.assistant_id,
                model=params.data.model,
                message=params.data.message,
            ),
        )

    @classmethod
    def from_schedule(cls, schedule: Schedule) -> "ScheduledJob":
        """
        Create a ScheduledJob from an APScheduler Schedule.

        Args:
            schedule (Schedule): The APScheduler schedule to convert.

        Returns:
            ScheduledJob: The converted scheduled job.

        Raises:
            ValueError: If the schedule has no determinable `next_fire_time`.
        """
        # Extract next_fire_time from schedule or trigger
        next_fire_time: UnixDatetime
        if schedule.next_fire_time is not None:
            next_fire_time = schedule.next_fire_time
        elif isinstance(schedule.trigger, DateTrigger):
            next_fire_time = schedule.trigger.run_time
        else:
            error_msg = f"Schedule {schedule.id} has no next_fire_time"
            raise ValueError(error_msg)

        # Reconstruct data from kwargs
        data = MessageRerunnerData.model_validate(schedule.kwargs or {})

        return cls(
            id=schedule.id,
            next_fire_time=next_fire_time,
            data=data,
        )
