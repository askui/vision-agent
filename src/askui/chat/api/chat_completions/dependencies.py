from fastapi import Depends

from askui.chat.api.chat_completions.service import ChatCompletionService
from askui.chat.api.dependencies import SettingsDep
from askui.chat.api.messages.dependencies import MessageServiceDep
from askui.chat.api.messages.service import MessageService
from askui.chat.api.settings import Settings


def get_chat_completion_service(
    settings: Settings = SettingsDep,
    message_service: MessageService = MessageServiceDep,
) -> ChatCompletionService:
    """Get ChatCompletionService instance."""
    return ChatCompletionService(
        base_dir=settings.data_dir,
        anthropic_api_key=settings.anthropic_api_key,
        message_service=message_service,
    )


ChatCompletionServiceDep = Depends(get_chat_completion_service)
