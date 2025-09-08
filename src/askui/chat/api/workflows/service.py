from pathlib import Path
from typing import Callable

from askui.chat.api.models import WorkspaceId
from askui.chat.api.utils import build_workspace_filter_fn
from askui.chat.api.workflows.models import (
    Workflow,
    WorkflowCreateParams,
    WorkflowId,
    WorkflowModifyParams,
)
from askui.utils.api_utils import (
    ConflictError,
    ListQuery,
    ListResponse,
    NotFoundError,
    list_resources,
)


def _build_workflow_filter_fn(
    workspace_id: WorkspaceId | None,
    tags: list[str] | None = None,
) -> Callable[[Workflow], bool]:
    workspace_filter: Callable[[Workflow], bool] = build_workspace_filter_fn(
        workspace_id, Workflow
    )

    def filter_fn(workflow: Workflow) -> bool:
        if not workspace_filter(workflow):
            return False
        if tags is not None:
            return any(tag in workflow.tags for tag in tags)
        return True

    return filter_fn


class WorkflowService:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._workflows_dir = base_dir / "workflows"

    def _get_workflow_path(self, workflow_id: WorkflowId, new: bool = False) -> Path:
        workflow_path = self._workflows_dir / f"{workflow_id}.json"
        exists = workflow_path.exists()
        if new and exists:
            error_msg = f"Workflow {workflow_id} already exists"
            raise ConflictError(error_msg)
        if not new and not exists:
            error_msg = f"Workflow {workflow_id} not found"
            raise NotFoundError(error_msg)
        return workflow_path

    def list_(
        self,
        workspace_id: WorkspaceId | None,
        query: ListQuery,
        tags: list[str] | None = None,
    ) -> ListResponse[Workflow]:
        return list_resources(
            base_dir=self._workflows_dir,
            query=query,
            resource_type=Workflow,
            filter_fn=_build_workflow_filter_fn(workspace_id, tags=tags),
        )

    def retrieve(
        self, workspace_id: WorkspaceId | None, workflow_id: WorkflowId
    ) -> Workflow:
        try:
            workflow_path = self._get_workflow_path(workflow_id)
            workflow = Workflow.model_validate_json(workflow_path.read_text())

            # Check workspace access
            if workspace_id is not None and workflow.workspace_id != workspace_id:
                error_msg = f"Workflow {workflow_id} not found"
                raise NotFoundError(error_msg)

        except FileNotFoundError as e:
            error_msg = f"Workflow {workflow_id} not found"
            raise NotFoundError(error_msg) from e
        else:
            return workflow

    def create(
        self, workspace_id: WorkspaceId | None, params: WorkflowCreateParams
    ) -> Workflow:
        workflow = Workflow.create(workspace_id, params)
        self._save(workflow, new=True)
        return workflow

    def modify(
        self,
        workspace_id: WorkspaceId | None,
        workflow_id: WorkflowId,
        params: WorkflowModifyParams,
    ) -> Workflow:
        workflow = self.retrieve(workspace_id, workflow_id)
        modified = workflow.modify(params)
        self._save(modified)
        return modified

    def _save(self, workflow: Workflow, new: bool = False) -> None:
        self._workflows_dir.mkdir(parents=True, exist_ok=True)
        workflow_file = self._get_workflow_path(workflow.id, new=new)
        workflow_file.write_text(workflow.model_dump_json(), encoding="utf-8")
