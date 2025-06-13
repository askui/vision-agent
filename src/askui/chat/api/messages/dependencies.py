from fastapi import Depends

from askui.chat.api.dependencies import SettingsDep
from askui.chat.api.messages.message_persisted_service import MessagePersistedService
from askui.chat.api.messages.service import MessageService
from askui.chat.api.settings import Settings


def get_message_persisted_service(
    settings: Settings = SettingsDep,
) -> MessagePersistedService:
    """Get MessagePersistedService instance."""
    return MessagePersistedService(settings.data_dir)


MessagePersistedServiceDep = Depends(get_message_persisted_service)


def get_message_service(
    service: MessagePersistedService = MessagePersistedServiceDep,
) -> MessageService:
    """Get MessageService instance."""
    return MessageService(service)


MessageServiceDep = Depends(get_message_service)
