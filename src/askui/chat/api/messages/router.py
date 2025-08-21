from fastapi import APIRouter, HTTPException, status

from askui.chat.api.messages.dependencies import MessageServiceDep
from askui.chat.api.messages.service import (
    Message,
    MessageCreateRequest,
    MessageService,
)
from askui.chat.api.models import ListQueryDep, MessageId, ThreadId
from askui.utils.api_utils import ListQuery, ListResponse, NotFoundError

router = APIRouter(prefix="/threads/{thread_id}/messages", tags=["messages"])


@router.get("")
async def list_messages(
    thread_id: ThreadId,
    query: ListQuery = ListQueryDep,
    message_service: MessageService = MessageServiceDep,
) -> ListResponse[Message]:
    """List messages for a thread."""
    return await message_service.find(thread_id=thread_id, query=query)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_message(
    request: CreateMessageRequest,
    thread_id: ThreadId,
    message_service: MessageService = MessageServiceDep,
) -> Message:
    """Create a new message in a thread."""
    return await message_service.create(request=request, thread_id=thread_id)


@router.get("/{message_id}")
async def retrieve_message(
    message_id: MessageId,
    thread_id: ThreadId,
    message_service: MessageService = MessageServiceDep,
) -> Message:
    """Get a message by ID."""
    return await message_service.find_one(thread_id=thread_id, message_id=message_id)


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    thread_id: ThreadId,
    message_id: MessageId,
    message_service: MessageService = MessageServiceDep,
) -> None:
    """Delete a message from a thread."""
    try:
        await message_service.delete(thread_id, message_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
