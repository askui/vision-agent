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
    """List messages in a tree path.

    Navigation behavior (only one of after/before can be specified):

    - `after=msg_xyz`: Find the latest leaf in msg_xyz's subtree, return path from
      msg_xyz DOWN to that leaf
    - `before=msg_xyz`: Traverse UP from msg_xyz to the root
    - Neither specified: Returns main branch (root → latest leaf in entire thread)

    Each message includes its `parent_id` field for tree navigation.

    Pagination:
    - `order=asc`: Results ordered by ID ascending (oldest first)
    - `order=desc`: Results ordered by ID descending (newest first)
    - `limit`: Maximum number of messages to return

    Args:
        askui_workspace (WorkspaceId): The workspace ID from header.
        thread_id (ThreadId): The thread ID.
        query (ListQuery): Pagination parameters (after OR before, limit, order).
        message_service (MessageService): The message service dependency.

    Returns:
        ListResponse[Message]: Paginated list of messages in the tree path.

    Raises:
        ValueError: If both `after` and `before` are specified.
    """
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
