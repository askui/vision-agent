from pathlib import Path

from fastapi import Depends

from askui.chat.api.dependencies import WorkspaceDirDep
from askui.chat.api.files.dependencies import FileServiceDep
from askui.chat.api.files.service import FileService
from askui.chat.api.messages.chat_history_manager import ChatHistoryManager
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


def get_chat_history_manager(
    message_service: MessageService = MessageServiceDep,
    message_translator: MessageTranslator = MessageTranslatorDep,
) -> ChatHistoryManager:
    return ChatHistoryManager(
        message_service=message_service,
        message_translator=message_translator,
    )


ChatHistoryManagerDep = Depends(get_chat_history_manager)
