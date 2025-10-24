from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, Field

from askui.chat.migrations.shared.models import UnixDatetimeV1, WorkspaceIdV1
from askui.chat.migrations.shared.utils import build_prefixer

ThreadIdV1 = Annotated[
    str, Field(pattern=r"^thread_[a-z0-9]+$"), BeforeValidator(build_prefixer("thread"))
]


class ThreadV1(BaseModel):
    id: ThreadIdV1
    object: Literal["thread"] = "thread"
    created_at: UnixDatetimeV1
    name: str | None = None
    workspace_id: WorkspaceIdV1 = Field(exclude=True)

    def to_db_dict(self) -> dict[str, Any]:
        return {
            **self.model_dump(exclude={"id", "object"}),
            "id": self.id.removeprefix("thread_"),
            "workspace_id": self.workspace_id.hex,
        }
