from fastapi import APIRouter, status

from askui.chat.api.assistants.dependencies import AssistantServiceDep
from askui.chat.api.assistants.models import (
    Assistant,
    AssistantCreateParams,
    AssistantModifyParams,
)
from askui.chat.api.assistants.service import AssistantService
from askui.chat.api.dependencies import ListQueryDep
from askui.chat.api.models import AssistantId
from askui.utils.api_utils import ListQuery, ListResponse

router = APIRouter(prefix="/assistants", tags=["assistants"])


@router.get("")
def list_assistants(
    query: ListQuery = ListQueryDep,
    assistant_service: AssistantService = AssistantServiceDep,
) -> ListResponse[Assistant]:
    return assistant_service.list_(query=query)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_assistant(
    params: AssistantCreateParams,
    assistant_service: AssistantService = AssistantServiceDep,
) -> Assistant:
    return assistant_service.create(params)


@router.get("/{assistant_id}")
def retrieve_assistant(
    assistant_id: AssistantId,
    assistant_service: AssistantService = AssistantServiceDep,
) -> Assistant:
    return assistant_service.retrieve(assistant_id)


@router.post("/{assistant_id}")
def modify_assistant(
    assistant_id: AssistantId,
    params: AssistantModifyParams,
    assistant_service: AssistantService = AssistantServiceDep,
) -> Assistant:
    return assistant_service.modify(assistant_id, params)


@router.delete("/{assistant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assistant(
    assistant_id: AssistantId,
    assistant_service: AssistantService = AssistantServiceDep,
) -> None:
    assistant_service.delete(assistant_id)
