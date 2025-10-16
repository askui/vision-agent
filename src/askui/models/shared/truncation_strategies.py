from dataclasses import dataclass
from typing import Annotated

from anthropic.types.beta import BetaTextBlockParam, BetaToolUnionParam
from pydantic import Field
from typing_extensions import override

from askui.models.shared.agent_message_param import (
    CacheControlEphemeralParam,
    MessageParam,
    TextBlockParam,
)
from askui.models.shared.token_counter import SimpleTokenCounter, TokenCounter

# needs to be below limits imposed by endpoint
MAX_INPUT_TOKENS = 100_000

# see https://docs.anthropic.com/en/api/messages#body-messages
MAX_MESSAGES = 100_000


class TruncationStrategy:
    """Abstract base class for truncation strategies."""

    def __init__(
        self,
        tools: list[BetaToolUnionParam] | None,
        system: str | list[BetaTextBlockParam] | None,
        messages: list[MessageParam],
        model: str,
    ) -> None:
        self._tools = tools
        self._messages = messages
        self._system = system
        self._model = model

    def append_message(self, message: MessageParam) -> None:
        self._messages.append(message)

    @property
    def messages(self) -> list[MessageParam]:
        """Get the truncated messages."""
        return self._messages


def _is_tool_result_user_message(message: MessageParam) -> bool:
    return message.role == "user" and (
        isinstance(message.content, list)
        and any(block.type == "tool_result" for block in message.content)
    )


def _is_tool_use_assistant_message(message: MessageParam) -> bool:
    return message.role == "assistant" and (
        isinstance(message.content, list)
        and any(block.type == "tool_use" for block in message.content)
    )


def _is_end_of_loop(
    message: MessageParam, previous_message: MessageParam | None
) -> bool:
    return (
        not _is_tool_result_user_message(message)
        and previous_message is not None
        and previous_message.role == "assistant"
    )


@dataclass(kw_only=True)
class MessageContainer:
    index: int
    message: MessageParam
    tokens: int


