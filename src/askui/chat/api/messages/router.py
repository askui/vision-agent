from fastapi import APIRouter, HTTPException, status

from askui.chat.api.messages.dependencies import MessageServiceDep
from askui.chat.api.messages.service import Message, MessageListResponse, MessageService
from askui.models.shared.computer_agent_message_param import MessageParam

router = APIRouter(prefix="/threads/{thread_id}/messages", tags=["messages"])


@router.get("")
def list_messages(
    thread_id: str,
    limit: int | None = None,
    message_service: MessageService = MessageServiceDep,
) -> MessageListResponse:
    """List all messages in a thread."""
    try:
        return message_service.list_(thread_id, limit=limit)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_message(
    thread_id: str,
    message: MessageParam,
    message_service: MessageService = MessageServiceDep,
) -> Message:
    """Create a new message in a thread."""
    try:
        return message_service.create(
            thread_id=thread_id,
            message=message,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{message_id}")
def retrieve_message(
    thread_id: str,
    message_id: str,
    message_service: MessageService = MessageServiceDep,
) -> Message:
    """Get a specific message from a thread."""
    try:
        return message_service.retrieve(thread_id, message_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    thread_id: str,
    message_id: str,
    message_service: MessageService = MessageServiceDep,
) -> None:
    """Delete a message from a thread."""
    try:
        message_service.delete(thread_id, message_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
