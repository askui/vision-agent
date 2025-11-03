from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, Field, computed_field

from askui.chat.migrations.shared.assistants.models import AssistantIdV1
from askui.chat.migrations.shared.models import UnixDatetimeV1, WorkspaceIdV1
from askui.chat.migrations.shared.threads.models import ThreadIdV1
from askui.chat.migrations.shared.utils import build_prefixer, now_v1

RunStatusV1 = Literal[
    "queued",
    "in_progress",
    "completed",
    "cancelling",
    "cancelled",
    "failed",
    "expired",
]


class RunErrorV1(BaseModel):
    """Error information for a failed run."""

    message: str
    code: Literal["server_error", "rate_limit_exceeded", "invalid_prompt"]


RunIdV1 = Annotated[
    str, Field(pattern=r"^run_[a-z0-9]+$"), BeforeValidator(build_prefixer("run"))
]


class RunV1(BaseModel):
    id: RunIdV1
    object: Literal["thread.run"] = "thread.run"
    thread_id: ThreadIdV1
    created_at: UnixDatetimeV1
    expires_at: UnixDatetimeV1
    started_at: UnixDatetimeV1 | None = None
    completed_at: UnixDatetimeV1 | None = None
    failed_at: UnixDatetimeV1 | None = None
    cancelled_at: UnixDatetimeV1 | None = None
    tried_cancelling_at: UnixDatetimeV1 | None = None
    last_error: RunErrorV1 | None = None
    assistant_id: AssistantIdV1 | None = None
    workspace_id: WorkspaceIdV1 = Field(exclude=True)

    def to_db_dict(self) -> dict[str, Any]:
        return {
            **self.model_dump(exclude={"id", "thread_id", "assistant_id", "object"}),
            "id": self.id.removeprefix("run_"),
            "thread_id": self.thread_id.removeprefix("thread_"),
            "assistant_id": self.assistant_id.removeprefix("asst_")
            if self.assistant_id
            else None,
            "workspace_id": self.workspace_id.hex,
        }

    @computed_field  # type: ignore[prop-decorator]
    @property
    def status(self) -> RunStatusV1:
        if self.cancelled_at:
            return "cancelled"
        if self.failed_at:
            return "failed"
        if self.completed_at:
            return "completed"
        if self.expires_at and self.expires_at < now_v1():
            return "expired"
        if self.tried_cancelling_at:
            return "cancelling"
        if self.started_at:
            return "in_progress"
        return "queued"
