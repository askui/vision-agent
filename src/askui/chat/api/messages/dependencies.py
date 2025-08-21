from pathlib import Path

from fastapi import Depends

from askui.chat.api.dependencies import WorkspaceDirDep
from askui.chat.api.files.dependencies import FileServiceDep
from askui.chat.api.files.service import FileService
from askui.chat.api.messages.service import MessageService
from askui.chat.api.messages.translator import MessageTranslator


def get_message_service(
    workspace_dir: Path = WorkspaceDirDep,
) -> MessageService:
    """Get MessagePersistedService instance."""
    return MessageService(workspace_dir)


MessageServiceDep = Depends(get_message_service)


def get_message_translator(
    file_service: FileService = FileServiceDep,
) -> MessageTranslator:
    return MessageTranslator(file_service)


MessageTranslatorDep = Depends(get_message_translator)
