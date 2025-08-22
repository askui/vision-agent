from fastapi import APIRouter, status

from askui.chat.api.dependencies import ListQueryDep
from askui.chat.api.messages.dependencies import MessageServiceDep
from askui.chat.api.messages.models import Message, MessageCreateParams
from askui.chat.api.messages.service import MessageService
from askui.chat.api.models import MessageId, ThreadId
from askui.chat.api.threads.dependencies import ThreadFacadeDep
from askui.chat.api.threads.facade import ThreadFacade
from askui.utils.api_utils import ListQuery, ListResponse

router = APIRouter(prefix="/threads/{thread_id}/messages", tags=["messages"])


@router.get("")
def list_messages(
    thread_id: ThreadId,
    query: ListQuery = ListQueryDep,
    thread_facade: ThreadFacade = ThreadFacadeDep,
) -> ListResponse[Message]:
    return thread_facade.list_messages(thread_id, query=query)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_message(
    thread_id: ThreadId,
    params: MessageCreateParams,
    thread_facade: ThreadFacade = ThreadFacadeDep,
) -> Message:
    return thread_facade.create_message(thread_id=thread_id, params=params)


@router.get("/{message_id}")
def retrieve_message(
    thread_id: ThreadId,
    message_id: MessageId,
    message_service: MessageService = MessageServiceDep,
) -> Message:
    return message_service.retrieve(thread_id, message_id)


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    thread_id: ThreadId,
    message_id: MessageId,
    message_service: MessageService = MessageServiceDep,
) -> None:
    message_service.delete(thread_id, message_id)
