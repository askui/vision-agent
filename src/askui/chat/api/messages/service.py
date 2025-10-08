"""Message service with SQLAlchemy persistence."""

from pathlib import Path
from typing import Callable, Iterator

from askui.chat.api.db.query_builder import QueryBuilder
from askui.chat.api.messages.models import MessageModel
from askui.chat.api.messages.schemas import Message, MessageCreateParams
from askui.chat.api.models import MessageId, ThreadId
from askui.utils.api_utils import ListQuery, ListResponse, NotFoundError
from sqlalchemy.orm import Session


class MessageService:
    """Service for managing Message resources with SQLAlchemy persistence."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def _to_pydantic(self, db_model: MessageModel) -> Message:
        """Convert SQLAlchemy model to Pydantic model."""
        return db_model.to_pydantic()

    def list_(self, thread_id: ThreadId, query: ListQuery) -> ListResponse[Message]:
        """List messages for a thread with pagination."""
        with self._session_factory() as session:
            q = session.query(MessageModel).filter(MessageModel.thread_id == thread_id)

            # Apply list query parameters
            q = QueryBuilder.apply_list_query(
                q, MessageModel, query, MessageModel.created_at, MessageModel.id
            )

            # Apply limit
            limit = query.limit or 20
            q = q.limit(limit + 1)  # +1 to check if there are more

            results = q.all()
            return QueryBuilder.build_list_response(results, limit, self._to_pydantic)

    def retrieve(self, thread_id: ThreadId, message_id: MessageId) -> Message:
        """Retrieve a message by ID."""
        with self._session_factory() as session:
            db_message = (
                session.query(MessageModel)
                .filter(
                    MessageModel.thread_id == thread_id,
                    MessageModel.id == message_id,
                )
                .first()
            )
            if not db_message:
                error_msg = f"Message {message_id} not found"
                raise NotFoundError(error_msg)
            return self._to_pydantic(db_message)

    def create(self, thread_id: ThreadId, params: MessageCreateParams) -> Message:
        """Create a new message."""
        with self._session_factory() as session:
            db_message = MessageModel.from_create_params(params, thread_id)
            session.add(db_message)
            session.commit()
            session.refresh(db_message)

            return self._to_pydantic(db_message)

    def delete(self, thread_id: ThreadId, message_id: MessageId) -> None:
        """Delete a message."""
        with self._session_factory() as session:
            db_message = (
                session.query(MessageModel)
                .filter(
                    MessageModel.thread_id == thread_id,
                    MessageModel.id == message_id,
                )
                .first()
            )
            if not db_message:
                error_msg = f"Message {message_id} not found"
                raise NotFoundError(error_msg)

            session.delete(db_message)
            session.commit()

    def get_messages_dir(self, thread_id: ThreadId) -> Path:
        """Get messages directory for a thread (for backward compatibility)."""
        return Path.cwd() / "chat" / "messages" / thread_id

    def list_messages(self, thread_id: ThreadId) -> Iterator[Message]:
        """List all messages for a thread (for backward compatibility)."""
        with self._session_factory() as session:
            db_messages = (
                session.query(MessageModel)
                .filter(MessageModel.thread_id == thread_id)
                .order_by(MessageModel.created_at)
                .all()
            )
            for db_message in db_messages:
                yield self._to_pydantic(db_message)
