from fastapi import Depends

from askui.chat.api.dependencies import SettingsDep
from askui.chat.api.messages.dependencies import MessagePersistedServiceDep
from askui.chat.api.messages.message_persisted_service import MessagePersistedService
from askui.chat.api.settings import Settings
from askui.chat.api.threads.service import ThreadService


def get_thread_service(
    settings: Settings = SettingsDep,
    message_service: MessagePersistedService = MessagePersistedServiceDep,
) -> ThreadService:
    """Get ThreadService instance."""
    return ThreadService(
        base_dir=settings.data_dir,
        message_service=message_service,
    )


ThreadServiceDep = Depends(get_thread_service)
