from fastapi import Depends

from askui.chat.api.dependencies import SettingsDep
from askui.chat.api.messages.service import MessageService
from askui.chat.api.settings import Settings


def get_message_service(
    settings: Settings = SettingsDep,
) -> MessageService:
    """Get MessagePersistedService instance."""
    return MessageService(settings.data_dir)


MessageServiceDep = Depends(get_message_service)
