from datetime import timedelta
from typing import Literal

from pydantic import BaseModel, computed_field

from askui.chat.api.models import AssistantId, RunId, ThreadId
from askui.chat.api.threads.models import ThreadCreateParams
from askui.utils.api_utils import Resource
from askui.utils.datetime_utils import UnixDatetime, now
from askui.utils.id_utils import generate_time_ordered_id

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
    """Error information for a failed run."""

    message: str
    code: Literal["server_error", "rate_limit_exceeded", "invalid_prompt"]


class RunBase(BaseModel):
    """Base run model."""

    assistant_id: AssistantId


class RunCreateParams(RunBase):
    """Parameters for creating a run."""

    stream: bool = False


class ThreadAndRunCreateParams(RunCreateParams):
    thread: ThreadCreateParams


class Run(RunBase, Resource):
    """A run execution within a thread."""

    id: RunId
    object: Literal["thread.run"] = "thread.run"
    thread_id: ThreadId
    created_at: UnixDatetime
    expires_at: UnixDatetime
    started_at: UnixDatetime | None = None
    completed_at: UnixDatetime | None = None
    failed_at: UnixDatetime | None = None
    cancelled_at: UnixDatetime | None = None
    tried_cancelling_at: UnixDatetime | None = None
    last_error: RunError | None = None

    @classmethod
    def create(cls, thread_id: ThreadId, params: RunCreateParams) -> "Run":
        return cls(
            id=generate_time_ordered_id("run"),
            thread_id=thread_id,
            created_at=now(),
            expires_at=now() + timedelta(minutes=10),
            **params.model_dump(exclude={"stream"}),
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def status(self) -> RunStatus:
        if self.cancelled_at:
            return "cancelled"
        if self.failed_at:
            return "failed"
        if self.completed_at:
            return "completed"
        if self.expires_at and self.expires_at < now():
            return "expired"
        if self.tried_cancelling_at:
            return "cancelling"
        if self.started_at:
            return "in_progress"
        return "queued"

    def start(self) -> None:
        self.started_at = now()
        self.expires_at = now() + timedelta(minutes=10)

    def ping(self) -> None:
        self.expires_at = now() + timedelta(minutes=10)

    def complete(self) -> None:
        self.completed_at = now()

    def cancel(self) -> None:
        self.cancelled_at = now()

    def fail(self, error: RunError) -> None:
        self.failed_at = now()
        self.last_error = error
