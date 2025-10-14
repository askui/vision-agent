from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, Field

from askui.chat.migrations.shared.models import UnixDatetimeV1, WorkspaceIdV1


def add_prefix(id_: str) -> str:
    if id_.startswith("asst_"):
        return id_
    return f"asst_{id_}"


AssistantIdV1 = Annotated[
    str, Field(pattern=r"^asst_[a-z0-9]+$"), BeforeValidator(add_prefix)
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
