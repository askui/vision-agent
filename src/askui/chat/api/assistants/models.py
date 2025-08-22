from typing import Literal

from pydantic import BaseModel

from askui.chat.api.models import AssistantId
from askui.utils.api_utils import Resource
from askui.utils.datetime_utils import UnixDatetime, now
from askui.utils.id_utils import generate_time_ordered_id
from askui.utils.not_given import NOT_GIVEN, BaseModelWithNotGiven, NotGiven


class AssistantBase(BaseModel):
    """Base assistant model."""

    name: str | None = None
    description: str | None = None
    avatar: str | None = None


class AssistantCreateParams(AssistantBase):
    """Parameters for creating an assistant."""


class AssistantModifyParams(BaseModelWithNotGiven):
    """Parameters for modifying an assistant."""

    name: str | NotGiven = NOT_GIVEN
    description: str | NotGiven = NOT_GIVEN
    avatar: str | NotGiven = NOT_GIVEN


class Assistant(AssistantBase, Resource):
    """An assistant that can be used in a thread."""

    id: AssistantId
    object: Literal["assistant"] = "assistant"
    created_at: UnixDatetime

    @classmethod
    def create(cls, params: AssistantCreateParams) -> "Assistant":
        return cls(
            id=generate_time_ordered_id("asst"),
            created_at=now(),
            **params.model_dump(),
        )

    def modify(self, params: AssistantModifyParams) -> "Assistant":
        return Assistant.model_validate(
            {
                **self.model_dump(),
                **params.model_dump(),
            }
        )
