from fastapi import Depends

from chat.api.dependencies import SettingsDep
from chat.api.settings import Settings

from .service import RunService


def get_runs_service(settings: Settings = SettingsDep) -> RunService:
    """Get RunService instance."""
    return RunService(settings.data_dir)


RunServiceDep = Depends(get_runs_service)
