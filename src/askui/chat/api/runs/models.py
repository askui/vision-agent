from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field

from askui.chat.api.models import (
    MODEL_DEFAULT,
    AssistantId,
    RunId,
    ThreadId,
    UnixDatetime,
)
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
    instructions: str = ""
    last_error: RunError | None = None
    model: str = MODEL_DEFAULT
    object: Literal["thread.run"] = "thread.run"
    parallel_tool_calls: bool = False  # different from OpenAI
    response_format: Literal["auto"] = "auto"
    started_at: UnixDatetime | None = None
    thread_id: ThreadId
    tool_choice: Literal["auto"] = "auto"
    tools: list[Any] = Field(default_factory=list)
    tried_cancelling_at: UnixDatetime | None = None

    @computed_field
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
