"""Cache Executor speaker for executing cached trajectories."""

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from PIL import Image
from pydantic import BaseModel, Field
from typing_extensions import Literal

from askui.models.shared.agent_message_param import (
    MessageParam,
    TextBlockParam,
    ToolUseBlockParam,
)
from askui.utils.caching.cache_manager import CacheManager
from askui.utils.caching.cache_parameter_handler import CacheParameterHandler
from askui.utils.visual_validation import (
    compute_ahash,
    compute_hamming_distance,
    compute_phash,
    extract_region,
    find_recent_screenshot,
)

from .conversation import Conversation
from .speaker import Speaker, SpeakerResult

if TYPE_CHECKING:
    from askui.models.shared.settings import CacheFile
    from askui.models.shared.tools import ToolCollection

logger = logging.getLogger(__name__)


class ExecutionResult(BaseModel):
    """Result of executing a single step in a trajectory.

    Attributes:
        status: Execution status (SUCCESS, FAILED, NEEDS_AGENT, COMPLETED)
        step_index: Index of the step that was executed
        tool_result: The ToolResultBlockParam returned by the tool (if any),
            preserving proper data types like ImageBlockParam for screenshots
        error_message: Error message if execution failed
        screenshots_taken: List of screenshots captured during this step
        message_history: List of MessageParam representing the conversation history,
            with proper content types (ImageBlockParam, TextBlockParam, etc.)
    """

    status: Literal["SUCCESS", "FAILED", "NEEDS_AGENT", "COMPLETED"]
    step_index: int
    tool_result: Optional[Any] = None
    error_message: Optional[str] = None
    screenshots_taken: list[Any] = Field(default_factory=list)
    message_history: list[MessageParam] = Field(default_factory=list)


