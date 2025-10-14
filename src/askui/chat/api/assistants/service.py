from sqlalchemy import or_
from sqlalchemy.orm import Session

from askui.chat.api.assistants.models import Assistant, AssistantCreate, AssistantModify
from askui.chat.api.assistants.orms import AssistantOrm
from askui.chat.api.db.queries import list_all
from askui.chat.api.models import AssistantId, WorkspaceId
from askui.utils.api_utils import ForbiddenError, ListQuery, ListResponse, NotFoundError


class AssistantService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_(
        self, workspace_id: WorkspaceId | None, query: ListQuery
    ) -> ListResponse[Assistant]:
        q = self._session.query(AssistantOrm).filter(
            or_(
                AssistantOrm.workspace_id == workspace_id,
                AssistantOrm.workspace_id.is_(None),
            ),
        )
        orms: list[AssistantOrm]
        orms, has_more = list_all(q, query, AssistantOrm.id)
        data = [orm.to_model() for orm in orms]
        return ListResponse(
            data=data,
            has_more=has_more,
            first_id=data[0].id if data else None,
            last_id=data[-1].id if data else None,
        )

    def _find_by_id(
        self, workspace_id: WorkspaceId | None, assistant_id: AssistantId
    ) -> AssistantOrm:
        assistant_orm: AssistantOrm | None = (
            self._session.query(AssistantOrm)
            .filter(
                AssistantOrm.id == assistant_id,
                or_(
                    AssistantOrm.workspace_id == workspace_id,
                    AssistantOrm.workspace_id.is_(None),
                ),
            )
            .first()
        )
        if assistant_orm is None:
            error_msg = f"Assistant {assistant_id} not found"
            raise NotFoundError(error_msg)
        return assistant_orm

    def retrieve(
        self, workspace_id: WorkspaceId | None, assistant_id: AssistantId
    ) -> Assistant:
        assistant_model = self._find_by_id(workspace_id, assistant_id)
        return assistant_model.to_model()

    def create(
        self, workspace_id: WorkspaceId | None, params: AssistantCreate
    ) -> Assistant:
        assistant = Assistant.create(workspace_id, params)
        assistant_model = AssistantOrm.from_model(assistant)
        self._session.add(assistant_model)
        self._session.commit()
        return assistant

    def modify(
        self,
        workspace_id: WorkspaceId | None,
        assistant_id: AssistantId,
        params: AssistantModify,
        force: bool = False,
    ) -> Assistant:
        assistant_model = self._find_by_id(workspace_id, assistant_id)
        if assistant_model.workspace_id is None and not force:
            error_msg = f"Default assistant {assistant_id} cannot be modified"
            raise ForbiddenError(error_msg)
        assistant_model.update(params.model_dump())
        self._session.commit()
        self._session.refresh(assistant_model)
        return assistant_model.to_model()

    def delete(
        self,
        workspace_id: WorkspaceId | None,
        assistant_id: AssistantId,
        force: bool = False,
    ) -> None:
        assistant_model = self._find_by_id(workspace_id, assistant_id)
        if assistant_model.workspace_id is None and not force:
            error_msg = f"Default assistant {assistant_id} cannot be deleted"
            raise ForbiddenError(error_msg)
        self._session.delete(assistant_model)
        self._session.commit()
