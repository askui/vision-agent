from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Header, Query, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from askui.chat.api.dependencies import ListQueryDep
from askui.chat.api.models import ThreadId, WorkspaceId
from askui.chat.api.workflow_executions.dependencies import ExecutionServiceDep
from askui.chat.api.workflow_executions.models import (
    WorkflowExecution,
    WorkflowExecutionCreateParams,
    WorkflowExecutionId,
)
from askui.chat.api.workflow_executions.service import ExecutionService
from askui.chat.api.workflows.models import WorkflowId
from askui.utils.api_utils import ListQuery, ListResponse

router = APIRouter(prefix="/workflow-executions", tags=["workflow-executions"])


@router.get("/")
def list_workflow_executions(
    askui_workspace: Annotated[WorkspaceId, Header()],
    query: ListQuery = ListQueryDep,
    workflow_id: Annotated[WorkflowId | None, Query()] = None,
    thread_id: Annotated[ThreadId | None, Query()] = None,
    execution_service: ExecutionService = ExecutionServiceDep,
) -> ListResponse[WorkflowExecution]:
    """List executions with optional filtering by workflow and/or thread."""
    return execution_service.list_(
        workspace_id=askui_workspace,
        query=query,
        workflow_id=workflow_id,
        thread_id=thread_id,
    )


@router.post("/")
async def create_workflow_execution(
    askui_workspace: Annotated[WorkspaceId, Header()],
    params: WorkflowExecutionCreateParams,
    background_tasks: BackgroundTasks,
    execution_service: ExecutionService = ExecutionServiceDep,
) -> WorkflowExecution:
    """Create a new workflow execution."""
    execution, async_generator = await execution_service.create(
        workspace_id=askui_workspace, params=params
    )

    async def _run_async_generator() -> None:
        async for _ in async_generator:
            pass

    background_tasks.add_task(_run_async_generator)
    return execution


@router.get("/{execution_id}")
def retrieve_workflow_execution(
    askui_workspace: Annotated[WorkspaceId, Header()],
    execution_id: WorkflowExecutionId,
    execution_service: ExecutionService = ExecutionServiceDep,
) -> WorkflowExecution:
    """Retrieve a specific execution by ID."""
    return execution_service.retrieve(
        workspace_id=askui_workspace, execution_id=execution_id
    )
