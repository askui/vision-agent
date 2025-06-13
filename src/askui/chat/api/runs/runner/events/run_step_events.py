from typing import Literal

from pydantic import BaseModel

from askui.chat.api.run_steps.models import RunStep, RunStepDetails, RunStepId
from askui.chat.api.runs.runner.events.event_base import EventBase


class RunStepDeltaDelta(BaseModel):
    step_details: RunStepDetails


class RunStepDelta(BaseModel):
    id: RunStepId
    object: Literal["thread.run.step.delta"] = "thread.run.step.delta"
    delta: RunStepDeltaDelta


class RunStepDeltaEvent(EventBase):
    """Event for run step delta."""

    event: Literal["thread.run.step.delta"] = "thread.run.step.delta"
    data: RunStepDelta


class RunStepEvent(EventBase):
    """Event for run step status changes."""

    data: RunStep
    event: Literal[
        "thread.run.step.cancelled",
        "thread.run.step.completed",
        "thread.run.step.created",
        "thread.run.step.expired",
        "thread.run.step.failed",
        "thread.run.step.in_progress",
    ]
