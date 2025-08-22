from pathlib import Path

from fastapi import Depends

from askui.chat.api.dependencies import WorkspaceDirDep
from askui.chat.api.messages.dependencies import MessageServiceDep, MessageTranslatorDep
from askui.chat.api.messages.service import MessageService
from askui.chat.api.messages.translator import MessageTranslator

from .service import RunService


def get_runs_service(
    workspace_dir: Path = WorkspaceDirDep,
    message_service: MessageService = MessageServiceDep,
    message_translator: MessageTranslator = MessageTranslatorDep,
) -> RunService:
    """Get RunService instance."""
    return RunService(workspace_dir, message_service, message_translator)


RunServiceDep = Depends(get_runs_service)
