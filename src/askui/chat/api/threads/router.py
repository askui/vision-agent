from fastapi import APIRouter, HTTPException

from askui.chat.api.threads.dependencies import ThreadServiceDep
from askui.chat.api.threads.service import Thread, ThreadListResponse, ThreadService

router = APIRouter(prefix="/threads", tags=["threads"])


@router.get("")
def list_threads(
    limit: int | None = None,
    thread_service: ThreadService = ThreadServiceDep,
) -> ThreadListResponse:
    """List all threads."""
    return thread_service.list_(limit=limit)


@router.post("")
def create_thread(
    thread_service: ThreadService = ThreadServiceDep,
) -> Thread:
    """Create a new thread."""
    return thread_service.create()


@router.get("/{thread_id}")
def get_thread(
    thread_id: str,
    thread_service: ThreadService = ThreadServiceDep,
) -> Thread:
    """Get a thread by ID."""
    try:
        return thread_service.retrieve(thread_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{thread_id}")
def delete_thread(
    thread_id: str,
    thread_service: ThreadService = ThreadServiceDep,
) -> None:
    """Delete a thread."""
    try:
        thread_service.delete(thread_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
