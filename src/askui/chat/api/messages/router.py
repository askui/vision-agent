from io import BytesIO
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel

from askui.chat.api.messages.dependencies import MessageServiceDep
from askui.chat.api.messages.service import Message, MessageListResponse, MessageService


class CreateMessageRequest(BaseModel):
    """Request model for creating a message."""

    role: str
    content: str | dict[str, Any] | list[Any]


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


@router.post("")
async def create_message(
    thread_id: str,
    request: CreateMessageRequest,
    image: UploadFile | None = None,
    message_service: MessageService = MessageServiceDep,
) -> Message:
    """Create a new message in a thread."""
    try:
        # Handle image upload if provided
        pil_image = None
        if image:
            img_data = await image.read()
            pil_image = Image.open(BytesIO(img_data))

        return message_service.create(
            thread_id=thread_id,
            role=request.role,
            content=request.content,
            image=pil_image,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{message_id}")
def get_message(
    thread_id: str,
    message_id: str,
    message_service: MessageService = MessageServiceDep,
) -> Message:
    """Get a specific message from a thread."""
    try:
        return message_service.retrieve(thread_id, message_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{message_id}")
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
