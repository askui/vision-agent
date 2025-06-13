from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from askui.chat.api.messages.dependencies import MessageServiceDep
from askui.chat.api.messages.message_persisted_service import Metadata
from askui.chat.api.messages.models import Message
from askui.chat.api.messages.service import (
    MessageCreateRequest,
    MessagePatch,
    MessageService,
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
    message_service: MessageService = MessageServiceDep,
) -> ListResponse[Message]:
    """List all messages in a thread."""
    try:
        return message_service.list_(thread_id, query=query)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_message(
    thread_id: ThreadId,
    request: MessageCreateRequest,
    message_service: MessageService = MessageServiceDep,
) -> Message:
    """Create a new message in a thread."""
    try:
        return message_service.create(
            thread_id=thread_id,
            request=request,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{message_id}")
def retrieve_message(
    thread_id: ThreadId,
    message_id: MessageId,
    message_service: MessageService = MessageServiceDep,
) -> Message:
    """Get a specific message from a thread."""
    try:
        return message_service.retrieve(thread_id, message_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    thread_id: ThreadId,
    message_id: MessageId,
    message_service: MessageService = MessageServiceDep,
) -> None:
    """Delete a message from a thread."""
    try:
        message_service.delete(thread_id, message_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


class MessageModifyRequest(BaseModel):
    metadata: Metadata  # TODO Stronger validation


@router.post("/{message_id}")
def modify_message(
    thread_id: ThreadId,
    message_id: MessageId,
    request: MessageModifyRequest,
    message_service: MessageService = MessageServiceDep,
) -> Message:
    """Modify a message in a thread."""
    return message_service.patch(
        thread_id,
        message_id,
        MessagePatch(metadata=request.metadata),
    )
