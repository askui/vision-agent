from fastapi import APIRouter, HTTPException, status

from askui.chat.api.messages.dependencies import MessagePersistedServiceDep
from askui.chat.api.messages.message_persisted_service import (
    MessagePersisted,
    MessagePersistedService,
)
from askui.chat.api.models import (
    ListQuery,
    ListQueryDep,
    ListResponse,
    MessageId,
    ThreadId,
)

router = APIRouter(prefix="/threads/{thread_id}/messages", tags=["messages"])


@router.get("")
def list_messages(
    thread_id: ThreadId,
    query: ListQuery = ListQueryDep,
    message_service: MessagePersistedService = MessagePersistedServiceDep,
) -> ListResponse[MessagePersisted]:
    """List all messages in a thread."""
    try:
        messages = message_service.list_(thread_id, query=query)
        return ListResponse(
            data=messages,
            first_id=messages[0].id if messages else None,
            last_id=messages[-1].id if messages else None,
            has_more=len(messages) > query.limit,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_message(
    thread_id: ThreadId,
    message: MessagePersisted,
    message_service: MessagePersistedService = MessagePersistedServiceDep,
) -> MessagePersisted:
    """Create a new message in a thread."""
    try:
        return message_service.create(thread_id=thread_id, message=message)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{message_id}")
def retrieve_message(
    thread_id: ThreadId,
    message_id: MessageId,
    message_service: MessagePersistedService = MessagePersistedServiceDep,
) -> MessagePersisted:
    """Get a specific message from a thread."""
    try:
        messages = message_service.list_(thread_id=thread_id, query=ListQuery(limit=1))
        for msg in messages:
            if msg.id == message_id:
                return msg
        error_msg = f"Message {message_id} not found in thread {thread_id}"
        raise HTTPException(status_code=404, detail=error_msg)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    thread_id: ThreadId,
    message_id: MessageId,
    message_service: MessagePersistedService = MessagePersistedServiceDep,
) -> None:
    """Delete a message from a thread."""
    try:
        message_service.delete(thread_id, message_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
