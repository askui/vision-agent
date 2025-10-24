from typing import Iterator

from sqlalchemy.orm import Session

from askui.chat.api.db.queries import list_all
from askui.chat.api.messages.models import Message, MessageCreate
from askui.chat.api.messages.orms import MessageOrm
from askui.chat.api.models import MessageId, ThreadId, WorkspaceId
from askui.utils.api_utils import (
    LIST_LIMIT_DEFAULT,
    ListOrder,
    ListQuery,
    ListResponse,
    NotFoundError,
)


class MessageService:
    """Service for managing Message resources with database persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _find_by_id(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, message_id: MessageId
    ) -> MessageOrm:
        """Find message by ID."""
        message_orm: MessageOrm | None = (
            self._session.query(MessageOrm)
            .filter(
                MessageOrm.id == message_id,
                MessageOrm.thread_id == thread_id,
                MessageOrm.workspace_id == workspace_id,
            )
            .first()
        )
        if message_orm is None:
            error_msg = f"Message {message_id} not found in thread {thread_id}"
            raise NotFoundError(error_msg)
        return message_orm

    def create(
        self,
        workspace_id: WorkspaceId,
        thread_id: ThreadId,
        params: MessageCreate,
    ) -> Message:
        """Create a new message."""
        message = Message.create(workspace_id, thread_id, params)
        message_orm = MessageOrm.from_model(message)
        self._session.add(message_orm)
        self._session.commit()
        return message

    def list_(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, query: ListQuery
    ) -> ListResponse[Message]:
        """List messages with pagination and filtering."""
        q = self._session.query(MessageOrm).filter(
            MessageOrm.thread_id == thread_id,
            MessageOrm.workspace_id == workspace_id,
        )
        orms: list[MessageOrm]
        orms, has_more = list_all(q, query, MessageOrm.id)
        data = [orm.to_model() for orm in orms]
        return ListResponse(
            data=data,
            has_more=has_more,
            first_id=data[0].id if data else None,
            last_id=data[-1].id if data else None,
        )

    def iter(
        self,
        workspace_id: WorkspaceId,
        thread_id: ThreadId,
        order: ListOrder = "asc",
        batch_size: int = LIST_LIMIT_DEFAULT,
    ) -> Iterator[Message]:
        """Iterate through messages in batches."""
        has_more = True
        last_id: str | None = None
        while has_more:
            list_messages_response = self.list_(
                workspace_id=workspace_id,
                thread_id=thread_id,
                query=ListQuery(limit=batch_size, order=order, after=last_id),
            )
            has_more = list_messages_response.has_more
            last_id = list_messages_response.last_id
            for msg in list_messages_response.data:
                yield msg

    def retrieve(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, message_id: MessageId
    ) -> Message:
        """Retrieve message by ID."""
        message_orm = self._find_by_id(workspace_id, thread_id, message_id)
        return message_orm.to_model()

    def delete(
        self, workspace_id: WorkspaceId, thread_id: ThreadId, message_id: MessageId
    ) -> None:
        """Delete a message."""
        message_orm = self._find_by_id(workspace_id, thread_id, message_id)
        self._session.delete(message_orm)
        self._session.commit()
