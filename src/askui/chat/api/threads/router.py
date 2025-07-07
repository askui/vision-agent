from fastapi import APIRouter, HTTPException, status

from askui.chat.api.models import ListQuery, ListQueryDep, ListResponse, ThreadId
from askui.chat.api.threads.dependencies import ThreadServiceDep
from askui.chat.api.threads.service import (
    Thread,
    ThreadCreateRequest,
    ThreadModifyRequest,
    ThreadService,
)

router = APIRouter(prefix="/threads", tags=["threads"])


@router.get("")
def list_threads(
    query: ListQuery = ListQueryDep,
    thread_service: ThreadService = ThreadServiceDep,
) -> ListResponse[Thread]:
    """List all threads."""
    return thread_service.list_(query=query)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_thread(
    request: ThreadCreateRequest,
    thread_service: ThreadService = ThreadServiceDep,
) -> Thread:
    """Create a new thread."""
    return thread_service.create(request=request)


@router.get("/{thread_id}")
def retrieve_thread(
    thread_id: ThreadId,
    thread_service: ThreadService = ThreadServiceDep,
) -> Thread:
    """Get a thread by ID."""
    try:
        return thread_service.retrieve(thread_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(
    thread_id: ThreadId,
    thread_service: ThreadService = ThreadServiceDep,
) -> None:
    """Delete a thread."""
    try:
        thread_service.delete(thread_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{thread_id}")
def modify_thread(
    thread_id: ThreadId,
    request: ThreadModifyRequest,
    thread_service: ThreadService = ThreadServiceDep,
) -> Thread:
    """Modify a thread."""
    return thread_service.modify(thread_id, request)
