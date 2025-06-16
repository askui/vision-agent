from fastapi import Depends

from chat.api.assistants.service import AssistantService
from chat.api.dependencies import SettingsDep
from chat.api.settings import Settings


def get_assistant_service(settings: Settings = SettingsDep) -> AssistantService:
    """Get AssistantService instance."""
    return AssistantService(settings.data_dir)


AssistantServiceDep = Depends(get_assistant_service)
