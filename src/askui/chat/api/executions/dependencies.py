from fastapi import Depends

from askui.chat.api.dependencies import SettingsDep
from askui.chat.api.executions.service import ExecutionService
from askui.chat.api.settings import Settings


def get_execution_service(settings: Settings = SettingsDep) -> ExecutionService:
    """Get ExecutionService instance."""
    return ExecutionService(settings.data_dir)


ExecutionServiceDep = Depends(get_execution_service)
