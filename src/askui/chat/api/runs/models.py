from datetime import datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel, Field, computed_field

from askui.chat.api.models import AssistantId, RunId, ThreadId, UnixDatetime
from askui.chat.api.utils import generate_time_ordered_id

RunStatus = Literal[
    "queued",
    "in_progress",
    "completed",
    "cancelling",
    "cancelled",
    "failed",
    "expired",
]


class RunError(BaseModel):
    message: str
    code: Literal["server_error", "rate_limit_exceeded", "invalid_prompt"]


class Run(BaseModel):
    assistant_id: AssistantId
    cancelled_at: UnixDatetime | None = None
    completed_at: UnixDatetime | None = None
    created_at: UnixDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    expires_at: UnixDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc) + timedelta(minutes=10)
    )
    failed_at: UnixDatetime | None = None
    id: RunId = Field(default_factory=lambda: generate_time_ordered_id("run"))
    last_error: RunError | None = None
    object: Literal["thread.run"] = "thread.run"
    started_at: UnixDatetime | None = None
    thread_id: ThreadId
    tried_cancelling_at: UnixDatetime | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def status(self) -> RunStatus:
        if self.cancelled_at:
            return "cancelled"
        if self.failed_at:
            return "failed"
        if self.completed_at:
            return "completed"
        if self.expires_at and self.expires_at < datetime.now(tz=timezone.utc):
            return "expired"
        if self.tried_cancelling_at:
            return "cancelling"
        if self.started_at:
            return "in_progress"
        return "queued"
