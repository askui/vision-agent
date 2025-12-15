import json
import logging

from opentelemetry import context, trace
from typing_extensions import override

from askui.models.exceptions import MaxTokensExceededError, ModelRefusalError
from askui.models.models import ActModel
from askui.models.shared.agent_message_param import MessageParam, UsageParam
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

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


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
        accumulated_usage: UsageParam | None = None,
    ) -> UsageParam:
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
            accumulated_usage (UsageParam, optional): UsageParam to accumulate
                token usage across steps.

        Returns:
            UsageParam: Accumulated token usage with input_tokens and output_tokens.
        """
        if accumulated_usage is None:
            accumulated_usage = UsageParam(
                input_tokens=0,
                output_tokens=0,
                cache_creation_input_tokens=0,
                cache_read_input_tokens=0,
            )
        step_span = tracer.start_span("_step")
        ctx = trace.set_span_in_context(step_span)
        token = context.attach(ctx)
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
                temperature=settings.messages.temperature,
            )
            # Accumulate token usage
            if response_message.usage:
                accumulated_usage.input_tokens = (
                    accumulated_usage.input_tokens or 0
                ) + (response_message.usage.input_tokens or 0)
                accumulated_usage.output_tokens = (
                    accumulated_usage.output_tokens or 0
                ) + (response_message.usage.output_tokens or 0)
                accumulated_usage.cache_creation_input_tokens = (
                    accumulated_usage.cache_creation_input_tokens or 0
                ) + (response_message.usage.cache_creation_input_tokens or 0)
                accumulated_usage.cache_read_input_tokens = (
                    accumulated_usage.cache_read_input_tokens or 0
                ) + (response_message.usage.cache_read_input_tokens or 0)

            step_span.set_attributes(
                {
                    "cache_creation_input_tokens": (
                        response_message.usage.cache_creation_input_tokens or 0
                        if response_message.usage
                        else 0
                    ),
                    "cache_read_input_tokens": (
                        response_message.usage.cache_read_input_tokens or 0
                        if response_message.usage
                        else 0
                    ),
                    "input_tokens": response_message.usage.input_tokens or 0
                    if response_message.usage
                    else 0,
                    "output_tokens": response_message.usage.output_tokens or 0
                    if response_message.usage
                    else 0,
                }
            )
            message_by_assistant = self._call_on_message(
                on_message, response_message, truncation_strategy.messages
            )
            if message_by_assistant is None:
                context.detach(token)
                step_span.end()
                return accumulated_usage
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
                context.detach(token)
                step_span.end()
                return self._step(
                    model=model,
                    tool_collection=tool_collection,
                    on_message=on_message,
                    settings=settings,
                    truncation_strategy=truncation_strategy,
                    accumulated_usage=accumulated_usage,
                )
        context.detach(token)
        step_span.end()
        return accumulated_usage

    @tracer.start_as_current_span("_call_on_message")
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
    @tracer.start_as_current_span("act")
    def act(
        self,
        messages: list[MessageParam],
        model: str,
        on_message: OnMessageCb | None = None,
        tools: ToolCollection | None = None,
        settings: ActSettings | None = None,
    ) -> None:
        _settings = settings or ActSettings()
        _tool_collection = tools or ToolCollection()
        truncation_strategy = (
            self._truncation_strategy_factory.create_truncation_strategy(
                tools=_tool_collection.to_params(),
                system=_settings.messages.system or None,
                messages=messages,
                model=model,
            )
        )
        accumulated_usage = self._step(
            model=model,
            on_message=on_message or NULL_ON_MESSAGE_CB,
            settings=_settings,
            tool_collection=_tool_collection,
            truncation_strategy=truncation_strategy,
        )
        current_span = trace.get_current_span()
        current_span.set_attributes(
            {
                "input_tokens": accumulated_usage.input_tokens or 0,
                "output_tokens": accumulated_usage.output_tokens or 0,
                "cache_creation_input_tokens": (
                    accumulated_usage.cache_creation_input_tokens or 0
                ),
                "cache_read_input_tokens": accumulated_usage.cache_read_input_tokens
                or 0,
            }
        )

    @tracer.start_as_current_span("_use_tools")
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

        current_span = trace.get_current_span()
        for idx, tool_use_block in enumerate(tool_use_content_blocks, 1):
            current_span.set_attributes(
                {
                    f"id_{idx}": tool_use_block.id,
                    f"input_{idx}": json.dumps(tool_use_block.input),
                    f"name_{idx}": tool_use_block.name,
                    f"type_{idx}": tool_use_block.type,
                    f"caching_control_{idx}": str(tool_use_block.cache_control),
                }
            )

        content = tool_collection.run(tool_use_content_blocks)
        if len(content) == 0:
            return None

        return MessageParam(
            content=content,
            role="user",
        )

    @tracer.start_as_current_span("_handle_stop_reason")
    def _handle_stop_reason(self, message: MessageParam, max_tokens: int) -> None:
        if message.stop_reason == "max_tokens":
            raise MaxTokensExceededError(max_tokens)
        if message.stop_reason == "refusal":
            raise ModelRefusalError
