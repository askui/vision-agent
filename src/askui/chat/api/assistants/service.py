from typing import Callable

from askui.chat.api.assistants.models import AssistantModel
from askui.chat.api.assistants.schemas import (
    Assistant,
    AssistantCreateParams,
    AssistantModifyParams,
)
from askui.chat.api.assistants.seeds import SEEDS
from askui.chat.api.db.query_builder import QueryBuilder
from askui.chat.api.models import AssistantId, WorkspaceId
from askui.utils.api_utils import ForbiddenError, ListQuery, ListResponse, NotFoundError
from askui.utils.not_given import NOT_GIVEN
from sqlalchemy.orm import Session


class AssistantService:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def _to_pydantic(self, db_model: AssistantModel) -> Assistant:
        """Convert SQLAlchemy model to Pydantic model."""
        return db_model.to_pydantic()

    def list_(
        self, workspace_id: WorkspaceId | None, query: ListQuery
    ) -> ListResponse[Assistant]:
        with self._session_factory() as session:
            q = session.query(AssistantModel)

            # Filter by workspace
            if workspace_id is not None:
                q = q.filter(AssistantModel.workspace_id == str(workspace_id))
            else:
                q = q.filter(AssistantModel.workspace_id.is_(None))

            # Apply list query parameters
            q = QueryBuilder.apply_list_query(
                q, AssistantModel, query, AssistantModel.created_at, AssistantModel.id
            )

            # Apply limit
            limit = query.limit or 20
            q = q.limit(limit + 1)  # +1 to check if there are more

            results = q.all()
            return QueryBuilder.build_list_response(results, limit, self._to_pydantic)

    def retrieve(
        self, workspace_id: WorkspaceId | None, assistant_id: AssistantId
    ) -> Assistant:
        with self._session_factory() as session:
            db_assistant = (
                session.query(AssistantModel)
                .filter(AssistantModel.id == assistant_id)
                .first()
            )
            if not db_assistant:
                error_msg = f"Assistant {assistant_id} not found"
                raise NotFoundError(error_msg)

            # Check workspace access
            if not (
                db_assistant.workspace_id is None
                or db_assistant.workspace_id == str(workspace_id)
            ):
                error_msg = f"Assistant {assistant_id} not found"
                raise NotFoundError(error_msg)

            return self._to_pydantic(db_assistant)

    def create(
        self, workspace_id: WorkspaceId, params: AssistantCreateParams
    ) -> Assistant:
        with self._session_factory() as session:
            db_assistant = AssistantModel.from_create_params(params, workspace_id)
            session.add(db_assistant)
            session.commit()
            session.refresh(db_assistant)

            return self._to_pydantic(db_assistant)

    def modify(
        self,
        workspace_id: WorkspaceId,
        assistant_id: AssistantId,
        params: AssistantModifyParams,
    ) -> Assistant:
        with self._session_factory() as session:
            db_assistant = (
                session.query(AssistantModel)
                .filter(AssistantModel.id == assistant_id)
                .first()
            )
            if not db_assistant:
                error_msg = f"Assistant {assistant_id} not found"
                raise NotFoundError(error_msg)

            # Check workspace access
            if not (
                db_assistant.workspace_id is None
                or db_assistant.workspace_id == str(workspace_id)
            ):
                error_msg = f"Assistant {assistant_id} not found"
                raise NotFoundError(error_msg)

            if db_assistant.workspace_id is None:
                error_msg = f"Default assistant {assistant_id} cannot be modified"
                raise ForbiddenError(error_msg)

            # Update fields
            if params.name is not NOT_GIVEN:
                db_assistant.name = params.name
            if params.description is not NOT_GIVEN:
                db_assistant.description = params.description
            if params.avatar is not NOT_GIVEN:
                db_assistant.avatar = params.avatar
            if params.tools is not NOT_GIVEN:
                db_assistant.tools = params.tools
            if params.system is not NOT_GIVEN:
                db_assistant.system = params.system

            session.commit()
            session.refresh(db_assistant)

            return self._to_pydantic(db_assistant)

    def delete(
        self,
        workspace_id: WorkspaceId | None,
        assistant_id: AssistantId,
        force: bool = False,
    ) -> None:
        with self._session_factory() as session:
            db_assistant = (
                session.query(AssistantModel)
                .filter(AssistantModel.id == assistant_id)
                .first()
            )

            if not db_assistant:
                if not force:
                    error_msg = f"Assistant {assistant_id} not found"
                    raise NotFoundError(error_msg)
                return

            # Check workspace access
            if not (
                db_assistant.workspace_id is None
                or db_assistant.workspace_id == str(workspace_id)
            ):
                if not force:
                    error_msg = f"Assistant {assistant_id} not found"
                    raise NotFoundError(error_msg)
                return

            if db_assistant.workspace_id is None and not force:
                error_msg = f"Default assistant {assistant_id} cannot be deleted"
                raise ForbiddenError(error_msg)

            session.delete(db_assistant)
            session.commit()

    def seed(self) -> None:
        """Seed the assistant service with default assistants."""
        with self._session_factory() as session:
            for seed in SEEDS:
                # Check if already exists
                existing = (
                    session.query(AssistantModel)
                    .filter(AssistantModel.id == seed.id)
                    .first()
                )

                if existing:
                    # Update existing
                    existing.name = seed.name
                    existing.description = seed.description
                    existing.avatar = seed.avatar
                    existing.tools = seed.tools
                    existing.system = seed.system
                else:
                    # Create new
                    db_assistant = AssistantModel(
                        id=seed.id,
                        workspace_id=None,  # Default assistants have no workspace
                        created_at=seed.created_at,
                        name=seed.name,
                        description=seed.description,
                        avatar=seed.avatar,
                        tools=seed.tools,
                        system=seed.system,
                    )
                    session.add(db_assistant)

            session.commit()
            session.commit()
