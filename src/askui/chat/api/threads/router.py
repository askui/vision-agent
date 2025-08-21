from fastapi import APIRouter, HTTPException, status

from askui.chat.api.models import ListQueryDep, ThreadId
from askui.chat.api.threads.dependencies import ThreadServiceDep
from askui.chat.api.threads.service import (
    Thread,
    ThreadCreateRequest,
    ThreadModifyRequest,
    ThreadService,
)
from askui.utils.api_utils import ListQuery, ListResponse

router = APIRouter(prefix="/threads", tags=["threads"])


@router.get("")
async def list_threads(
    query: ListQuery = ListQueryDep,
    thread_service: ThreadService = ThreadServiceDep,
) -> ListResponse[Thread]:
    """List all threads."""
    return await thread_service.find(query=query)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_thread(
    request: CreateThreadRequest,
    thread_service: ThreadService = ThreadServiceDep,
) -> Thread:
    """Create a new thread."""
    return await thread_service.create(request=request)


@router.get("/{thread_id}")
async def retrieve_thread(
    thread_id: ThreadId,
    thread_service: ThreadService = ThreadServiceDep,
) -> Thread:
    """Get a thread by ID."""
    return await thread_service.find_one(thread_id=thread_id)


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: ThreadId,
    thread_service: ThreadService = ThreadServiceDep,
) -> None:
    """Delete a thread."""
    try:
        await thread_service.delete(thread_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{thread_id}")
async def modify_thread(
    thread_id: ThreadId,
    request: ThreadModifyRequest,
    thread_service: ThreadService = ThreadServiceDep,
) -> Thread:
    """Modify a thread."""
    return await thread_service.modify(thread_id, request)