class SimpleTruncationStrategy(TruncationStrategy):
    """Simple truncation strategy that truncates messages to stay within token and
    message limits.

    Clusters messages into "tool calling loops" - sequences of messages starting with
    a user message (not containing `tool_result` blocks) or the first message, and
    ending with an assistant message before the next such user message or the last
    message.

    The last tool calling loop is called the "open loop" and represents the current
    conversation context being worked on.

    Truncation follows this priority order until both token and message thresholds
    are met:
    1. Remove tool calling turns (assistant tool_use + user tool_result pairs)
       from closed loops
    2. Remove entire closed loops (except first and last which usually contain
       the most important context)
    3. Remove the first loop if it's not the open loop
    4. Remove tool calling turns from the open loop (except the first and last turn)
       - We need to preserve the thinking block in first turn of open loop.
       - Also these are the blocks with the most important context.
    5. Raise ValueError if still exceeds limits after all truncation attempts

    We truncate until a threshold that is way below the limits to make sure that
    the threshold is not reached immediately afterwards again and caching can work
    in that time.

    Args:
        tools (list[BetaToolUnionParam] | None): Available tools for the conversation
        system (str | list[BetaTextBlockParam] | None): System prompt or blocks
        messages (list[MessageParam]): Initial conversation messages
        model (str): Model name for token counting
        max_input_tokens (int, optional): Maximum input tokens allowed. Defaults to
            100,000.
        input_token_truncation_threshold (float, optional): Fraction of max tokens to
            truncate at. Defaults to 0.75.
        max_messages (int, optional): Maximum messages allowed. Defaults to 100,000.
        message_truncation_threshold (float, optional): Fraction of max messages to
            truncate at. Defaults to 0.75.
        token_counter (TokenCounter | None, optional): Token counter instance. Defaults
            to SimpleTokenCounter.

    Raises:
        ValueError: If conversation cannot be truncated below limits after all attempts.
    """

    def __init__(
        self,
        tools: list[BetaToolUnionParam] | None,
        system: str | list[BetaTextBlockParam] | None,
        messages: list[MessageParam],
        model: str,
        max_input_tokens: int = MAX_INPUT_TOKENS,
        input_token_truncation_threshold: Annotated[
            float, Field(gt=0.0, lt=1.0)
        ] = 0.75,
        max_messages: int = MAX_MESSAGES,
        message_truncation_threshold: Annotated[float, Field(gt=0.0, lt=1.0)] = 0.75,
        token_counter: TokenCounter | None = None,
    ) -> None:
        super().__init__(
            tools=tools,
            system=system,
            messages=messages,
            model=model,
        )
        self._max_input_tokens = max_input_tokens
        self._max_input_tokens_after_truncation = int(
            input_token_truncation_threshold * max_input_tokens
        )
        self._max_messages = max_messages
        self._max_messages_after_truncation = int(
            message_truncation_threshold * max_messages
        )
        self._token_counter = token_counter or SimpleTokenCounter()
        self._token_counts = self._token_counter.count_tokens(
            tools=tools,
            system=system,
            messages=messages,
        )

    @override
    def append_message(self, message: MessageParam) -> None:
        super().append_message(message)
        self._token_counts.append_message_tokens(
            self._token_counter.count_tokens(messages=[message]).total
        )
        if self._should_truncate():
            self._truncate()

    def _should_truncate(self) -> bool:
        return (
            self._token_counts.total > self._max_input_tokens
            or len(self._messages) > self._max_messages
        )

    @property
    @override
    def messages(self) -> list[MessageParam]:
        self._move_cache_control_to_last_non_tool_result_user_message()
        return self._messages

    def _move_cache_control_to_last_non_tool_result_user_message(self) -> None:
        found_last = False
        for message in reversed(self._messages):
            if message.role == "user" and not _is_tool_result_user_message(message):
                if not found_last:
                    found_last = True
                    if isinstance(message.content, str):
                        message.content = [
                            TextBlockParam(
                                text=message.content,
                                cache_control=CacheControlEphemeralParam(
                                    type="ephemeral",
                                ),
                            )
                        ]
                    elif len(message.content) > 0:
                        last_content = message.content[-1]
                        if hasattr(last_content, "cache_control"):
                            last_content.cache_control = CacheControlEphemeralParam(
                                type="ephemeral",
                            )
                else:
                    if isinstance(message.content, list) and message.content:
                        last_content = message.content[-1]
                        if hasattr(last_content, "cache_control"):
                            last_content.cache_control = None
                    break

    def _truncate(self) -> None:  # noqa: C901
        messages_to_remove_min = min(
            len(self._messages) - self._max_messages_after_truncation, 0
        )
        tokens_to_remove_min = max(
            self._token_counts.total - self._max_input_tokens_after_truncation, 0
        )
        messages_removed_indices: set[int] = set()
        tokens_removed = 0
        loops = self._cluster_into_tool_calling_loops()

        # 1. Remove tool calling turns within closed loops
        last_message_was_tool_use_assistant_message = False
        for closed_loop in loops[:-1]:
            for message_container in closed_loop:
                if last_message_was_tool_use_assistant_message:
                    messages_removed_indices.add(message_container.index)
                    tokens_removed += message_container.tokens
                    if (
                        len(messages_removed_indices) >= messages_to_remove_min
                        or tokens_removed >= tokens_to_remove_min
                    ):
                        self._remove_messages(messages_removed_indices)
                        return

                last_message_was_tool_use_assistant_message = False
                if _is_tool_use_assistant_message(message_container.message):
                    last_message_was_tool_use_assistant_message = True
                    messages_removed_indices.add(message_container.index)
                    tokens_removed += message_container.tokens

        # 2. Remove loops except first and last (open) loop
        for closed_loop in loops[1:-1]:
            for message_container in closed_loop:
                if message_container.index not in messages_removed_indices:
                    messages_removed_indices.add(message_container.index)
                    tokens_removed += message_container.tokens
            if (
                len(messages_removed_indices) >= messages_to_remove_min
                or tokens_removed >= tokens_to_remove_min
            ):
                self._remove_messages(messages_removed_indices)
                return

        # 3. Remove first loop if it is not the last (open) loop
        if len(loops) > 1:
            for message_container in loops[0]:
                if message_container.index not in messages_removed_indices:
                    messages_removed_indices.add(message_container.index)
                    tokens_removed += message_container.tokens
            if (
                len(messages_removed_indices) >= messages_to_remove_min
                or tokens_removed >= tokens_to_remove_min
            ):
                self._remove_messages(messages_removed_indices)
                return

        # 4. Remove tool calling turns within open loop except last turn
        if len(loops) > 0:
            open_loop = loops[-1]
            last_message_was_tool_use_assistant_message = False
            for i, message_container in enumerate(open_loop):
                if last_message_was_tool_use_assistant_message:
                    messages_removed_indices.add(message_container.index)
                    tokens_removed += message_container.tokens
                    if (
                        len(messages_removed_indices) >= messages_to_remove_min
                        or tokens_removed >= tokens_to_remove_min
                    ):
                        self._remove_messages(messages_removed_indices)
                        return

                last_message_was_tool_use_assistant_message = False
                if (
                    _is_tool_use_assistant_message(message_container.message)
                    and 1 < i < len(open_loop) - 2
                ):
                    last_message_was_tool_use_assistant_message = True
                    messages_removed_indices.add(message_container.index)
                    tokens_removed += message_container.tokens

        # Everything that is left is the last non-tool-result user message
        # and the last (open or closed) tool calling turn (if there is one)
        error_msg = "Conversation too long. Please start a new conversation."
        raise ValueError(error_msg)

    def _remove_messages(self, indices: set[int]) -> None:
        self._token_counts.reset_message_tokens(
            [
                self._token_counts.retrieve_message_tokens(i)
                for i, _ in enumerate(self._messages)
                if i not in indices
            ]
        )
        self._messages = [
            message for i, message in enumerate(self._messages) if i not in indices
        ]

    def _cluster_into_tool_calling_loops(self) -> list[list[MessageContainer]]:
        loops: list[list[MessageContainer]] = []
        current_loop: list[MessageContainer] = []
        for i, message in enumerate(self._messages):
            if _is_end_of_loop(
                message, current_loop[-1].message if current_loop else None
            ):
                loops.append(current_loop)
                current_loop = []
            current_loop.append(
                MessageContainer(
                    index=i,
                    message=message,
                    tokens=self._token_counts.retrieve_message_tokens(i),
                ),
            )
        loops.append(current_loop)
        return loops


