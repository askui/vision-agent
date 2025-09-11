from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Callable

from askui.chat.api.executions.models import (
    Execution,
    ExecutionCreateParams,
    ExecutionId,
    ExecutionModifyParams,
)
from askui.chat.api.messages.models import MessageCreateParams
from askui.chat.api.models import ThreadId, WorkspaceId
from askui.chat.api.runs.models import ThreadAndRunCreateParams
from askui.chat.api.runs.runner.events.events import Events
from askui.chat.api.threads.facade import ThreadFacade
from askui.chat.api.threads.models import ThreadCreateParams
from askui.chat.api.utils import build_workspace_filter_fn
from askui.chat.api.workflows.models import WorkflowId
from askui.chat.api.workflows.service import WorkflowService
from askui.utils.api_utils import (
    ConflictError,
    ListQuery,
    ListResponse,
    NotFoundError,
    list_resources,
)


def _build_execution_filter_fn(
    workspace_id: WorkspaceId,
    workflow_id: WorkflowId | None = None,
    thread_id: ThreadId | None = None,
) -> Callable[[Execution], bool]:
    """Build filter function for executions with optional workflow and thread filters."""
    workspace_filter: Callable[[Execution], bool] = build_workspace_filter_fn(
        workspace_id, Execution
    )

    def filter_fn(execution: Execution) -> bool:
        if not workspace_filter(execution):
            return False
        if workflow_id is not None and execution.workflow_id != workflow_id:
            return False
        if thread_id is not None and execution.thread_id != thread_id:
            return False
        return True

    return filter_fn


class ExecutionService:
    """Service for managing Execution resources with filesystem persistence."""

    def __init__(
        self,
        base_dir: Path,
        workflow_service: WorkflowService,
        thread_facade: ThreadFacade,
    ) -> None:
        self._base_dir = base_dir
        self._executions_dir = base_dir / "executions"
        self._workflow_service = workflow_service
        self._thread_facade = thread_facade

    def _get_execution_path(self, execution_id: ExecutionId, new: bool = False) -> Path:
        """Get the file path for an execution."""
        execution_path = self._executions_dir / f"{execution_id}.json"
        exists = execution_path.exists()
        if new and exists:
            error_msg = f"Execution {execution_id} already exists"
            raise ConflictError(error_msg)
        if not new and not exists:
            error_msg = f"Execution {execution_id} not found"
            raise NotFoundError(error_msg)
        return execution_path

    def list_(
        self,
        workspace_id: WorkspaceId,
        query: ListQuery,
        workflow_id: WorkflowId | None = None,
        thread_id: ThreadId | None = None,
    ) -> ListResponse[Execution]:
        """List executions with optional filtering by workflow and/or thread."""
        return list_resources(
            base_dir=self._executions_dir,
            query=query,
            resource_type=Execution,
            filter_fn=_build_execution_filter_fn(workspace_id, workflow_id, thread_id),
        )

    def retrieve(
        self, workspace_id: WorkspaceId, execution_id: ExecutionId
    ) -> Execution:
        """Retrieve a specific execution by ID."""
        try:
            execution_path = self._get_execution_path(execution_id)
            execution = Execution.model_validate_json(execution_path.read_text())

            # Check workspace access - allow if workspace_id is None (global access)
            # or if execution workspace matches or execution has no workspace
            if (
                workspace_id is not None
                and execution.workspace_id is not None
                and execution.workspace_id != workspace_id
            ):
                error_msg = f"Execution {execution_id} not found"
                raise NotFoundError(error_msg)

        except FileNotFoundError as e:
            error_msg = f"Execution {execution_id} not found"
            raise NotFoundError(error_msg) from e
        else:
            return execution

    async def create(
        self, workspace_id: WorkspaceId, params: ExecutionCreateParams
    ) -> tuple[Execution, AsyncGenerator[Events, None]]:
        """Create a new execution."""
        # Validate that the workflow exists in the same workspace
        workflow = self._workflow_service.retrieve(workspace_id, params.workflow_id)

        # Create a thread and a run
        run, async_generator = await self._thread_facade.create_thread_and_run(
            workspace_id,
            ThreadAndRunCreateParams(
                assistant_id=workflow.assistant_id,
                thread=ThreadCreateParams(
                    name=workflow.name,
                    messages=[
                        MessageCreateParams(role="user", content=workflow.description)
                    ],
                ),
            ),
        )

        execution = Execution.create(
            workspace_id, params.workflow_id, run.id, run.thread_id
        )
        self._save(execution, new=True)
        return execution, async_generator

    def modify(
        self,
        workspace_id: WorkspaceId,
        execution_id: ExecutionId,
        params: ExecutionModifyParams,
    ) -> Execution:
        """Update an existing execution (only status can be modified)."""
        execution = self.retrieve(workspace_id, execution_id)
        modified = execution.modify(params)
        self._save(modified)
        return modified

    def _save(self, execution: Execution, new: bool = False) -> None:
        """Save execution to filesystem."""
        self._executions_dir.mkdir(parents=True, exist_ok=True)
        execution_file = self._get_execution_path(execution.id, new=new)
        execution_file.write_text(execution.model_dump_json(), encoding="utf-8")
