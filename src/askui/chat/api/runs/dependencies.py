from fastapi import Depends
from pydantic import UUID4
from sqlalchemy.orm import Session

from askui.chat.api.assistants.dependencies import (
    AssistantServiceDep,
    get_assistant_service,
)
from askui.chat.api.assistants.service import AssistantService
from askui.chat.api.db.session import SessionDep
from askui.chat.api.dependencies import SettingsDep, get_settings
from askui.chat.api.files.dependencies import get_file_service
from askui.chat.api.mcp_clients.dependencies import (
    McpClientManagerManagerDep,
    get_mcp_client_manager_manager,
)
from askui.chat.api.mcp_clients.manager import McpClientManagerManager
from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service
from askui.chat.api.messages.chat_history_manager import ChatHistoryManager
from askui.chat.api.messages.dependencies import (
    ChatHistoryManagerDep,
    get_chat_history_manager,
    get_message_service,
    get_message_translator,
    get_truncation_strategy_factory,
)
from askui.chat.api.runs.models import RunListQuery
from askui.chat.api.settings import Settings

from .service import RunService

RunListQueryDep = Depends(RunListQuery)


def get_runs_service(
    session: SessionDep,
    assistant_service: AssistantService = AssistantServiceDep,
    chat_history_manager: ChatHistoryManager = ChatHistoryManagerDep,
    mcp_client_manager_manager: McpClientManagerManager = McpClientManagerManagerDep,
    settings: Settings = SettingsDep,
) -> RunService:
    """
    Get RunService instance for FastAPI dependency injection.

    This function is designed for use with FastAPI's DI system.
    For manual construction outside of a request context, use `create_run_service()`.
    """
    return RunService(
        session=session,
        assistant_service=assistant_service,
        mcp_client_manager_manager=mcp_client_manager_manager,
        chat_history_manager=chat_history_manager,
        settings=settings,
    )


RunServiceDep = Depends(get_runs_service)


def create_run_service(session: Session, workspace_id: UUID4) -> RunService:
    """
    Create a RunService with all required dependencies manually.

    Use this function when you need a `RunService` outside of FastAPI's
    dependency injection context (e.g. APScheduler callbacks).

    Args:
        session (Session): Database session.
        workspace_id (UUID4): The workspace ID for the run execution.

    Returns:
        RunService: Configured run service.
    """
    settings = get_settings()

    assistant_service = get_assistant_service(session)
    file_service = get_file_service(session, settings)
    mcp_config_service = get_mcp_config_service(session, settings)
    mcp_client_manager_manager = get_mcp_client_manager_manager(mcp_config_service)

    message_service = get_message_service(session)
    message_translator = get_message_translator(file_service, workspace_id)
    truncation_strategy_factory = get_truncation_strategy_factory()
    chat_history_manager = get_chat_history_manager(
        message_service,
        message_translator,
        truncation_strategy_factory,
    )

    return RunService(
        session=session,
        assistant_service=assistant_service,
        mcp_client_manager_manager=mcp_client_manager_manager,
        chat_history_manager=chat_history_manager,
        settings=settings,
    )
