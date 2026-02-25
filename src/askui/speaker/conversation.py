"""Conversation class for managing speaker-based agent interactions."""

import logging
from typing import TYPE_CHECKING, Any

from opentelemetry import trace

tracer = trace.get_tracer(__name__)

from askui.model_providers.detection_provider import DetectionProvider
from askui.model_providers.image_qa_provider import ImageQAProvider
from askui.model_providers.vlm_provider import VlmProvider
from askui.models.shared.agent_message_param import (
    MessageParam,
    ToolResultBlockParam,
    ToolUseBlockParam,
    UsageParam,
)
from askui.models.shared.agent_on_message_cb import (
    NULL_ON_MESSAGE_CB,
    OnMessageCb,
    OnMessageCbParam,
)
from askui.models.shared.settings import ActSettings
from askui.models.shared.tools import ToolCollection
from askui.models.shared.truncation_strategies import (
    SimpleTruncationStrategyFactory,
    TruncationStrategy,
    TruncationStrategyFactory,
)
from askui.reporting import NULL_REPORTER, Reporter

from .speaker import SpeakerResult, Speakers

if TYPE_CHECKING:
    from askui.utils.caching.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class ConversationException(Exception):
    """Exception raised during conversation execution."""

    def __init__(self, msg: str) -> None:
        super().__init__(msg)
        self.msg = msg


