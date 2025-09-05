from pathlib import Path

from fastapi import Depends

from askui.chat.api.assistants.dependencies import AssistantServiceDep
from askui.chat.api.assistants.service import AssistantService
from askui.chat.api.dependencies import WorkspaceDirDep
from askui.chat.api.mcp_clients.dependencies import McpClientManagerManagerDep
from askui.chat.api.mcp_clients.manager import McpClientManagerManager
from askui.chat.api.messages.dependencies import MessageServiceDep, MessageTranslatorDep
from askui.chat.api.messages.service import MessageService
from askui.chat.api.messages.translator import MessageTranslator

from .service import RunService


def get_runs_service(
    workspace_dir: Path = WorkspaceDirDep,
    assistant_service: AssistantService = AssistantServiceDep,
    mcp_client_manager_manager: McpClientManagerManager = McpClientManagerManagerDep,
    message_service: MessageService = MessageServiceDep,
    message_translator: MessageTranslator = MessageTranslatorDep,
) -> RunService:
    """Get RunService instance."""
    return RunService(
        base_dir=workspace_dir,
        assistant_service=assistant_service,
        mcp_client_manager_manager=mcp_client_manager_manager,
        message_service=message_service,
        message_translator=message_translator,
    )


RunServiceDep = Depends(get_runs_service)
