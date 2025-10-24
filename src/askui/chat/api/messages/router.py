from typing import Annotated

from fastapi import APIRouter, Header, status

from askui.chat.api.dependencies import ListQueryDep
from askui.chat.api.messages.dependencies import MessageServiceDep
from askui.chat.api.messages.models import Message, MessageCreate
from askui.chat.api.messages.service import MessageService
from askui.chat.api.models import MessageId, ThreadId, WorkspaceId
from askui.utils.api_utils import ListQuery, ListResponse

router = APIRouter(prefix="/threads/{thread_id}/messages", tags=["messages"])


@router.get("")
def list_messages(
    askui_workspace: Annotated[WorkspaceId, Header()],
    thread_id: ThreadId,
    query: ListQuery = ListQueryDep,
    message_service: MessageService = MessageServiceDep,
) -> ListResponse[Message]:
    return message_service.list_(
        workspace_id=askui_workspace, thread_id=thread_id, query=query
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_message(
    askui_workspace: Annotated[WorkspaceId, Header()],
    thread_id: ThreadId,
    params: MessageCreate,
    message_service: MessageService = MessageServiceDep,
) -> Message:
    return message_service.create(
        workspace_id=askui_workspace, thread_id=thread_id, params=params
    )


@router.get("/{message_id}")
def retrieve_message(
    askui_workspace: Annotated[WorkspaceId, Header()],
    thread_id: ThreadId,
    message_id: MessageId,
    message_service: MessageService = MessageServiceDep,
) -> Message:
    return message_service.retrieve(
        workspace_id=askui_workspace, thread_id=thread_id, message_id=message_id
    )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    askui_workspace: Annotated[WorkspaceId, Header()],
    thread_id: ThreadId,
    message_id: MessageId,
    message_service: MessageService = MessageServiceDep,
) -> None:
    message_service.delete(
        workspace_id=askui_workspace, thread_id=thread_id, message_id=message_id
    )
