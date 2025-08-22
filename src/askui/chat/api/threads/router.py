from fastapi import APIRouter, status

from askui.chat.api.dependencies import ListQueryDep
from askui.chat.api.models import ThreadId
from askui.chat.api.threads.dependencies import ThreadServiceDep
from askui.chat.api.threads.models import Thread, ThreadCreateParams, ThreadModifyParams
from askui.chat.api.threads.service import ThreadService
from askui.utils.api_utils import ListQuery, ListResponse

router = APIRouter(prefix="/threads", tags=["threads"])


@router.get("")
def list_threads(
    query: ListQuery = ListQueryDep,
    thread_service: ThreadService = ThreadServiceDep,
) -> ListResponse[Thread]:
    return thread_service.list_(query=query)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_thread(
    params: ThreadCreateParams,
    thread_service: ThreadService = ThreadServiceDep,
) -> Thread:
    return thread_service.create(params)


@router.get("/{thread_id}")
def retrieve_thread(
    thread_id: ThreadId,
    thread_service: ThreadService = ThreadServiceDep,
) -> Thread:
    return thread_service.retrieve(thread_id)


@router.post("/{thread_id}")
def modify_thread(
    thread_id: ThreadId,
    params: ThreadModifyParams,
    thread_service: ThreadService = ThreadServiceDep,
) -> Thread:
    return thread_service.modify(thread_id, params)


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(
    thread_id: ThreadId,
    thread_service: ThreadService = ThreadServiceDep,
) -> None:
    thread_service.delete(thread_id)
