from typing import Annotated

from fastapi import APIRouter, Header, status

from askui.chat.api.dependencies import ListQueryDep
from askui.chat.api.models import ThreadId, WorkspaceId
from askui.chat.api.threads.dependencies import ThreadServiceDep
from askui.chat.api.threads.models import Thread, ThreadCreate, ThreadModify
from askui.chat.api.threads.service import ThreadService
from askui.utils.api_utils import ListQuery, ListResponse

router = APIRouter(prefix="/threads", tags=["threads"])


@router.get("")
def list_threads(
    askui_workspace: Annotated[WorkspaceId, Header()],
    query: ListQuery = ListQueryDep,
    thread_service: ThreadService = ThreadServiceDep,
) -> ListResponse[Thread]:
    return thread_service.list_(workspace_id=askui_workspace, query=query)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_thread(
    askui_workspace: Annotated[WorkspaceId, Header()],
    params: ThreadCreate,
    thread_service: ThreadService = ThreadServiceDep,
) -> Thread:
    return thread_service.create(workspace_id=askui_workspace, params=params)


@router.get("/{thread_id}")
def retrieve_thread(
    askui_workspace: Annotated[WorkspaceId, Header()],
    thread_id: ThreadId,
    thread_service: ThreadService = ThreadServiceDep,
) -> Thread:
    return thread_service.retrieve(workspace_id=askui_workspace, thread_id=thread_id)


@router.post("/{thread_id}")
def modify_thread(
    askui_workspace: Annotated[WorkspaceId, Header()],
    thread_id: ThreadId,
    params: ThreadModify,
    thread_service: ThreadService = ThreadServiceDep,
) -> Thread:
    return thread_service.modify(
        workspace_id=askui_workspace, thread_id=thread_id, params=params
    )


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(
    askui_workspace: Annotated[WorkspaceId, Header()],
    thread_id: ThreadId,
    thread_service: ThreadService = ThreadServiceDep,
) -> None:
    thread_service.delete(workspace_id=askui_workspace, thread_id=thread_id)
