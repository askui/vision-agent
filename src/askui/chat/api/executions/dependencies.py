from fastapi import Depends

from askui.chat.api.dependencies import SettingsDep
from askui.chat.api.executions.service import ExecutionService
from askui.chat.api.settings import Settings
from askui.chat.api.threads.dependencies import ThreadFacadeDep
from askui.chat.api.threads.facade import ThreadFacade
from askui.chat.api.workflows.dependencies import WorkflowServiceDep
from askui.chat.api.workflows.service import WorkflowService


def get_execution_service(
    settings: Settings = SettingsDep,
    workflow_service: WorkflowService = WorkflowServiceDep,
    thread_facade: ThreadFacade = ThreadFacadeDep,
) -> ExecutionService:
    """Get ExecutionService instance."""
    return ExecutionService(settings.data_dir, workflow_service, thread_facade)


ExecutionServiceDep = Depends(get_execution_service)
