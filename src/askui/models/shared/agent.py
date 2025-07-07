from typing_extensions import override

from askui.models.exceptions import MaxTokensExceededError, ModelRefusalError
from askui.models.models import ActModel
from askui.models.shared.agent_message_param import (
    ImageBlockParam,
    MessageParam,
    TextBlockParam,
)
from askui.models.shared.agent_on_message_cb import (
    NULL_ON_MESSAGE_CB,
    OnMessageCb,
    OnMessageCbParam,
)
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.settings import ActSettings
from askui.models.shared.tools import Tool, ToolCollection
from askui.reporting import NULL_REPORTER, Reporter

from ...logger import logger


class Agent(ActModel):
    """Base class for agents that can execute autonomous actions.

    This class provides common functionality for both AskUI and Anthropic agents,
    including tool handling, message processing, and image filtering.

    Args:
        messages_api (MessagesApi): Messages API for creating messages.
        reporter (Reporter, optional): The reporter for logging messages and actions.
            Defaults to `NULL_REPORTER`.
    """

    def __init__(
        self,
        messages_api: MessagesApi,
        reporter: Reporter = NULL_REPORTER,
    ) -> None:
        self._messages_api = messages_api
        self._reporter = reporter

    def _step(
        self,
        messages: list[MessageParam],
        model: str,
        on_message: OnMessageCb,
        settings: ActSettings,
        tool_collection: ToolCollection,
    ) -> None:
        """Execute a single step in the conversation.

        If the last message is an assistant's message and does not contain tool use
        blocks, this method is going to return immediately, as there is nothing to act
        upon.

        Args:
            messages (list[MessageParam]): The message history.
                Contains at least one message.
            model (str): The model to use for message creation.
            on_message (OnMessageCb): Callback on new messages
            settings (AgentSettings): The settings for the step.
            tool_collection (ToolCollection): The tools to use for the step.

        Returns:
            None
        """
        if settings.only_n_most_recent_images:
            messages = self._maybe_filter_to_n_most_recent_images(
                messages,
                settings.only_n_most_recent_images,
                settings.image_truncation_threshold,
            )

        if messages[-1].role == "user":
            response_message = self._messages_api.create_message(
                messages=messages,
                model=model,
                tools=tool_collection,
                max_tokens=settings.messages.max_tokens,
                betas=settings.messages.betas,
                system=settings.messages.system,
                thinking=settings.messages.thinking,
                tool_choice=settings.messages.tool_choice,
            )
            message_by_assistant = self._call_on_message(
                on_message, response_message, messages
            )
            if message_by_assistant is None:
                return
            message_by_assistant_dict = message_by_assistant.model_dump(mode="json")
            logger.debug(message_by_assistant_dict)
            messages.append(message_by_assistant)
            self._reporter.add_message(
                self.__class__.__name__, message_by_assistant_dict
            )
        else:
            message_by_assistant = messages[-1]

        self._handle_stop_reason(message_by_assistant, settings.messages.max_tokens)
        if tool_result_message := self._use_tools(
            message_by_assistant, tool_collection
        ):
            if tool_result_message := self._call_on_message(
                on_message, tool_result_message, messages
            ):
                tool_result_message_dict = tool_result_message.model_dump(mode="json")
                logger.debug(tool_result_message_dict)
                messages.append(tool_result_message)
                self._step(
                    messages=messages,
                    model=model,
                    tool_collection=tool_collection,
                    on_message=on_message,
                    settings=settings,
                )

    def _call_on_message(
        self,
        on_message: OnMessageCb | None,
        message: MessageParam,
        messages: list[MessageParam],
    ) -> MessageParam | None:
        if on_message is None:
            return message
        return on_message(OnMessageCbParam(message=message, messages=messages))

    @override
    def act(
        self,
        messages: list[MessageParam],
        model_choice: str,
        on_message: OnMessageCb | None = None,
        tools: list[Tool] | None = None,
        settings: ActSettings | None = None,
    ) -> None:
        _settings = settings or ActSettings()
        self._step(
            messages=messages,
            model=_settings.messages.model or model_choice,
            on_message=on_message or NULL_ON_MESSAGE_CB,
            settings=_settings,
            tool_collection=ToolCollection(tools),
        )

    def _use_tools(
        self,
        message: MessageParam,
        tool_collection: ToolCollection,
    ) -> MessageParam | None:
        """Process tool use blocks in a message.

        Args:
            message (MessageParam): The message containing tool use blocks.

        Returns:
            MessageParam | None: A message containing tool results or `None`
                if no tools were used.
        """
        if isinstance(message.content, str):
            return None

        tool_use_content_blocks = [
            content_block
            for content_block in message.content
            if content_block.type == "tool_use"
        ]
        content = tool_collection.run(tool_use_content_blocks)
        if len(content) == 0:
            return None

        return MessageParam(
            content=content,
            role="user",
        )

    @staticmethod
    def _maybe_filter_to_n_most_recent_images(
        messages: list[MessageParam],
        images_to_keep: int | None,
        min_removal_threshold: int,
    ) -> list[MessageParam]:
        """
        Filter the message history in-place to keep only the most recent images,
        according to the given chunking policy.

        Args:
            messages (list[MessageParam]): The message history.
            images_to_keep (int | None): Number of most recent images to keep.
            min_removal_threshold (int): Minimum number of images to remove at once.

        Returns:
            list[MessageParam]: The filtered message history.
        """
        if images_to_keep is None:
            return messages

        tool_result_blocks = [
            item
            for message in messages
            for item in (message.content if isinstance(message.content, list) else [])
            if item.type == "tool_result"
        ]
        total_images = sum(
            1
            for tool_result in tool_result_blocks
            if not isinstance(tool_result.content, str)
            for content in tool_result.content
            if content.type == "image"
        )
        images_to_remove = total_images - images_to_keep
        if images_to_remove < min_removal_threshold:
            return messages
        # for better cache behavior, we want to remove in chunks
        images_to_remove -= images_to_remove % min_removal_threshold
        if images_to_remove <= 0:
            return messages

        # Remove images from the oldest tool_result blocks first
        for tool_result in tool_result_blocks:
            if images_to_remove <= 0:
                break
            if isinstance(tool_result.content, list):
                new_content: list[TextBlockParam | ImageBlockParam] = []
                for content in tool_result.content:
                    if content.type == "image" and images_to_remove > 0:
                        images_to_remove -= 1
                        continue
                    new_content.append(content)
                tool_result.content = new_content
        return messages

    def _handle_stop_reason(self, message: MessageParam, max_tokens: int) -> None:
        if message.stop_reason == "max_tokens":
            raise MaxTokensExceededError(max_tokens)
        if message.stop_reason == "refusal":
            raise ModelRefusalError
