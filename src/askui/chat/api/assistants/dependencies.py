from typing import Callable

from askui.chat.api.assistants.service import AssistantService
from askui.chat.api.dependencies import SessionFactoryDep
from fastapi import Depends
from sqlalchemy.orm import Session


def get_assistant_service(
    session_factory: Callable[[], Session] = SessionFactoryDep,
) -> AssistantService:
    """Get AssistantService instance."""
    return AssistantService(session_factory)


AssistantServiceDep = Depends(get_assistant_service)
