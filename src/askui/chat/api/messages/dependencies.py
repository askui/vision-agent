from fastapi import Depends

from askui.chat.api.db.session import SessionDep
from askui.chat.api.files.dependencies import FileServiceDep
from askui.chat.api.files.service import FileService
from askui.chat.api.messages.chat_history_manager import ChatHistoryManager
from askui.chat.api.messages.service import MessageService
from askui.chat.api.messages.translator import MessageTranslator
from askui.models.shared.truncation_strategies import (
    SimpleTruncationStrategyFactory,
    TruncationStrategyFactory,
)


def get_message_service(
    session: SessionDep,
) -> MessageService:
    """Get MessageService instance."""
    return MessageService(session)


MessageServiceDep = Depends(get_message_service)


def get_message_translator(
    file_service: FileService = FileServiceDep,
) -> MessageTranslator:
    return MessageTranslator(file_service)


MessageTranslatorDep = Depends(get_message_translator)


def get_truncation_strategy_factory() -> TruncationStrategyFactory:
    return SimpleTruncationStrategyFactory()


TruncationStrategyFactoryDep = Depends(get_truncation_strategy_factory)


def get_chat_history_manager(
    message_service: MessageService = MessageServiceDep,
    message_translator: MessageTranslator = MessageTranslatorDep,
    truncation_strategy_factory: TruncationStrategyFactory = TruncationStrategyFactoryDep,
) -> ChatHistoryManager:
    return ChatHistoryManager(
        message_service=message_service,
        message_translator=message_translator,
        truncation_strategy_factory=truncation_strategy_factory,
    )


ChatHistoryManagerDep = Depends(get_chat_history_manager)
