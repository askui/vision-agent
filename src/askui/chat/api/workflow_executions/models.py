import datetime
from typing import Literal

from pydantic import BaseModel

from askui.chat.api.models import (
    RunId,
    ThreadId,
    WorkflowExecutionId,
    WorkspaceId,
    WorkspaceResource,
)
from askui.chat.api.workflows.models import WorkflowId
from askui.utils.datetime_utils import now
from askui.utils.id_utils import generate_time_ordered_id


class WorkflowExecutionCreateParams(BaseModel):
    """
    Parameters for creating a workflow execution via API.
    """

    workflow_id: WorkflowId


class WorkflowExecution(WorkspaceResource):
    """
    A workflow execution resource in the chat API.

    Args:
        id (WorkflowExecutionId): The id of the execution. Must start with the 'exec_' prefix and be
            followed by one or more alphanumerical characters.
        object (Literal['execution']): The object type, always 'execution'.
        created_at (datetime.datetime): The creation time as a datetime.
        workflow (WorkflowId): The id of the workflow being executed. Must start with the 'wf_' prefix.
        thread (ThreadId): The id of the thread this execution is associated with. Must start with the 'thread_' prefix.
        status (ExecutionStatus): The current status of the workflow execution.
        workspace_id (WorkspaceId | None, optional): The workspace this execution belongs to.
    """

    id: WorkflowExecutionId
    object: Literal["workflow_execution"] = "workflow_execution"
    created_at: datetime.datetime
    workflow_id: WorkflowId
    thread_id: ThreadId
    run_id: RunId

    @classmethod
    def create(
        cls,
        workspace_id: WorkspaceId,
        workflow_id: WorkflowId,
        run_id: RunId,
        thread_id: ThreadId,
    ) -> "WorkflowExecution":
        return cls(
            id=generate_time_ordered_id("wfexec"),
            created_at=now(),
            workspace_id=workspace_id,
            run_id=run_id,
            thread_id=thread_id,
            workflow_id=workflow_id,
        )
