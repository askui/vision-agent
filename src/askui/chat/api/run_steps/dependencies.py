from fastapi import Depends

from askui.chat.api.dependencies import SettingsDep
from askui.chat.api.settings import Settings

from .service import RunStepService


def get_run_step_service(settings: Settings = SettingsDep) -> RunStepService:
    """Get RunStepService instance."""
    return RunStepService(settings.data_dir)


RunStepServiceDep = Depends(get_run_step_service)
