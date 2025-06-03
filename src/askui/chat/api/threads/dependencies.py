from fastapi import Depends

from askui.chat.api.dependencies import SettingsDep
from askui.chat.api.settings import Settings
from askui.chat.api.threads.service import ThreadService


def get_thread_service(settings: Settings = SettingsDep) -> ThreadService:
    """Get ThreadService instance."""
    return ThreadService(settings.data_dir)


ThreadServiceDep = Depends(get_thread_service)
