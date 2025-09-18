from pathlib import Path

from fastapi import Depends

from askui.chat.api.assistants.dependencies import AssistantServiceDep
from askui.chat.api.assistants.service import AssistantService
from askui.chat.api.dependencies import WorkspaceDirDep
from askui.chat.api.mcp_clients.dependencies import McpClientManagerManagerDep
from askui.chat.api.mcp_clients.manager import McpClientManagerManager
from askui.chat.api.messages.chat_history_manager import ChatHistoryManager
from askui.chat.api.messages.dependencies import ChatHistoryManagerDep
from askui.chat.api.runs.models import RunListQuery

from .service import RunService

RunListQueryDep = Depends(RunListQuery)


def get_runs_service(
    workspace_dir: Path = WorkspaceDirDep,
    assistant_service: AssistantService = AssistantServiceDep,
    chat_history_manager: ChatHistoryManager = ChatHistoryManagerDep,
    mcp_client_manager_manager: McpClientManagerManager = McpClientManagerManagerDep,
) -> RunService:
    return RunService(
        base_dir=workspace_dir,
        assistant_service=assistant_service,
        mcp_client_manager_manager=mcp_client_manager_manager,
        chat_history_manager=chat_history_manager,
    )


RunServiceDep = Depends(get_runs_service)
