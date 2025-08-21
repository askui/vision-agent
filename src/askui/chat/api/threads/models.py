from typing import Literal

from pydantic import BaseModel

from askui.chat.api.messages.models import MessageCreateParams
from askui.chat.api.models import ThreadId
from askui.utils.api_utils import Resource
from askui.utils.datetime_utils import UnixDatetime, now
from askui.utils.id_utils import generate_time_ordered_id
from askui.utils.not_given import NOT_GIVEN, BaseModelWithNotGiven, NotGiven


class ThreadBase(BaseModel):
    """Base thread model."""

    name: str | None = None


class ThreadCreateParams(ThreadBase):
    """Parameters for creating a thread."""

    messages: list[MessageCreateParams] | None = None


class ThreadModifyParams(BaseModelWithNotGiven):
    """Parameters for modifying a thread."""

    name: str | None | NotGiven = NOT_GIVEN


class Thread(ThreadBase, Resource):
    """A chat thread/session."""

    id: ThreadId
    object: Literal["thread"] = "thread"
    created_at: UnixDatetime

    @classmethod
    def create(cls, params: ThreadCreateParams) -> "Thread":
        return cls(
            id=generate_time_ordered_id("thread"),
            created_at=now(),
            **params.model_dump(exclude={"messages"}),
        )

    def modify(self, params: ThreadModifyParams) -> "Thread":
        return Thread.model_validate(
            {
                **self.model_dump(),
                **params.model_dump(),
            }
        )
