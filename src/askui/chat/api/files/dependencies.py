from fastapi import Depends

from askui.chat.api.dependencies import SettingsDep
from askui.chat.api.files.service import FileService
from askui.chat.api.settings import Settings


def get_file_service(settings: Settings = SettingsDep) -> FileService:
    """Get FileService instance."""
    return FileService(settings.data_dir)


FileServiceDep = Depends(get_file_service)
