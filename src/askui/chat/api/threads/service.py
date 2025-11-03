from sqlalchemy.orm import Session

from askui.chat.api.db.queries import list_all
from askui.chat.api.models import ThreadId, WorkspaceId
from askui.chat.api.threads.models import Thread, ThreadCreate, ThreadModify
from askui.chat.api.threads.orms import ThreadOrm
from askui.utils.api_utils import ListQuery, ListResponse, NotFoundError


class ThreadService:
    """Service for managing Thread resources with database persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _find_by_id(self, workspace_id: WorkspaceId, thread_id: ThreadId) -> ThreadOrm:
        """Find thread by ID."""
        thread_orm: ThreadOrm | None = (
            self._session.query(ThreadOrm)
            .filter(
                ThreadOrm.id == thread_id,
                ThreadOrm.workspace_id == workspace_id,
            )
            .first()
        )
        if thread_orm is None:
            error_msg = f"Thread {thread_id} not found"
            raise NotFoundError(error_msg)
        return thread_orm

    def list_(
        self, workspace_id: WorkspaceId, query: ListQuery
    ) -> ListResponse[Thread]:
        """List threads with pagination and filtering."""
        q = self._session.query(ThreadOrm).filter(
            ThreadOrm.workspace_id == workspace_id
        )
        orms: list[ThreadOrm]
        orms, has_more = list_all(q, query, ThreadOrm.id)
        data = [orm.to_model() for orm in orms]
        return ListResponse(
            data=data,
            has_more=has_more,
            first_id=data[0].id if data else None,
            last_id=data[-1].id if data else None,
        )

    def retrieve(self, workspace_id: WorkspaceId, thread_id: ThreadId) -> Thread:
        """Retrieve thread by ID."""
        thread_orm = self._find_by_id(workspace_id, thread_id)
        return thread_orm.to_model()

    def create(self, workspace_id: WorkspaceId, params: ThreadCreate) -> Thread:
        """Create a new thread."""
        thread = Thread.create(workspace_id, params)
        thread_orm = ThreadOrm.from_model(thread)
        self._session.add(thread_orm)
        self._session.commit()
        return thread

    def modify(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, params: ThreadModify
    ) -> Thread:
        """Modify an existing thread."""
        thread_orm = self._find_by_id(workspace_id, thread_id)
        thread_orm.update(params.model_dump())
        self._session.commit()
        self._session.refresh(thread_orm)
        return thread_orm.to_model()

    def delete(self, workspace_id: WorkspaceId, thread_id: ThreadId) -> None:
        """Delete a thread and cascade to messages and runs."""
        thread_orm = self._find_by_id(workspace_id, thread_id)
        self._session.delete(thread_orm)
        self._session.commit()
