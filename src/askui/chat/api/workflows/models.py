from typing import Annotated, Literal

from pydantic import BaseModel, Field

from askui.chat.api.models import WorkspaceId, WorkspaceResource
from askui.utils.datetime_utils import UnixDatetime, now
from askui.utils.id_utils import IdField, generate_time_ordered_id

WorkflowId = Annotated[str, IdField("wf")]


class WorkflowCreateParams(BaseModel):
    """
    Parameters for creating a workflow via API.
    """

    name: str
    description: str
    tags: list[str] = Field(default_factory=list)


class WorkflowModifyParams(BaseModel):
    """
    Parameters for modifying a workflow via API.
    """

    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None


class Workflow(WorkspaceResource):
    """
    A workflow resource in the chat API.

    Args:
        id (WorkflowId): The id of the workflow. Must start with the 'wf_' prefix and be
            followed by one or more alphanumerical characters.
        object (Literal['workflow']): The object type, always 'workflow'.
        created_at (UnixDatetime): The creation time as a Unix timestamp.
        name (str): The name or title of the workflow.
        description (str): A detailed description of the workflow's purpose and steps.
        tags (list[str], optional): Tags associated with the workflow for filtering or
            categorization. Default is an empty list.
        workspace_id (WorkspaceId | None, optional): The workspace this workflow belongs to.
    """

    id: WorkflowId
    object: Literal["workflow"] = "workflow"
    created_at: UnixDatetime
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)

    @classmethod
    def create(
        cls, workspace_id: WorkspaceId | None, params: WorkflowCreateParams
    ) -> "Workflow":
        return cls(
            id=generate_time_ordered_id("wf"),
            created_at=now(),
            workspace_id=workspace_id,
            **params.model_dump(),
        )

    def modify(self, params: WorkflowModifyParams) -> "Workflow":
        update_data = {k: v for k, v in params.model_dump().items() if v is not None}
        return Workflow.model_validate(
            {
                **self.model_dump(),
                **update_data,
            }
        )