class Conversation:
    """Manages conversation state and delegates execution to speakers.

    The Conversation holds all model providers (`VlmProvider`, `ImageQAProvider`,
    `DetectionProvider`), message history, truncation strategy, token usage,
    and current speaker. It orchestrates the conversation by delegating each
    step to the appropriate speaker.

    Speakers access the model providers via the conversation instance
    (e.g., `conversation.vlm_provider`).

    Args:
        speakers: Collection of speakers to use
        vlm_provider: VLM provider for LLM API calls
        image_qa_provider: Image Q&A provider (optional)
        detection_provider: Detection provider (optional)
        reporter: Reporter for logging messages and actions
        cache_manager: Cache manager for recording/playback (optional)
        truncation_strategy_factory: Factory for creating truncation strategies
    """

    def __init__(
        self,
        speakers: Speakers,
        vlm_provider: VlmProvider,
        image_qa_provider: ImageQAProvider | None = None,
        detection_provider: DetectionProvider | None = None,
        reporter: Reporter = NULL_REPORTER,
        cache_manager: "CacheManager | None" = None,
        truncation_strategy_factory: TruncationStrategyFactory | None = None,
    ) -> None:
        """Initialize conversation with speakers and model providers."""
        if not speakers:
            msg = "At least one speaker must be provided"
            raise ValueError(msg)

        # Speakers and current state
        self.speakers = speakers
        self.current_speaker = speakers[speakers.default_speaker]
        self.accumulated_usage = UsageParam()

        # Model providers - accessible by speakers via conversation instance
        self.vlm_provider = vlm_provider
        self.image_qa_provider = image_qa_provider
        self.detection_provider = detection_provider

        # Infrastructure
        self._reporter = reporter
        self._cache_manager = cache_manager
        self._truncation_strategy_factory = (
            truncation_strategy_factory or SimpleTruncationStrategyFactory()
        )
        self._truncation_strategy: TruncationStrategy | None = None

        # State for current execution (set in start())
        self.settings: ActSettings = ActSettings()
        self.tools: ToolCollection = ToolCollection()
        self._on_message: OnMessageCb = NULL_ON_MESSAGE_CB
        self._reporters: list[Reporter] = []

        # Cache execution context (for communication between tools and CacheExecutor)
        self.cache_execution_context: dict[str, Any] = {}

    @tracer.start_as_current_span("conversation")
    def start(
        self,
        messages: list[MessageParam],
        on_message: OnMessageCb | None = None,
        tools: ToolCollection | None = None,
        settings: ActSettings | None = None,
        reporters: list[Reporter] | None = None,
    ) -> None:
        """Initialize conversation state and start execution loop.

        Model providers are accessed via self.vlm_provider, etc.
        Speakers can access them via conversation.vlm_provider.

        Args:
            messages: Initial message history
            on_message: Optional callback for each message
            tools: Available tools
            settings: Agent settings
            reporters: Optional list of additional reporters for this conversation
        """
        # Reset state
        self.accumulated_usage = UsageParam()

        # Store execution parameters
        self.settings = settings or ActSettings()
        self.tools = tools or ToolCollection()
        self._reporters = reporters or []
        self._on_message = on_message or NULL_ON_MESSAGE_CB

        # Initialize truncation strategy
        self._truncation_strategy = (
            self._truncation_strategy_factory.create_truncation_strategy(
                tools=self.tools.to_params(),
                system=self.settings.messages.system,
                messages=messages,
                model=self.vlm_provider.model_id,
            )
        )

        logger.info(
            "Starting conversation with speaker: %s", self.current_speaker.get_name()
        )

        # Execute conversation loop
        continue_execution = True
        while continue_execution:
            continue_execution = self._execute_loop()

        # Finish recording if cache_manager is active
        if self._cache_manager is not None:
            self._cache_manager.finish_recording(self.get_messages())

        # Report final usage
        self._reporter.add_usage_summary(self.accumulated_usage.model_dump())

    @tracer.start_as_current_span("step")
    def _execute_loop(self) -> bool:
        """Execute one step of the conversation loop with speakers.

        Each step includes:
        1. Get message(s) from active speaker
        2. Add messages to history (with on_message callback and reporting)
        3. Check if last message contains tool calls
        4. If yes, execute tools and create tool result message
        5. Add tool results to history
        6. Check if conversation should continue and switch current speaker if necessary

        Returns:
            True if loop should continue, False if done
        """
        speaker = self.current_speaker

        # Check if speaker can handle current state
        if not speaker.can_handle(self):
            logger.debug(
                "Speaker %s cannot handle current state, switching to default",
                self.current_speaker.get_name(),
            )
            self.switch_speaker(self.speakers.default_speaker)
            speaker = self.speakers[self.current_speaker.get_name()]

        # Execute one step with current speaker to get next message(s)
        logger.debug("Executing step with speaker: %s", speaker.get_name())
        result: SpeakerResult = speaker.handle_step(self, self._cache_manager)

        # Accumulate usage
        if result.usage:
            self._accumulate_usage(result.usage)

        # Add messages from speaker to conversation
        for message in result.messages_to_add:
            self._add_message(message)

        # Check if we need to execute tools from the last message
        if result.messages_to_add:
            last_message = result.messages_to_add[-1]
            tool_result_message = self._execute_tools_if_present(last_message)
            if tool_result_message:
                self._add_message(tool_result_message)

                # Handle side effects of tool execution (e.g., speaker switches)
                self._handle_tool_results(last_message, tool_result_message)

                # Check if cache execution was requested (set by _handle_tool_results)
                if self.cache_execution_context:
                    self.switch_speaker("CacheExecutor")

                return True

        return self._handle_result_status(result)

    @tracer.start_as_current_span("execute_tool")
    def _execute_tools_if_present(self, message: MessageParam) -> MessageParam | None:
        """Execute tools if the message contains tool use blocks.

        Args:
            message: Message to check for tool calls

        Returns:
            MessageParam with tool results, or None if no tools to execute
        """
        # Only process assistant messages
        if message.role != "assistant":
            return None

        # Check if content is a list (could contain tool use blocks)
        if isinstance(message.content, str):
            return None

        # Find tool use blocks
        tool_use_blocks = [
            block for block in message.content if block.type == "tool_use"
        ]

        if not tool_use_blocks:
            return None

        # Execute tools
        logger.debug("Executing %d tool(s)", len(tool_use_blocks))
        tool_results = self.tools.run(tool_use_blocks)

        if not tool_results:
            return None

        # Return tool results as a user message
        return MessageParam(content=tool_results, role="user")

    @tracer.start_as_current_span("handle_tool_result")
    def _handle_tool_results(
        self,
        assistant_message: MessageParam,
        tool_result_message: MessageParam,
    ) -> None:
        """Handle side effects of tool execution.

        Extracts tool use blocks and tool results from messages, then checks
        if specific tools require speaker switches or other actions.

        Currently handles:
        - ExecuteCachedTrajectory: Switches to CacheExecutor if successful

        Args:
            assistant_message: The assistant message containing tool use blocks
            tool_result_message: The user message containing tool results
        """
        # Extract tool use blocks from assistant message
        if isinstance(assistant_message.content, str):
            return

        tool_use_blocks: list[ToolUseBlockParam] = [
            block for block in assistant_message.content if block.type == "tool_use"
        ]

        if isinstance(tool_result_message.content, str):
            return

        tool_results: list[ToolResultBlockParam] = tool_result_message.content  # type: ignore[assignment]

        # Handle side effects for each tool
        for tool_use_block, tool_result in zip(
            tool_use_blocks, tool_results, strict=False
        ):
            # Check if ExecuteCachedTrajectory was called successfully
            if (
                tool_use_block.name == "execute_cached_executions_tool"
                and not tool_result.is_error
            ):
                # Extract parameters from tool call (input is dict at runtime)
                trajectory_file: str = tool_use_block.input["trajectory_file"]  # type: ignore[index]
                start_from_step_index: int = tool_use_block.input.get(  # type: ignore[attr-defined]
                    "start_from_step_index", 0
                )
                parameter_values: dict[str, str] = tool_use_block.input.get(  # type: ignore[attr-defined]
                    "parameter_values", {}
                )

                # Prepare cache execution context for CacheExecutor
                # CacheExecutor will validate and load the cache file
                self.cache_execution_context = {
                    "trajectory_file": trajectory_file,
                    "start_from_step_index": start_from_step_index,
                    "parameter_values": parameter_values,
                    "toolbox": self.tools,
                }

    def _add_message(self, message: MessageParam) -> None:
        """Add message to conversation history.

        Args:
            message: Message to add
        """
        if not self._truncation_strategy:
            logger.warning("No truncation strategy, cannot add message")
            return

        # Call on_message callback
        processed = self._call_on_message(message)
        if not processed:
            return

        # Add to truncation strategy
        self._truncation_strategy.append_message(processed)

        # Report to reporter
        self._reporter.add_message(
            self.current_speaker.get_name(), processed.model_dump(mode="json")
        )

    @tracer.start_as_current_span("message_callback")
    def _call_on_message(self, message: MessageParam) -> MessageParam | None:
        """Call on_message callback.

        Args:
            message: Message to pass to callback

        Returns:
            Processed message or None if cancelled by callback
        """
        messages = (
            self._truncation_strategy.messages if self._truncation_strategy else []
        )
        return self._on_message(OnMessageCbParam(message=message, messages=messages))

    @tracer.start_as_current_span("handle_result_status")
    def _handle_result_status(self, result: SpeakerResult) -> bool:
        """Handle speaker result status and determine if loop should continue.

        Args:
            result: Result from speaker

        Returns:
            True if loop should continue, False if done
        """
        if result.status == "done":
            logger.info("Conversation completed successfully")
            return False
        if result.status == "failed":
            logger.error("Conversation failed")
            return False
        if result.status == "switch_speaker":
            if result.next_speaker:
                self.switch_speaker(result.next_speaker)
            return True
        # status == "continue"
        return True

    @tracer.start_as_current_span("switch_speaker")
    def switch_speaker(self, speaker_name: str) -> None:
        """Switch to a different speaker.

        Args:
            speaker_name: Name of the speaker to switch to
        """
        old_speaker = self.current_speaker
        self.current_speaker = self.speakers[speaker_name]
        logger.info(
            "Switched speaker: %s => %s",
            old_speaker.get_name(),
            self.current_speaker.get_name(),
        )

    def get_messages(self) -> list[MessageParam]:
        """Get current message history from truncation strategy.

        Returns:
            List of messages in current conversation
        """
        return self._truncation_strategy.messages if self._truncation_strategy else []

    def get_truncation_strategy(self) -> TruncationStrategy | None:
        """Get current truncation strategy.

        Returns:
            Current truncation strategy or None if not initialized
        """
        return self._truncation_strategy

    def _accumulate_usage(self, step_usage: UsageParam) -> None:
        """Accumulate token usage statistics.

        Args:
            step_usage: Usage from a single step
        """
        self.accumulated_usage.input_tokens = (
            self.accumulated_usage.input_tokens or 0
        ) + (step_usage.input_tokens or 0)
        self.accumulated_usage.output_tokens = (
            self.accumulated_usage.output_tokens or 0
        ) + (step_usage.output_tokens or 0)
        self.accumulated_usage.cache_creation_input_tokens = (
            self.accumulated_usage.cache_creation_input_tokens or 0
        ) + (step_usage.cache_creation_input_tokens or 0)
        self.accumulated_usage.cache_read_input_tokens = (
            self.accumulated_usage.cache_read_input_tokens or 0
        ) + (step_usage.cache_read_input_tokens or 0)

        current_span = trace.get_current_span()
        current_span.set_attributes(
            {
                "input_tokens": step_usage.input_tokens or 0,
                "output_tokens": step_usage.output_tokens or 0,
                "cache_creation_input_tokens": (
                    step_usage.cache_creation_input_tokens or 0
                ),
                "cache_read_input_tokens": step_usage.cache_read_input_tokens or 0,
            }
        )
