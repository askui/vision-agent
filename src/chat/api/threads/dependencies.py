from fastapi import Depends

from chat.api.dependencies import SettingsDep
from chat.api.messages.dependencies import MessageServiceDep
from chat.api.messages.service import MessageService
from chat.api.settings import Settings
from chat.api.threads.service import ThreadService


def get_thread_service(
    settings: Settings = SettingsDep,
    message_service: MessageService = MessageServiceDep,
) -> ThreadService:
    """Get ThreadService instance."""
    return ThreadService(
        base_dir=settings.data_dir,
        message_service=message_service,
    )


ThreadServiceDep = Depends(get_thread_service)
