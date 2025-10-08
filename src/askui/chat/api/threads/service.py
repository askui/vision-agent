from typing import Callable

from askui.chat.api.db.query_builder import QueryBuilder
from askui.chat.api.messages.service import MessageService
from askui.chat.api.models import ThreadId
from askui.chat.api.runs.service import RunService
from askui.chat.api.threads.models import ThreadModel
from askui.chat.api.threads.schemas import (
    Thread,
    ThreadCreateParams,
    ThreadModifyParams,
)
from askui.utils.api_utils import ListQuery, ListResponse, NotFoundError
from sqlalchemy.orm import Session


class ThreadService:
    """Service for managing Thread resources with SQLAlchemy persistence."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        message_service: MessageService,
        run_service: RunService,
    ) -> None:
        self._session_factory = session_factory
        self._message_service = message_service
        self._run_service = run_service

    def _to_pydantic(self, db_model: ThreadModel) -> Thread:
        """Convert SQLAlchemy model to Pydantic model."""
        return db_model.to_pydantic()

    def list_(self, query: ListQuery) -> ListResponse[Thread]:
        with self._session_factory() as session:
            q = session.query(ThreadModel)

            # Apply list query parameters
            q = QueryBuilder.apply_list_query(
                q, ThreadModel, query, ThreadModel.created_at, ThreadModel.id
            )

            # Apply limit
            limit = query.limit or 20
            q = q.limit(limit + 1)  # +1 to check if there are more

            results = q.all()
            return QueryBuilder.build_list_response(results, limit, self._to_pydantic)

    def retrieve(self, thread_id: ThreadId) -> Thread:
        with self._session_factory() as session:
            db_thread = (
                session.query(ThreadModel).filter(ThreadModel.id == thread_id).first()
            )
            if not db_thread:
                error_msg = f"Thread {thread_id} not found"
                raise NotFoundError(error_msg)
            return self._to_pydantic(db_thread)

    def create(self, params: ThreadCreateParams) -> Thread:
        with self._session_factory() as session:
            db_thread = ThreadModel.from_create_params(params)
            session.add(db_thread)
            session.commit()
            session.refresh(db_thread)

            thread = self._to_pydantic(db_thread)

            if params.messages:
                for message in params.messages:
                    self._message_service.create(
                        thread_id=thread.id,
                        params=message,
                    )
            return thread

    def modify(self, thread_id: ThreadId, params: ThreadModifyParams) -> Thread:
        with self._session_factory() as session:
            db_thread = (
                session.query(ThreadModel).filter(ThreadModel.id == thread_id).first()
            )
            if not db_thread:
                error_msg = f"Thread {thread_id} not found"
                raise NotFoundError(error_msg)

            # Update fields
            if params.name is not None:
                db_thread.name = params.name

            session.commit()
            session.refresh(db_thread)

            return self._to_pydantic(db_thread)

    def delete(self, thread_id: ThreadId) -> None:
        with self._session_factory() as session:
            db_thread = (
                session.query(ThreadModel).filter(ThreadModel.id == thread_id).first()
            )
            if not db_thread:
                error_msg = f"Thread {thread_id} not found"
                raise NotFoundError(error_msg)

            # Delete related messages and runs (cascade will handle this)
            session.delete(db_thread)
            session.commit()
            session.commit()
