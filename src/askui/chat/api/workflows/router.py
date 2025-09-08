from typing import Annotated

from fastapi import APIRouter, Header, Path, Query, status

from askui.chat.api.dependencies import ListQueryDep
from askui.chat.api.models import WorkspaceId
from askui.chat.api.workflows.dependencies import WorkflowServiceDep
from askui.chat.api.workflows.models import (
    Workflow,
    WorkflowCreateParams,
    WorkflowId,
    WorkflowModifyParams,
)
from askui.chat.api.workflows.service import WorkflowService
from askui.utils.api_utils import ListQuery, ListResponse

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("")
def list_workflows(
    askui_workspace: Annotated[WorkspaceId | None, Header()],
    tags: Annotated[list[str] | None, Query()] = None,
    query: ListQuery = ListQueryDep,
    workflow_service: WorkflowService = WorkflowServiceDep,
) -> ListResponse[Workflow]:
    """
    List workflows with optional tag filtering.

    Args:
        askui_workspace: The workspace ID from header
        tags: Optional list of tags to filter by
        query: Standard list query parameters (limit, after, before, order)
        workflow_service: Injected workflow service

    Returns:
        ListResponse containing workflows matching the criteria
    """
    return workflow_service.list_(workspace_id=askui_workspace, query=query, tags=tags)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_workflow(
    askui_workspace: Annotated[WorkspaceId | None, Header()],
    params: WorkflowCreateParams,
    workflow_service: WorkflowService = WorkflowServiceDep,
) -> Workflow:
    """
    Create a new workflow.

    Args:
        askui_workspace: The workspace ID from header
        params: Workflow creation parameters (name, description, tags)
        workflow_service: Injected workflow service

    Returns:
        The created workflow
    """
    return workflow_service.create(workspace_id=askui_workspace, params=params)


@router.get("/{workflow_id}")
def retrieve_workflow(
    askui_workspace: Annotated[WorkspaceId | None, Header()],
    workflow_id: Annotated[WorkflowId, Path(...)],
    workflow_service: WorkflowService = WorkflowServiceDep,
) -> Workflow:
    """
    Retrieve a specific workflow by ID.

    Args:
        askui_workspace: The workspace ID from header
        workflow_id: The workflow ID to retrieve
        workflow_service: Injected workflow service

    Returns:
        The requested workflow

    Raises:
        NotFoundError: If workflow doesn't exist or user doesn't have access
    """
    return workflow_service.retrieve(
        workspace_id=askui_workspace, workflow_id=workflow_id
    )


@router.patch("/{workflow_id}")
def modify_workflow(
    askui_workspace: Annotated[WorkspaceId | None, Header()],
    workflow_id: Annotated[WorkflowId, Path(...)],
    params: WorkflowModifyParams,
    workflow_service: WorkflowService = WorkflowServiceDep,
) -> Workflow:
    """
    Modify an existing workflow.

    Args:
        askui_workspace: The workspace ID from header
        workflow_id: The workflow ID to modify
        params: Workflow modification parameters (name, description, tags)
        workflow_service: Injected workflow service

    Returns:
        The modified workflow

    Raises:
        NotFoundError: If workflow doesn't exist or user doesn't have access
    """
    return workflow_service.modify(
        workspace_id=askui_workspace, workflow_id=workflow_id, params=params
    )
