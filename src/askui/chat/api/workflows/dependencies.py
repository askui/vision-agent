from fastapi import Depends

from askui.chat.api.dependencies import SettingsDep
from askui.chat.api.settings import Settings
from askui.chat.api.workflows.service import WorkflowService


def get_workflow_service(settings: Settings = SettingsDep) -> WorkflowService:
    """Get WorkflowService instance."""
    return WorkflowService(settings.data_dir)


WorkflowServiceDep = Depends(get_workflow_service)
