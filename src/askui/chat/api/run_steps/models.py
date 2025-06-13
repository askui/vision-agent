from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, computed_field

from askui.chat.api.models import AssistantId, MessageId, RunId, ThreadId, UnixDatetime
from askui.chat.api.utils import generate_time_ordered_id

RunStepStatus = Literal[
    "in_progress",
    "completed",
    "failed",
    "cancelled",
    "expired",
]


class RunStepError(BaseModel):
    message: str
    code: Literal["server_error", "rate_limit_exceeded"]


class RunStepDetailsMessageCreationMessageCreation(BaseModel):
    """Details about the message creation run step."""

    message_id: MessageId


StepType = Literal["message_creation"]


class RunStepDetailsMessageCreation(BaseModel):
    """Details about the message creation run step."""

    type: StepType = "message_creation"
    message_creation: RunStepDetailsMessageCreationMessageCreation


RunStepDetails = RunStepDetailsMessageCreation
RunStepId = str


class RunStep(BaseModel):
    """A step in a run's execution."""

    assistant_id: AssistantId
    cancelled_at: UnixDatetime | None = None
    completed_at: UnixDatetime | None = None
    created_at: UnixDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    expired_at: UnixDatetime | None = None
    failed_at: UnixDatetime | None = None
    id: RunStepId = Field(default_factory=lambda: generate_time_ordered_id("step"))
    last_error: RunStepError | None = None
    object: Literal["thread.run.step"] = "thread.run.step"
    run_id: RunId
    step_details: RunStepDetails
    thread_id: ThreadId
    type: StepType

    @computed_field
    @property
    def status(self) -> RunStepStatus:
        if self.completed_at:
            return "completed"
        if self.failed_at:
            return "failed"
        if self.cancelled_at:
            return "cancelled"
        if self.expired_at:
            return "expired"
        return "in_progress"