class TruncationStrategyFactory:
    def create_truncation_strategy(
        self,
        tools: list[BetaToolUnionParam] | None,
        system: str | list[BetaTextBlockParam] | None,
        messages: list[MessageParam],
        model: str,
    ) -> TruncationStrategy:
        return TruncationStrategy(
            tools=tools,
            system=system,
            messages=messages,
            model=model,
        )


class SimpleTruncationStrategyFactory(TruncationStrategyFactory):
    def __init__(
        self,
        max_input_tokens: int = MAX_INPUT_TOKENS,
        input_token_truncation_threshold: Annotated[
            float, Field(gt=0.0, lt=1.0)
        ] = 0.75,
        max_messages: int = MAX_MESSAGES,
        message_truncation_threshold: Annotated[float, Field(gt=0.0, lt=1.0)] = 0.75,
        token_counter: TokenCounter | None = None,
    ) -> None:
        self._max_input_tokens = max_input_tokens
        self._input_token_truncation_threshold = input_token_truncation_threshold
        self._max_messages = max_messages
        self._message_truncation_threshold = message_truncation_threshold
        self._token_counter = token_counter or SimpleTokenCounter()

    def create_truncation_strategy(
        self,
        tools: list[BetaToolUnionParam] | None,
        system: str | list[BetaTextBlockParam] | None,
        messages: list[MessageParam],
        model: str,
    ) -> TruncationStrategy:
        return SimpleTruncationStrategy(
            tools=tools,
            system=system,
            messages=messages,
            model=model,
            max_input_tokens=self._max_input_tokens,
            input_token_truncation_threshold=self._input_token_truncation_threshold,
            max_messages=self._max_messages,
            message_truncation_threshold=self._message_truncation_threshold,
            token_counter=self._token_counter,
        )
