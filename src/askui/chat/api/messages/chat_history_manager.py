from askui.chat.api.messages.models import Message, MessageCreateParams
from askui.chat.api.messages.service import MessageService
from askui.chat.api.messages.translator import MessageTranslator
from askui.chat.api.models import ThreadId
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCbParam
from askui.utils.api_utils import LIST_LIMIT_MAX, ListQuery


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
    ) -> None:
        """
        Initialize the chat history manager.

        Args:
            message_service (MessageService): Service for managing message persistence.
            message_translator (MessageTranslator): Translator for converting between
                message formats.
        """
        self._message_service = message_service
        self._message_translator = message_translator
        self._message_content_translator = message_translator.content_translator

    async def retrieve(self, thread_id: ThreadId) -> list[MessageParam]:
        """
        Retrieve the message history for a thread, converted to Anthropic format.

        Args:
            thread_id (ThreadId): The thread ID to retrieve messages for.

        Returns:
            list[MessageParam]: List of messages in Anthropic format, ordered by creation time.
        """
        return [
            await self._message_translator.to_anthropic(msg)
            for msg in self._message_service.list_(
                thread_id=thread_id,
                query=ListQuery(limit=LIST_LIMIT_MAX, order="asc"),
            ).data
        ]

    async def append(
        self,
        thread_id: ThreadId,
        assistant_id: str | None,
        run_id: str,
        on_message_cb_param: OnMessageCbParam,
    ) -> Message:
        """
        Add a message to the chat history and return both the created message and original message param.

        This method creates a message in the database and returns both the created
        message object and the original message parameter for further processing.

        Args:
            thread_id (ThreadId): The thread ID to add the message to.
            assistant_id (str | None): The assistant ID if the message is from an assistant.
            run_id (str): The run ID associated with this message.
            on_message_cb_param (OnMessageCbParam): The message callback parameter
                containing the message to add.

        Returns:
            Message: The created message object
        """
        return self._message_service.create(
            thread_id=thread_id,
            params=MessageCreateParams(
                assistant_id=assistant_id
                if on_message_cb_param.message.role == "assistant"
                else None,
                role=on_message_cb_param.message.role,
                content=await self._message_content_translator.from_anthropic(
                    on_message_cb_param.message.content
                ),
                run_id=run_id,
            ),
        )
