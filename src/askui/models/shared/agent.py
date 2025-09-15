from typing_extensions import override

from askui.models.exceptions import MaxTokensExceededError, ModelRefusalError
from askui.models.models import ActModel
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import (
    NULL_ON_MESSAGE_CB,
    OnMessageCb,
    OnMessageCbParam,
)
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.settings import ActSettings
from askui.models.shared.tools import ToolCollection
from askui.models.shared.truncation_strategies import (
    SimpleTruncationStrategyFactory,
    TruncationStrategy,
    TruncationStrategyFactory,
)
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
        truncation_strategy (TruncationStrategyFactory, optional): The truncation
            strategy factory to use. This is used to create the truncation strategy
            to truncate the message history before sending it to the model.
            Defaults to `SimpleTruncationStrategyFactory`.
    """

    def __init__(
        self,
        messages_api: MessagesApi,
        reporter: Reporter = NULL_REPORTER,
        truncation_strategy_factory: TruncationStrategyFactory | None = None,
    ) -> None:
        self._messages_api = messages_api
        self._reporter = reporter
        self._truncation_strategy_factory = (
            truncation_strategy_factory or SimpleTruncationStrategyFactory()
        )

    def _step(
        self,
        model: str,
        on_message: OnMessageCb,
        settings: ActSettings,
        tool_collection: ToolCollection,
        truncation_strategy: TruncationStrategy,
    ) -> None:
        """Execute a single step in the conversation.

        If the last message is an assistant's message and does not contain tool use
        blocks, this method is going to return immediately, as there is nothing to act
        upon.

        Args:
            model (str): The model to use for message creation.
            on_message (OnMessageCb): Callback on new messages
            settings (AgentSettings): The settings for the step.
            tool_collection (ToolCollection): The tools to use for the step.
            truncation_strategy (TruncationStrategy): The truncation strategy to use
                for the step.

        Returns:
            None
        """
        if truncation_strategy.messages[-1].role == "user":
            response_message = self._messages_api.create_message(
                messages=truncation_strategy.messages,
                model=model,
                tools=tool_collection,
                max_tokens=settings.messages.max_tokens,
                betas=settings.messages.betas,
                system=settings.messages.system,
                thinking=settings.messages.thinking,
                tool_choice=settings.messages.tool_choice,
            )
            message_by_assistant = self._call_on_message(
                on_message, response_message, truncation_strategy.messages
            )
            if message_by_assistant is None:
                return
            message_by_assistant_dict = message_by_assistant.model_dump(mode="json")
            logger.debug(message_by_assistant_dict)
            truncation_strategy.append_message(message_by_assistant)
            self._reporter.add_message(
                self.__class__.__name__, message_by_assistant_dict
            )
        else:
            message_by_assistant = truncation_strategy.messages[-1]
        self._handle_stop_reason(message_by_assistant, settings.messages.max_tokens)
        if tool_result_message := self._use_tools(
            message_by_assistant, tool_collection
        ):
            if tool_result_message := self._call_on_message(
                on_message, tool_result_message, truncation_strategy.messages
            ):
                tool_result_message_dict = tool_result_message.model_dump(mode="json")
                logger.debug(tool_result_message_dict)
                truncation_strategy.append_message(tool_result_message)
                self._step(
                    model=model,
                    tool_collection=tool_collection,
                    on_message=on_message,
                    settings=settings,
                    truncation_strategy=truncation_strategy,
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
        tools: ToolCollection | None = None,
        settings: ActSettings | None = None,
    ) -> None:
        _settings = settings or ActSettings()
        _model = _settings.messages.model or model_choice
        _tool_collection = tools or ToolCollection()
        truncation_strategy = (
            self._truncation_strategy_factory.create_truncation_strategy(
                tools=_tool_collection.to_params(),
                system=_settings.messages.system or None,
                messages=messages,
                model=_model,
            )
        )
        self._step(
            model=_model,
            on_message=on_message or NULL_ON_MESSAGE_CB,
            settings=_settings,
            tool_collection=_tool_collection,
            truncation_strategy=truncation_strategy,
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

    def _handle_stop_reason(self, message: MessageParam, max_tokens: int) -> None:
        if message.stop_reason == "max_tokens":
            raise MaxTokensExceededError(max_tokens)
        if message.stop_reason == "refusal":
            raise ModelRefusalError
