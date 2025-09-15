from anthropic.types.beta import BetaTextBlockParam, BetaToolUnionParam

from askui.chat.api.messages.models import Message, MessageCreateParams
from askui.chat.api.messages.service import MessageService
from askui.chat.api.messages.translator import MessageTranslator
from askui.chat.api.models import ThreadId
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.truncation_strategies import TruncationStrategyFactory


class ChatHistoryManager:
    """
    Manages chat history by providing methods to retrieve and add messages.

    This service encapsulates the interaction between MessageService and MessageTranslator
    to provide a clean interface for managing chat history in the context of AI agents.
    """

    def __init__(
        self,
        message_service: MessageService,
        message_translator: MessageTranslator,
        truncation_strategy_factory: TruncationStrategyFactory,
    ) -> None:
        """
        Initialize the chat history manager.

        Args:
            message_service (MessageService): Service for managing message persistence.
            message_translator (MessageTranslator): Translator for converting between
                message formats.
            truncation_strategy_factory (TruncationStrategyFactory): Factory for creating truncation strategies.
        """
        self._message_service = message_service
        self._message_translator = message_translator
        self._message_content_translator = message_translator.content_translator
        self._truncation_strategy_factory = truncation_strategy_factory

    async def retrieve_message_params(
        self,
        thread_id: ThreadId,
        model: str,
        system: str | list[BetaTextBlockParam] | None,
        tools: list[BetaToolUnionParam],
    ) -> list[MessageParam]:
        truncation_strategy = (
            self._truncation_strategy_factory.create_truncation_strategy(
                system=system,
                tools=tools,
                messages=[],
                model=model,
            )
        )
        for msg in self._message_service.iter(thread_id=thread_id):
            anthropic_message = await self._message_translator.to_anthropic(msg)
            truncation_strategy.append_message(anthropic_message)
        return truncation_strategy.messages

    async def append_message(
        self,
        thread_id: ThreadId,
        assistant_id: str | None,
        run_id: str,
        message: MessageParam,
    ) -> Message:
        """
        Add a message to the chat history and return both the created message and original message param.

        This method creates a message in the database and returns both the created
        message object and the original message parameter for further processing.

        Args:
            thread_id (ThreadId): The thread ID to add the message to.
            assistant_id (str | None): The assistant ID if the message is from an assistant.
            run_id (str): The run ID associated with this message.
            message (MessageParam): The message to add.

        Returns:
            Message: The created message object
        """
        return self._message_service.create(
            thread_id=thread_id,
            params=MessageCreateParams(
                assistant_id=assistant_id if message.role == "assistant" else None,
                role=message.role,
                content=await self._message_content_translator.from_anthropic(
                    message.content
                ),
                run_id=run_id,
            ),
        )
