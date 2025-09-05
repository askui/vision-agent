from typing import Annotated

from fastapi import APIRouter, Header, Query

from askui.chat.api.dependencies import ListQueryDep
from askui.chat.api.executions.dependencies import ExecutionServiceDep
from askui.chat.api.executions.models import (
    Execution,
    ExecutionCreateParams,
    ExecutionId,
    ExecutionModifyParams,
)
from askui.chat.api.executions.service import ExecutionService
from askui.chat.api.models import ThreadId, WorkspaceId
from askui.chat.api.workflows.models import WorkflowId
from askui.utils.api_utils import ListQuery, ListResponse

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("/")
def list_executions(
    askui_workspace: Annotated[WorkspaceId, Header()],
    query: ListQuery = ListQueryDep,
    workflow_id: Annotated[WorkflowId | None, Query()] = None,
    thread_id: Annotated[ThreadId | None, Query()] = None,
    execution_service: ExecutionService = ExecutionServiceDep,
) -> ListResponse[Execution]:
    """List executions with optional filtering by workflow and/or thread."""
    return execution_service.list_(
        workspace_id=askui_workspace,
        query=query,
        workflow_id=workflow_id,
        thread_id=thread_id,
    )


@router.post("/")
def create_execution(
    askui_workspace: Annotated[WorkspaceId, Header()],
    params: ExecutionCreateParams,
    execution_service: ExecutionService = ExecutionServiceDep,
) -> Execution:
    """Create a new workflow execution."""
    return execution_service.create(workspace_id=askui_workspace, params=params)


@router.get("/{execution_id}")
def retrieve_execution(
    askui_workspace: Annotated[WorkspaceId, Header()],
    execution_id: ExecutionId,
    execution_service: ExecutionService = ExecutionServiceDep,
) -> Execution:
    """Retrieve a specific execution by ID."""
    return execution_service.retrieve(
        workspace_id=askui_workspace, execution_id=execution_id
    )


@router.patch("/{execution_id}")
def modify_execution(
    askui_workspace: Annotated[WorkspaceId, Header()],
    execution_id: ExecutionId,
    params: ExecutionModifyParams,
    execution_service: ExecutionService = ExecutionServiceDep,
) -> Execution:
    """Update an existing execution (only status can be modified)."""
    return execution_service.modify(
        workspace_id=askui_workspace,
        execution_id=execution_id,
        params=params,
    )
