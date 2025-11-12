from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated, Literal

from fastapi import Query
from pydantic import BaseModel, Field, computed_field

from askui.chat.api.models import (
    AssistantId,
    MessageId,
    RunId,
    ThreadId,
    WorkspaceId,
    WorkspaceResource,
)
from askui.chat.api.threads.models import ThreadCreate
from askui.utils.api_utils import ListQuery
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


class RunCreate(BaseModel):
    """Parameters for creating a run."""

    stream: bool = False
    assistant_id: AssistantId
    last_message_id: MessageId


class RunStart(BaseModel):
    """Parameters for starting a run."""

    type: Literal["start"] = "start"
    status: Literal["in_progress"] = "in_progress"
    started_at: UnixDatetime = Field(default_factory=now)
    expires_at: UnixDatetime = Field(
        default_factory=lambda: now() + timedelta(minutes=10)
    )


class RunPing(BaseModel):
    """Parameters for pinging a run."""

    type: Literal["ping"] = "ping"
    expires_at: UnixDatetime = Field(
        default_factory=lambda: now() + timedelta(minutes=10)
    )


class RunComplete(BaseModel):
    """Parameters for completing a run."""

    type: Literal["complete"] = "complete"
    status: Literal["completed"] = "completed"
    completed_at: UnixDatetime = Field(default_factory=now)


class RunTryCancelling(BaseModel):
    """Parameters for trying to cancel a run."""

    type: Literal["try_cancelling"] = "try_cancelling"
    status: Literal["cancelling"] = "cancelling"
    tried_cancelling_at: UnixDatetime = Field(default_factory=now)


class RunCancel(BaseModel):
    """Parameters for canceling a run."""

    type: Literal["cancel"] = "cancel"
    status: Literal["cancelled"] = "cancelled"
    cancelled_at: UnixDatetime = Field(default_factory=now)


class RunFail(BaseModel):
    """Parameters for failing a run."""

    type: Literal["fail"] = "fail"
    status: Literal["failed"] = "failed"
    failed_at: UnixDatetime = Field(default_factory=now)
    last_error: RunError


RunModify = RunStart | RunPing | RunComplete | RunTryCancelling | RunCancel | RunFail


class ThreadAndRunCreate(RunCreate):
    thread: ThreadCreate


def map_status_to_readable_description(status: RunStatus) -> str:
    match status:
        case "queued":
            return "Run has been queued."
        case "in_progress":
            return "Run is in progress."
        case "completed":
            return "Run has been completed."
        case "cancelled":
            return "Run has been cancelled."
        case "failed":
            return "Run has failed."
        case "expired":
            return "Run has expired."
        case "cancelling":
            return "Run is being cancelled."


class Run(WorkspaceResource):
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
    assistant_id: AssistantId | None = None

    @classmethod
    def create(
        cls, workspace_id: WorkspaceId, thread_id: ThreadId, params: RunCreate
    ) -> "Run":
        return cls(
            id=generate_time_ordered_id("run"),
            workspace_id=workspace_id,
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

    def validate_modify(self, params: RunModify) -> None:  #  noqa: C901
        status_description = map_status_to_readable_description(self.status)
        error_msg = status_description
        match params.type:
            case "start":
                if self.status != "queued":
                    error_msg += " Cannot start it (again). Please create a new run."
                    raise ValueError(error_msg)
            case "ping":
                if self.status != "in_progress":
                    error_msg += " Cannot ping. Run is not in progress."
                    raise ValueError(error_msg)
            case "complete":
                if self.status != "in_progress":
                    error_msg += " Cannot complete. Run is not in progress."
                    raise ValueError(error_msg)
            case "try_cancelling":
                if self.status not in ["queued", "in_progress"]:
                    error_msg += " Cannot cancel (again)."
                    if self.status != "cancelling":
                        # I think this just sounds better if this is only added if it
                        # is not being cancelled as it is still in progress while being
                        # cancelled.
                        error_msg += " Run is neither queued nor in progress."
                    raise ValueError(error_msg)
            case "cancel":
                if self.status not in ["queued", "in_progress", "cancelling"]:
                    error_msg += " Cannot cancel. Run is neither queued, in progress, nor has it been tried to be cancelled."
                    raise ValueError(error_msg)
            case "fail":
                if self.status not in ["queued", "in_progress", "cancelling"]:
                    error_msg += " Cannot fail. Run is neither queued, in progress, nor has it been tried to be cancelled."
                    raise ValueError(error_msg)


@dataclass(kw_only=True)
class RunListQuery(ListQuery):
    thread: Annotated[ThreadId | None, Query()] = None
    status: Annotated[list[RunStatus] | None, Query()] = None
