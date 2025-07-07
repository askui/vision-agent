from fastapi import APIRouter, HTTPException

# from fastapi import status
from askui.chat.api.assistants.dependencies import AssistantServiceDep
from askui.chat.api.assistants.models import Assistant
from askui.chat.api.assistants.service import (
    AssistantService,
)  # AssistantModifyRequest, CreateAssistantRequest,
from askui.chat.api.models import ListQuery, ListQueryDep, ListResponse

router = APIRouter(prefix="/assistants", tags=["assistants"])


@router.get("")
def list_assistants(
    query: ListQuery = ListQueryDep,
    assistant_service: AssistantService = AssistantServiceDep,
) -> ListResponse[Assistant]:
    """List all assistants."""
    return assistant_service.list_(query=query)


# @router.post("", status_code=status.HTTP_201_CREATED)
# def create_assistant(
#     request: CreateAssistantRequest,
#     assistant_service: AssistantService = AssistantServiceDep,
# ) -> Assistant:
#     """Create a new assistant."""
#     return assistant_service.create(request)


@router.get("/{assistant_id}")
def retrieve_assistant(
    assistant_id: str,
    assistant_service: AssistantService = AssistantServiceDep,
) -> Assistant:
    """Get an assistant by ID."""
    try:
        return assistant_service.retrieve(assistant_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


# @router.post("/{assistant_id}")
# def modify_assistant(
#     assistant_id: str,
#     request: AssistantModifyRequest,
#     assistant_service: AssistantService = AssistantServiceDep,
# ) -> Assistant:
#     """Update an assistant."""
#     try:
#         return assistant_service.modify(assistant_id, request)
#     except FileNotFoundError as e:
#         raise HTTPException(status_code=404, detail=str(e)) from e


# @router.delete("/{assistant_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_assistant(
#     assistant_id: str,
#     assistant_service: AssistantService = AssistantServiceDep,
# ) -> None:
#     """Delete an assistant."""
#     try:
#         assistant_service.delete(assistant_id)
#     except FileNotFoundError as e:
#         raise HTTPException(status_code=404, detail=str(e)) from e
