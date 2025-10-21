from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, Field

from askui.chat.migrations.shared.models import UnixDatetimeV1, WorkspaceIdV1
from askui.chat.migrations.shared.utils import build_prefixer

AssistantIdV1 = Annotated[
    str, Field(pattern=r"^asst_[a-z0-9]+$"), BeforeValidator(build_prefixer("asst"))
]


class AssistantV1(BaseModel):
    id: AssistantIdV1
    object: Literal["assistant"] = "assistant"
    created_at: UnixDatetimeV1
    workspace_id: WorkspaceIdV1 | None = None
    name: str | None = None
    description: str | None = None
    avatar: str | None = None
    tools: list[str] = Field(default_factory=list)
    system: str | None = None

    def to_db_dict(self) -> dict[str, Any]:
        return {
            **self.model_dump(exclude={"id", "object", "workspace_id"}),
            "id": self.id.removeprefix("asst_"),
            "workspace_id": str(self.workspace_id) if self.workspace_id else None,
        }
