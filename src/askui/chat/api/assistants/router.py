from fastapi import APIRouter, Body, HTTPException, status

from askui.chat.api.assistants.dependencies import AssistantServiceDep
from askui.chat.api.assistants.service import (
    Assistant,
    AssistantListResponse,
    AssistantService,
    CreateAssistantRequest,
    UpdateAssistantRequest,
)

router = APIRouter(prefix="/assistants", tags=["assistants"])


@router.get("")
def list_assistants(
    limit: int | None = None,
    assistant_service: AssistantService = AssistantServiceDep,
) -> AssistantListResponse:
    """List all assistants."""
    return assistant_service.list_(limit=limit)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_assistant(
    request: CreateAssistantRequest,
    assistant_service: AssistantService = AssistantServiceDep,
) -> Assistant:
    """Create a new assistant."""
    return assistant_service.create(request)


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


@router.post("/{assistant_id}")
def update_assistant(
    assistant_id: str,
    request: UpdateAssistantRequest,
    assistant_service: AssistantService = AssistantServiceDep,
) -> Assistant:
    """Update an assistant."""
    try:
        return assistant_service.update(assistant_id, request)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{assistant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assistant(
    assistant_id: str,
    assistant_service: AssistantService = AssistantServiceDep,
) -> None:
    """Delete an assistant."""
    try:
        assistant_service.delete(assistant_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
