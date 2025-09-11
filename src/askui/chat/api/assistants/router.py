from typing import Annotated

from fastapi import APIRouter, Header, status

from askui.chat.api.assistants.dependencies import AssistantServiceDep
from askui.chat.api.assistants.models import (
    Assistant,
    AssistantCreateParams,
    AssistantModifyParams,
)
from askui.chat.api.assistants.service import AssistantService
from askui.chat.api.dependencies import ListQueryDep
from askui.chat.api.models import AssistantId, WorkspaceId
from askui.utils.api_utils import ListQuery, ListResponse

router = APIRouter(prefix="/assistants", tags=["assistants"])


@router.get("")
def list_assistants(
    askui_workspace: Annotated[WorkspaceId | None, Header()],
    query: ListQuery = ListQueryDep,
    assistant_service: AssistantService = AssistantServiceDep,
) -> ListResponse[Assistant]:
    return assistant_service.list_(workspace_id=askui_workspace, query=query)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_assistant(
    params: AssistantCreateParams,
    askui_workspace: Annotated[WorkspaceId, Header()],
    assistant_service: AssistantService = AssistantServiceDep,
) -> Assistant:
    return assistant_service.create(workspace_id=askui_workspace, params=params)


@router.get("/{assistant_id}")
def retrieve_assistant(
    assistant_id: AssistantId,
    askui_workspace: Annotated[WorkspaceId | None, Header()],
    assistant_service: AssistantService = AssistantServiceDep,
) -> Assistant:
    return assistant_service.retrieve(
        workspace_id=askui_workspace, assistant_id=assistant_id
    )


@router.post("/{assistant_id}")
def modify_assistant(
    assistant_id: AssistantId,
    askui_workspace: Annotated[WorkspaceId, Header()],
    params: AssistantModifyParams,
    assistant_service: AssistantService = AssistantServiceDep,
) -> Assistant:
    return assistant_service.modify(
        workspace_id=askui_workspace, assistant_id=assistant_id, params=params
    )


@router.delete("/{assistant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assistant(
    assistant_id: AssistantId,
    askui_workspace: Annotated[WorkspaceId | None, Header()],
    assistant_service: AssistantService = AssistantServiceDep,
) -> None:
    assistant_service.delete(workspace_id=askui_workspace, assistant_id=assistant_id)
