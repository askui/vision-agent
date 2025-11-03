from typing import Literal

from pydantic import BaseModel

from askui.chat.api.messages.models import MessageCreate
from askui.chat.api.models import ThreadId, WorkspaceId, WorkspaceResource
from askui.utils.datetime_utils import UnixDatetime, now
from askui.utils.id_utils import generate_time_ordered_id
from askui.utils.not_given import NOT_GIVEN, BaseModelWithNotGiven, NotGiven


class ThreadBase(BaseModel):
    """Base thread model."""

    name: str | None = None


class ThreadCreate(ThreadBase):
    """Parameters for creating a thread."""

    messages: list[MessageCreate] | None = None


class ThreadModify(BaseModelWithNotGiven):
    """Parameters for modifying a thread."""

    name: str | None | NotGiven = NOT_GIVEN


class Thread(ThreadBase, WorkspaceResource):
    """A chat thread/session."""

    id: ThreadId
    object: Literal["thread"] = "thread"
    created_at: UnixDatetime

    @classmethod
    def create(cls, workspace_id: WorkspaceId, params: ThreadCreate) -> "Thread":
        return cls(
            id=generate_time_ordered_id("thread"),
            created_at=now(),
            workspace_id=workspace_id,
            **params.model_dump(exclude={"messages"}),
        )
