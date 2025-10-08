from typing import Callable

from askui.chat.api.db.query_builder import QueryBuilder
from askui.chat.api.models import WorkspaceId
from askui.chat.api.workflows.models import WorkflowModel, WorkflowTagModel
from askui.chat.api.workflows.schemas import (
    Workflow,
    WorkflowCreateParams,
    WorkflowId,
    WorkflowModifyParams,
)
from askui.utils.api_utils import ForbiddenError, ListQuery, ListResponse, NotFoundError
from sqlalchemy.orm import Session


class WorkflowService:
    """Service for managing Workflow resources with SQLAlchemy persistence."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def _to_pydantic(self, db_model: WorkflowModel) -> Workflow:
        """Convert SQLAlchemy model to Pydantic model."""
        return db_model.to_pydantic()

    def list_(
        self,
        workspace_id: WorkspaceId | None,
        query: ListQuery,
        tags: list[str] | None = None,
    ) -> ListResponse[Workflow]:
        with self._session_factory() as session:
            q = session.query(WorkflowModel)

            # Filter by workspace
            if workspace_id is not None:
                q = q.filter(WorkflowModel.workspace_id == str(workspace_id))
            else:
                q = q.filter(WorkflowModel.workspace_id.is_(None))

            # Filter by tags if specified
            if tags:
                q = q.join(WorkflowTagModel).filter(WorkflowTagModel.tag.in_(tags))

            # Apply list query parameters
            q = QueryBuilder.apply_list_query(
                q, WorkflowModel, query, WorkflowModel.created_at, WorkflowModel.id
            )

            # Apply limit
            limit = query.limit or 20
            q = q.limit(limit + 1)  # +1 to check if there are more

            results = q.all()
            return QueryBuilder.build_list_response(results, limit, self._to_pydantic)

    def retrieve(
        self, workspace_id: WorkspaceId | None, workflow_id: WorkflowId
    ) -> Workflow:
        with self._session_factory() as session:
            db_workflow = (
                session.query(WorkflowModel)
                .filter(WorkflowModel.id == workflow_id)
                .first()
            )
            if not db_workflow:
                error_msg = f"Workflow {workflow_id} not found"
                raise NotFoundError(error_msg)

            # Check workspace access
            if not (
                db_workflow.workspace_id is None
                or db_workflow.workspace_id == str(workspace_id)
            ):
                error_msg = f"Workflow {workflow_id} not found"
                raise NotFoundError(error_msg)

            return self._to_pydantic(db_workflow)

    def create(
        self, workspace_id: WorkspaceId | None, params: WorkflowCreateParams
    ) -> Workflow:
        with self._session_factory() as session:
            db_workflow = WorkflowModel.from_create_params(params, workspace_id)
            session.add(db_workflow)
            session.commit()
            session.refresh(db_workflow)

            # Add tags
            if params.tags:
                for tag in params.tags:
                    db_tag = WorkflowTagModel(
                        workflow_id=db_workflow.id,
                        tag=tag,
                    )
                    session.add(db_tag)

            session.commit()
            return self._to_pydantic(db_workflow)

    def modify(
        self,
        workspace_id: WorkspaceId | None,
        workflow_id: WorkflowId,
        params: WorkflowModifyParams,
    ) -> Workflow:
        with self._session_factory() as session:
            db_workflow = (
                session.query(WorkflowModel)
                .filter(WorkflowModel.id == workflow_id)
                .first()
            )
            if not db_workflow:
                error_msg = f"Workflow {workflow_id} not found"
                raise NotFoundError(error_msg)

            # Check workspace access
            if not (
                db_workflow.workspace_id is None
                or db_workflow.workspace_id == str(workspace_id)
            ):
                error_msg = f"Workflow {workflow_id} not found"
                raise NotFoundError(error_msg)

            if db_workflow.workspace_id is None:
                error_msg = f"Default workflow {workflow_id} cannot be modified"
                raise ForbiddenError(error_msg)

            # Update fields
            if params.name is not None:
                db_workflow.name = params.name
            if params.description is not None:
                db_workflow.description = params.description
            if params.steps is not None:
                db_workflow.steps = params.steps

            # Update tags if provided
            if params.tags is not None:
                # Remove existing tags
                session.query(WorkflowTagModel).filter(
                    WorkflowTagModel.workflow_id == workflow_id
                ).delete()

                # Add new tags
                for tag in params.tags:
                    db_tag = WorkflowTagModel(
                        workflow_id=workflow_id,
                        tag=tag,
                    )
                    session.add(db_tag)

            session.commit()
            session.refresh(db_workflow)
            return self._to_pydantic(db_workflow)

    def delete(
        self,
        workspace_id: WorkspaceId | None,
        workflow_id: WorkflowId,
        force: bool = False,
    ) -> None:
        with self._session_factory() as session:
            db_workflow = (
                session.query(WorkflowModel)
                .filter(WorkflowModel.id == workflow_id)
                .first()
            )
            if not db_workflow:
                error_msg = f"Workflow {workflow_id} not found"
                if not force:
                    raise NotFoundError(error_msg)
                return

            # Check workspace access
            if not (
                db_workflow.workspace_id is None
                or db_workflow.workspace_id == str(workspace_id)
            ):
                error_msg = f"Workflow {workflow_id} not found"
                if not force:
                    raise NotFoundError(error_msg)
                return

            if db_workflow.workspace_id is None and not force:
                error_msg = f"Default workflow {workflow_id} cannot be deleted"
                raise ForbiddenError(error_msg)

            # Delete related tags (cascade will handle this)
            session.delete(db_workflow)
            session.commit()
            session.commit()
