from typing import Literal

from pydantic import BaseModel, Field

from askui.chat.api.models import AssistantId, WorkspaceId, WorkspaceResource
from askui.utils.datetime_utils import UnixDatetime, now
from askui.utils.id_utils import generate_time_ordered_id
from askui.utils.not_given import NOT_GIVEN, BaseModelWithNotGiven, NotGiven


class AssistantBase(BaseModel):
    """Base assistant model."""

    name: str | None = None
    description: str | None = None
    avatar: str | None = None
    tools: list[str] = Field(default_factory=list)
    system: str | None = None


class AssistantCreateParams(AssistantBase):
    """Parameters for creating an assistant."""


class AssistantModifyParams(BaseModelWithNotGiven):
    """Parameters for modifying an assistant."""

    name: str | NotGiven = NOT_GIVEN
    description: str | NotGiven = NOT_GIVEN
    avatar: str | NotGiven = NOT_GIVEN
    tools: list[str] | NotGiven = NOT_GIVEN
    system: str | NotGiven = NOT_GIVEN


class Assistant(AssistantBase, WorkspaceResource):
    """An assistant that can be used in a thread."""

    id: AssistantId
    object: Literal["assistant"] = "assistant"
    created_at: UnixDatetime

    @classmethod
    def create(
        cls, workspace_id: WorkspaceId, params: AssistantCreateParams
    ) -> "Assistant":
        return cls(
            id=generate_time_ordered_id("asst"),
            created_at=now(),
            workspace_id=workspace_id,
            **params.model_dump(),
        )

    def modify(self, params: AssistantModifyParams) -> "Assistant":
        return Assistant.model_validate(
            {
                **self.model_dump(),
                **params.model_dump(),
            }
        )
