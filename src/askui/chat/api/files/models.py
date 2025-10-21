import mimetypes
from typing import Literal

from pydantic import BaseModel, Field

from askui.chat.api.models import FileId, WorkspaceId, WorkspaceResource
from askui.utils.datetime_utils import UnixDatetime, now
from askui.utils.id_utils import generate_time_ordered_id


class FileBase(BaseModel):
    """Base file model."""

    size: int = Field(description="In bytes", ge=0)
    media_type: str


class FileCreate(FileBase):
    filename: str | None = None


class File(FileBase, WorkspaceResource):
    """A file that can be stored and managed."""

    id: FileId
    object: Literal["file"] = "file"
    created_at: UnixDatetime
    filename: str = Field(min_length=1)

    @classmethod
    def create(cls, workspace_id: WorkspaceId | None, params: FileCreate) -> "File":
        id_ = generate_time_ordered_id("file")
        filename = (
            params.filename or f"{id_}{mimetypes.guess_extension(params.media_type)}"
        )
        return cls(
            id=id_,
            created_at=now(),
            workspace_id=workspace_id,
            filename=filename,
            **params.model_dump(exclude={"filename"}),
        )
