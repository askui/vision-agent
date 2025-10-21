from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, Field

from askui.chat.migrations.shared.models import UnixDatetimeV1, WorkspaceIdV1
from askui.chat.migrations.shared.utils import build_prefixer

FileIdV1 = Annotated[
    str, Field(pattern=r"^file_[a-z0-9]+$"), BeforeValidator(build_prefixer("file"))
]


class FileV1(BaseModel):
    id: FileIdV1
    object: Literal["file"] = "file"
    created_at: UnixDatetimeV1
    filename: str = Field(min_length=1)
    size: int = Field(ge=0)
    media_type: str
    workspace_id: WorkspaceIdV1 | None = Field(default=None, exclude=True)

    def to_db_dict(self) -> dict[str, Any]:
        return {
            **self.model_dump(exclude={"id", "object", "workspace_id"}),
            "id": self.id.removeprefix("file_"),
            "workspace_id": str(self.workspace_id) if self.workspace_id else None,
        }
