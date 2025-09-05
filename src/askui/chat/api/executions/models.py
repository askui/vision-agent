import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from askui.chat.api.models import ExecutionId, ThreadId, WorkspaceId, WorkspaceResource
from askui.chat.api.workflows.models import WorkflowId
from askui.utils.datetime_utils import now
from askui.utils.id_utils import generate_time_ordered_id
from askui.utils.not_given import NOT_GIVEN, BaseModelWithNotGiven, NotGiven


class ExecutionStatus(str, Enum):
    """The current status of the workflow execution."""

    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"
    ERROR = "error"
    INCOMPLETE = "incomplete"
    SKIPPED = "skipped"
    INDETERMINATE = "indeterminate"


class ExecutionCreateParams(BaseModel):
    """
    Parameters for creating an execution via API.
    """

    workflow: WorkflowId
    thread: ThreadId
    status: ExecutionStatus = ExecutionStatus.PENDING


class ExecutionModifyParams(BaseModelWithNotGiven):
    """
    Parameters for modifying an execution via API.
    Only status can be updated.
    """

    status: ExecutionStatus | NotGiven = NOT_GIVEN


class Execution(WorkspaceResource):
    """
    A workflow execution resource in the chat API.

    Args:
        id (ExecutionId): The id of the execution. Must start with the 'exec_' prefix and be
            followed by one or more alphanumerical characters.
        object (Literal['execution']): The object type, always 'execution'.
        created_at (datetime.datetime): The creation time as a datetime.
        workflow (WorkflowId): The id of the workflow being executed. Must start with the 'wf_' prefix.
        thread (ThreadId): The id of the thread this execution is associated with. Must start with the 'thread_' prefix.
        status (ExecutionStatus): The current status of the workflow execution.
        workspace_id (WorkspaceId | None, optional): The workspace this execution belongs to.
    """

    id: ExecutionId
    object: Literal["execution"] = "execution"
    created_at: datetime.datetime
    workflow: WorkflowId
    thread: ThreadId
    status: ExecutionStatus = Field(
        ..., description="The current status of the workflow execution."
    )

    @classmethod
    def create(
        cls, workspace_id: WorkspaceId | None, params: ExecutionCreateParams
    ) -> "Execution":
        return cls(
            id=generate_time_ordered_id("exec"),
            created_at=now(),
            workspace_id=workspace_id,
            **params.model_dump(),
        )

    def modify(self, params: ExecutionModifyParams) -> "Execution":
        update_data = {
            k: v for k, v in params.model_dump().items() if v is not NOT_GIVEN
        }
        return Execution.model_validate(
            {
                **self.model_dump(),
                **update_data,
            }
        )
