from fastapi import Depends

from askui.chat.api.assistants.service import AssistantService
from askui.chat.api.db.session import SessionDep


def get_assistant_service(
    session: SessionDep,
) -> AssistantService:
    """Get AssistantService instance."""
    return AssistantService(session)


AssistantServiceDep = Depends(get_assistant_service)