class CacheExecutor(Speaker):
    """Speaker that handles cached trajectory playback.

    This speaker generates messages from a cached trajectory:
    1. Get next step from cached trajectory (as tool use message)
    2. Track progress through the trajectory
    3. Pause for non-cacheable tools (switch to agent)
    4. Handle completion (switch to agent for verification)
    5. Handle failures (update metadata, switch to agent)

    Tool execution is handled by the Conversation class, not by this speaker.
    """

    def __init__(self, skip_visual_validation: bool = False) -> None:
        """Initialize Cache Executor speaker.

        Args:
            skip_visual_validation: If True, disable visual validation even if
                configured in the cache file. Defaults to False.
        """
        # Cache execution state
        self._executing_from_cache: bool = False
        self._cache_verification_pending: bool = False
        self._cache_file: "CacheFile | None" = None
        self._cache_file_path: str | None = None

        # Trajectory execution state (merged from TrajectoryExecutor)
        self._trajectory: list[ToolUseBlockParam] = []
        self._toolbox: ToolCollection | None = None
        self._parameter_values: dict[str, str] = {}
        self._delay_time: float = 0.5
        self._skip_visual_validation: bool = skip_visual_validation
        self._visual_validation_enabled: bool = False
        self._visual_validation_method: str = "phash"
        self._visual_validation_region_size: int = 100
        self._visual_validation_threshold: int = 10
        self._current_step_index: int = 0
        self._message_history: list[MessageParam] = []

    def can_handle(self, conversation: Conversation) -> bool:
        """Check if cache execution is active or should be activated.

        Args:
            conversation: The conversation instance

        Returns:
            True if in cache execution mode or if context has cache execution data
        """
        return self._executing_from_cache or bool(conversation.cache_execution_context)

    def handle_step(
        self, conversation: Conversation, cache_manager: CacheManager | None
    ) -> SpeakerResult:
        """Get next cached step message.

        This speaker only generates messages (tool use blocks from cache).
        Tool execution is handled by the Conversation class.

        Args:
            conversation: The conversation instance with current state

        Returns:
            SpeakerResult with the next cached tool use message
        """
        if cache_manager is None:
            error_msg = "CacheManager must be provided if executing from Cache"
            raise RuntimeError(error_msg)

        # Check if we need to activate cache execution from context
        if not self._executing_from_cache and conversation.cache_execution_context:
            try:
                self._activate_from_context(conversation.cache_execution_context)
                # Clear the context after successful activation
                conversation.cache_execution_context = {}
            except Exception as e:
                # Validation or loading failed - report error and switch back to agent
                logger.exception("Failed to activate cache execution")
                conversation.cache_execution_context = {}  # Clear context

                error_message = MessageParam(
                    role="user",
                    content=[
                        TextBlockParam(
                            type="text",
                            text=f"Cache execution failed: {e}",
                        )
                    ],
                )

                return SpeakerResult(
                    status="switch_speaker",
                    next_speaker="AskUIAgent",
                    messages_to_add=[error_message],
                )

        messages = conversation.get_messages()

        # Check if last message was a tool result - if so, move to next step
        if messages and messages[-1].role == "user":
            # Last message is tool result, check if it's from our current step
            if self._message_history and len(self._message_history) > 0:
                # Tool was executed, move to next step
                self._current_step_index += 1
                # Add delay between actions
                if self._current_step_index < len(self._trajectory):
                    time.sleep(self._delay_time)

        # Check if we have a trajectory
        if not self._trajectory or not self._toolbox:
            logger.error("Cache executor called but no trajectory or toolbox available")
            return SpeakerResult(
                status="switch_speaker",
                next_speaker="AskUIAgent",
            )

        # Get next step from cache (doesn't execute, just prepares the message)
        logger.debug("Getting next step from cache")
        result: ExecutionResult = self._get_next_step(conversation_messages=messages)

        # Handle result based on status
        return self._handle_result(result, cache_manager)

    def get_name(self) -> str:
        """Return speaker name.

        Returns:
            "CacheExecutor"
        """
        return "CacheExecutor"

    def _handle_result(
        self, result: ExecutionResult, cache_manager: CacheManager
    ) -> SpeakerResult:
        if result.status == "SUCCESS":
            return self._handle_success(result)
        if result.status == "NEEDS_AGENT":
            return self._handle_needs_agent(result)
        if result.status == "COMPLETED":
            return self._handle_completed(result)
        # FAILED
        return self._handle_failed(cache_manager, result)

    def _handle_success(self, result: ExecutionResult) -> SpeakerResult:
        """Handle successful preparation of next cache step.

        SUCCESS means we have a tool use message ready to be executed.
        The Conversation will execute the tool.

        Args:
            result: The execution result

        Returns:
            SpeakerResult with the tool use message
        """
        if not result.message_history:
            # No message to return, switch to agent
            return SpeakerResult(
                status="switch_speaker",
                next_speaker="AskUIAgent",
            )

        # Get assistant message (tool use)
        assistant_msg = result.message_history[-1]

        # Store this message for tracking
        self._message_history.append(assistant_msg)

        # Continue with cache execution
        # Conversation will execute the tool and loop back to us
        return SpeakerResult(
            status="continue",
            messages_to_add=[assistant_msg],
        )

    def _handle_needs_agent(self, result: ExecutionResult) -> SpeakerResult:
        """Handle cache execution pausing for non-cacheable tool.

        NEEDS_AGENT means cache execution paused because the next tool
        is not cacheable and requires the agent to handle it.

        Args:
            result: The execution result

        Returns:
            SpeakerResult to switch to agent
        """
        logger.info(
            "Paused cache execution at step %d "
            "(non-cacheable tool - agent will handle this step)",
            result.step_index,
        )
        self._executing_from_cache = False

        # Get the tool that needs to be executed
        tool_to_execute = result.tool_result

        # Create instruction message for agent
        if tool_to_execute:
            instruction_message = MessageParam(
                role="user",
                content=[
                    TextBlockParam(
                        type="text",
                        text=(
                            f"Cache execution paused at step {result.step_index}. "
                            "The previous steps were executed successfully "
                            f"from cache. The next step requires the "
                            f"'{tool_to_execute.name}' tool, which cannot be "
                            "executed from cache. Please execute this tool with "
                            "the necessary parameters."
                        ),
                    )
                ],
            )

            return SpeakerResult(
                status="switch_speaker",
                next_speaker="AskUIAgent",
                messages_to_add=[instruction_message],
            )

        # No tool info, just switch
        return SpeakerResult(
            status="switch_speaker",
            next_speaker="AskUIAgent",
        )

    def _handle_completed(self, result: ExecutionResult) -> SpeakerResult:  # noqa: ARG002
        """Handle cache execution completion.

        COMPLETED means all steps in the trajectory have been executed
        successfully. Request agent verification.

        Args:
            result: The execution result (not used, but required for consistency)

        Returns:
            SpeakerResult to switch to agent for verification
        """
        logger.info(
            "✓ Cache trajectory execution completed - requesting agent verification"
        )
        self._executing_from_cache = False
        self._cache_verification_pending = True

        # Inject verification request message
        verification_request = MessageParam(
            role="user",
            content=[
                TextBlockParam(
                    type="text",
                    text=(
                        "[CACHE EXECUTION COMPLETED]\n\n"
                        "The CacheExecutor has automatically executed"
                        f" {len(self._trajectory)} steps from the cached trajectory"
                        f" '{self._cache_file_path}'. All previous tool calls in this"
                        f" conversation were replayed from cache, not performed by the"
                        f" agent.\n\n Please verify if the cached execution correctly"
                        " achieved the target system state using the"
                        " verify_cache_execution tool."
                    ),
                )
            ],
        )

        return SpeakerResult(
            status="switch_speaker",
            next_speaker="AskUIAgent",
            messages_to_add=[verification_request],
        )

    def _handle_failed(
        self, cache_manager: CacheManager, result: ExecutionResult
    ) -> SpeakerResult:
        """Handle cache execution failure.

        Args:
            result: The execution result

        Returns:
            SpeakerResult to switch to agent
        """
        logger.error(
            "✗ Cache execution failed at step %d: %s",
            result.step_index,
            result.error_message,
        )
        self._executing_from_cache = False

        # Update cache metadata
        if self._cache_file and self._cache_file_path:
            self._update_metadata_on_failure(
                cache_manager=cache_manager,
                step_index=result.step_index,
                error_message=result.error_message or "Unknown error",
            )

        return SpeakerResult(
            status="switch_speaker",
            next_speaker="AskUIAgent",
        )

    def _activate_from_context(self, context: dict[str, Any]) -> None:
        """Activate cache execution from conversation context.

        Loads and validates the cache file, then sets up internal state for execution.
        Raises exceptions if validation fails.

        Args:
            context: Dict containing cache execution parameters:
                - trajectory_file: Path to the cache file
                - start_from_step_index: Step to start from
                - parameter_values: Parameter values for the trajectory
                - toolbox: ToolCollection to use

        Raises:
            FileNotFoundError: If cache file doesn't exist
            ValueError: If validation fails (step index, parameters, etc.)
            Exception: If cache file can't be loaded
        """
        # Extract parameters
        trajectory_file: str = context["trajectory_file"]
        start_from_step_index: int = context.get("start_from_step_index", 0)
        parameter_values: dict[str, Any] = context.get("parameter_values", {})
        toolbox: ToolCollection = context["toolbox"]

        logger.debug("Activating cache execution from: %s", trajectory_file)

        # Load and validate cache file
        if not self._cache_file_path or self._cache_file_path != trajectory_file:
            self._cache_file_path = trajectory_file
            self.cache_file = CacheManager.read_cache_file(Path(trajectory_file))
        else:
            if not self.cache_file:
                self.cache_file = CacheManager.read_cache_file(Path(trajectory_file))

        # Validate step index
        if start_from_step_index < 0 or start_from_step_index >= len(
            self.cache_file.trajectory
        ):
            error_msg = (
                f"Invalid start_from_step_index: {start_from_step_index}. "
                f"Trajectory has {len(self.cache_file.trajectory)} steps "
                f"(valid indices: 0-{len(self.cache_file.trajectory) - 1})."
            )
            raise ValueError(error_msg)

        # Validate parameters
        is_valid, missing = CacheParameterHandler.validate_parameters(
            self.cache_file.trajectory, parameter_values
        )
        if not is_valid:
            error_msg = (
                f"Missing required parameter values: {', '.join(missing)}. "
                f"The trajectory contains the following parameters: "
                f"{', '.join(self.cache_file.cache_parameters.keys())}. "
                "Please provide values for all parameters."
            )
            raise ValueError(error_msg)

        # Warn if cache is invalid
        if not self.cache_file.metadata.is_valid:
            logger.warning(
                "Using invalid cache from %s. Reason: %s. "
                "This cache may not work correctly.",
                Path(trajectory_file).name,
                self.cache_file.metadata.invalidation_reason,
            )

        # Set up execution state
        self._trajectory = self.cache_file.trajectory
        self._toolbox = toolbox
        self._parameter_values = parameter_values
        self._delay_time = context.get("delay_time", 0.5)
        self._current_step_index = start_from_step_index
        self._message_history = []
        self._executing_from_cache = True

        # Enable visual validation if configured in cache metadata
        # Can be overridden by execution settings
        visual_validation_config = self.cache_file.metadata.visual_validation

        if self._skip_visual_validation:
            self._visual_validation_enabled = False
            logger.info("Visual validation disabled by execution settings")
        elif visual_validation_config and visual_validation_config.get("enabled"):
            self._visual_validation_enabled = True
            self._visual_validation_method = visual_validation_config.get(
                "method", "phash"
            )
            self._visual_validation_region_size = visual_validation_config.get(
                "region_size", 100
            )
            self._visual_validation_threshold = visual_validation_config.get(
                "threshold", 10
            )
            logger.info(
                "Visual validation enabled (method=%s, threshold=%d)",
                self._visual_validation_method,
                self._visual_validation_threshold,
            )
        else:
            self._visual_validation_enabled = False
            logger.debug("Visual validation disabled or not configured")

        logger.info(
            "✓ Cache execution activated: %s (%d steps, starting from step %d)",
            Path(trajectory_file).name,
            len(self.cache_file.trajectory),
            start_from_step_index,
        )

    def reset_state(self) -> None:
        """Reset cache execution state.

        Clears all cache-related state variables.
        """
        self._executing_from_cache = False
        self._cache_verification_pending = False
        self._cache_file = None
        self._cache_file_path = None
        self._trajectory = []
        self._toolbox = None
        self._parameter_values = {}
        self._current_step_index = 0
        self._message_history = []

    def get_cache_info(self) -> tuple["CacheFile | None", str | None]:
        """Get current cache file and path.

        Returns:
            Tuple of (cache_file, cache_file_path)
        """
        return self._cache_file, self._cache_file_path

    def is_verification_pending(self) -> bool:
        """Check if cache verification is pending.

        Returns:
            True if verification is pending
        """
        return self._cache_verification_pending

    def _update_metadata_on_failure(
        self, cache_manager: CacheManager, step_index: int, error_message: str
    ) -> None:
        """Update cache metadata on failure.

        Args:
            step_index: The step where failure occurred
            error_message: Error message describing the failure
        """

        if not self._cache_file or not self._cache_file_path:
            return

        cache_manager.update_metadata_on_failure(
            cache_file=self._cache_file,
            cache_file_path=self._cache_file_path,
            step_index=step_index,
            error_message=error_message,
        )

    def _get_next_step(
        self, conversation_messages: list[MessageParam] | None = None
    ) -> ExecutionResult:
        """Get the next step message from the trajectory.

        This method does NOT execute tools - it only prepares the message.
        Tool execution is handled by the Conversation class.

        Args:
            conversation_messages: Optional conversation messages for visual validation

        Returns:
            ExecutionResult with status and the prepared message

        The method will:
        1. Check if there are more steps to execute
        2. Check if the step should be skipped
        3. Check if the step is non-cacheable (needs agent)
        4. Perform visual validation if enabled
        5. Substitute parameters
        6. Create assistant message with tool use block
        7. Return result (Conversation will execute the tool)
        """
        # Check if we've completed all steps
        if self._current_step_index >= len(self._trajectory):
            return ExecutionResult(
                status="COMPLETED",
                step_index=self._current_step_index - 1,
                message_history=self._message_history,
            )

        step = self._trajectory[self._current_step_index]
        step_index = self._current_step_index

        # Check if step should be skipped
        if self._should_skip_step(step):
            logger.debug("Skipping step %d: %s", step_index, step.name)
            self._current_step_index += 1
            # Recursively get next step
            return self._get_next_step(conversation_messages=conversation_messages)

        # Check if step needs agent intervention (non-cacheable)
        if self._should_pause_for_agent(step):
            logger.info(
                "Pausing at step %d: %s (non-cacheable tool)",
                step_index,
                step.name,
            )

            return ExecutionResult(
                status="NEEDS_AGENT",
                step_index=step_index,
                message_history=self._message_history.copy(),
                tool_result=step,  # Pass the tool use block for reference
            )

        # Visual validation - check current UI state matches recorded state
        if self._visual_validation_enabled:
            # Find current screenshot from conversation messages
            current_screenshot = None
            if conversation_messages:
                current_screenshot = find_recent_screenshot(conversation_messages)

            is_valid, error_msg = self._validate_step_visually(
                step, current_screenshot=current_screenshot
            )
            if not is_valid:
                logger.warning(
                    "Visual validation failed at step %d: %s",
                    step_index,
                    error_msg,
                )
                return ExecutionResult(
                    status="FAILED",
                    step_index=step_index,
                    error_message=error_msg,
                    message_history=self._message_history.copy(),
                )

        # Substitute parameters
        substituted_step = CacheParameterHandler.substitute_parameters(
            step, self._parameter_values
        )

        # Create assistant message (tool use) - DON'T execute yet
        try:
            logger.debug("Preparing step %d: %s", step_index, step.name)

            # Create assistant message (tool use)
            assistant_message = MessageParam(
                role="assistant",
                content=[substituted_step],
            )

            return ExecutionResult(
                status="SUCCESS",
                step_index=step_index,
                tool_result=None,
                message_history=[assistant_message],
            )

        except Exception as e:
            logger.exception("Error preparing step %d: %s", step_index, step.name)
            return ExecutionResult(
                status="FAILED",
                step_index=step_index,
                error_message=str(e),
                message_history=self._message_history.copy(),
            )

    def _should_pause_for_agent(self, step: ToolUseBlockParam) -> bool:
        """Check if execution should pause for agent intervention.

        Args:
            step: The tool use block to check

        Returns:
            True if agent should execute this step, False if it can be cached

        Currently checks if the tool is marked as non-cacheable.
        """
        # Get the tool from toolbox
        if not self._toolbox:
            return False

        tool = self._toolbox.get_tools().get(step.name)  # noqa: SLF001

        if tool is None:
            # Tool not found in regular tools, might be MCP tool
            # For now, assume MCP tools are cacheable
            return False

        # Check if tool is marked as non-cacheable
        return not tool.is_cacheable

    def _should_skip_step(self, step: ToolUseBlockParam) -> bool:
        """Check if a step should be skipped during execution.

        Args:
            _step: The tool use block to check

        Returns:
            True if step should be skipped, False otherwise
        """
        tools_to_skip: list[str] = ["retrieve_available_trajectories_tool"]
        if step.name in tools_to_skip:
            return True
        return False

    def _validate_step_visually(
        self, step: ToolUseBlockParam, current_screenshot: Image.Image | None = None
    ) -> tuple[bool, str | None]:
        """Validate cached step using visual hash comparison.

        Compares the current UI state (screenshot) with the stored visual hash
        from when the trajectory was recorded. If the Hamming distance exceeds
        the threshold, validation fails.

        Args:
            step: The trajectory step to validate (contains visual_representation)
            current_screenshot: Optional current screenshot (if not provided, will
                               extract from message history)

        Returns:
            Tuple of (is_valid: bool, error_message: str | None)
            - (True, None) if validation passes or is disabled
            - (False, error_msg) if validation fails
        """
        # Check if visual validation is enabled
        if not self._visual_validation_enabled:
            return True, None

        # Check if step has a visual hash (only click and text_entry actions have them)
        if not step.visual_representation:
            # No hash stored, skip validation
            return True, None

        # Extract current screenshot if not provided
        if current_screenshot is None:
            current_screenshot = find_recent_screenshot(self._message_history)
            if not current_screenshot:
                # No screenshot available, cannot validate
                logger.warning("No screenshot found for visual validation, skipping")
                return True, None

        # Extract region and compute current hash
        try:
            # Extract the region around the action coordinate
            region = extract_region(
                current_screenshot,
                step.input,  # type: ignore[arg-type]
                region_size=self._visual_validation_region_size,
            )

            # Compute hash using configured method
            current_hash = self._compute_visual_hash(region)

            # Compare hashes using Hamming distance
            distance = compute_hamming_distance(step.visual_representation, current_hash)

            # Check if distance exceeds threshold
            if distance > self._visual_validation_threshold:
                error_msg = (
                    f"Visual validation failed: UI has changed significantly. "
                    f"Hamming distance: {distance} > threshold: {self._visual_validation_threshold}. "
                    f"The cached action may not work correctly in the current UI state."
                )
                return False, error_msg

            # Validation passed
            logger.debug(
                "Visual validation passed (distance=%d, threshold=%d)",
                distance,
                self._visual_validation_threshold,
            )
            return True, None

        except Exception as e:
            # If validation fails with exception, log and skip validation
            logger.exception("Failed to perform visual validation")
            # Return True to continue execution (don't block on validation errors)
            return True, f"Visual validation skipped due to error: {e}"

    def _compute_visual_hash(self, image: Image.Image) -> str:
        """Compute visual hash using configured method.

        Args:
            image: PIL Image to hash

        Returns:
            String representation of the hash
        """
        if self._visual_validation_method == "phash":
            return compute_phash(image, hash_size=8)
        elif self._visual_validation_method == "ahash":
            return compute_ahash(image, hash_size=8)
        else:
            msg = f"Unsupported visual validation method: {self._visual_validation_method}"
            raise ValueError(msg)
