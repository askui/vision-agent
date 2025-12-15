"""Trajectory executor for step-by-step cache execution.

This module provides the TrajectoryExecutor class that enables controlled
execution of cached trajectories with support for pausing at non-cacheable
steps, error handling, and agent intervention.
"""

import logging
import time
from typing import Any, Optional

from pydantic import BaseModel, Field
from typing_extensions import Literal

from askui.models.shared.agent_message_param import (
    ImageBlockParam,
    MessageParam,
    TextBlockParam,
    ToolResultBlockParam,
    ToolUseBlockParam,
)
from askui.models.shared.tools import ToolCollection
from askui.utils.placeholder_handler import PlaceholderHandler

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


class TrajectoryExecutor:
    """Executes cached trajectories step-by-step with control flow.

    Supports pausing at non-cacheable steps, placeholder substitution,
    and collecting execution results for the agent to review.
    """

    def __init__(
        self,
        trajectory: list[ToolUseBlockParam],
        toolbox: ToolCollection,
        placeholder_values: dict[str, str] | None = None,
        delay_time: float = 0.5,
        visual_validation_enabled: bool = False,
    ):
        """Initialize the trajectory executor.

        Args:
            trajectory: List of tool use blocks to execute
            toolbox: ToolCollection for executing tools
            placeholder_values: Dict of placeholder names to values
            delay_time: Seconds to wait between step executions
            visual_validation_enabled: Enable visual validation (future feature)
        """
        self.trajectory = trajectory
        self.toolbox = toolbox
        self.placeholder_values = placeholder_values or {}
        self.delay_time = delay_time
        self.visual_validation_enabled = visual_validation_enabled
        self.current_step_index = 0
        self.message_history: list[MessageParam] = []

    def execute_next_step(self) -> ExecutionResult:
        """Execute the next step in the trajectory.

        Returns:
            ExecutionResult with status and details of the execution

        The method will:
        1. Check if there are more steps to execute
        2. Check if the step should be skipped (screenshots, retrieval tools)
        3. Check if the step is non-cacheable (needs agent)
        4. Substitute placeholders
        5. Execute the tool and build messages with proper data types
        6. Return result with updated message history

        Note: Tool results are preserved with their proper data types (e.g.,
        ImageBlockParam for screenshots) and added to message history. The
        agent's truncation strategy will manage message history size.
        """
        # Check if we've completed all steps
        if self.current_step_index >= len(self.trajectory):
            return ExecutionResult(
                status="COMPLETED",
                step_index=self.current_step_index - 1,
                message_history=self.message_history,
            )

        step = self.trajectory[self.current_step_index]
        step_index = self.current_step_index

        # Check if step should be skipped
        if self._should_skip_step(step):
            logger.debug(f"Skipping step {step_index}: {step.name}")
            self.current_step_index += 1
            # Recursively execute next step
            return self.execute_next_step()

        # Check if step needs agent intervention (non-cacheable)
        if self.should_pause_for_agent(step):
            logger.info(
                f"Pausing at step {step_index}: {step.name} (non-cacheable tool)"
            )
            # Return result with current tool step info for the agent to handle
            # Note: We don't add any messages here - the cache manager will
            # inject a user message explaining what needs to be done
            return ExecutionResult(
                status="NEEDS_AGENT",
                step_index=step_index,
                message_history=self.message_history.copy(),
                tool_result=step,  # Pass the tool use block for reference
            )

        # Visual validation (future feature - currently always passes)
        # Extension point for aHash-based UI validation
        if self.visual_validation_enabled:
            is_valid, error_msg = self.validate_step_visually(step)
            if not is_valid:
                logger.warning(
                    f"Visual validation failed at step {step_index}: {error_msg}"
                )
                return ExecutionResult(
                    status="FAILED",
                    step_index=step_index,
                    error_message=error_msg,
                    message_history=self.message_history.copy(),
                )

        # Substitute placeholders
        substituted_step = PlaceholderHandler.substitute_placeholders(
            step, self.placeholder_values
        )

        # Execute the tool
        try:
            logger.debug(f"Executing step {step_index}: {step.name}")

            # Add assistant message (tool use) to history
            assistant_message = MessageParam(
                role="assistant",
                content=[substituted_step],
            )
            self.message_history.append(assistant_message)

            # Execute the tool
            tool_results = self.toolbox.run([substituted_step])

            # toolbox.run() returns a list of content blocks (ToolResultBlockParam, etc.)
            # We use these directly without converting to strings - this preserves
            # proper data types like ImageBlockParam

            # Add user message (tool result) to history
            user_message = MessageParam(
                role="user",
                content=tool_results if tool_results else [],
            )
            self.message_history.append(user_message)

            # Move to next step
            self.current_step_index += 1

            # Add delay between actions
            if self.current_step_index < len(self.trajectory):
                time.sleep(self.delay_time)

            return ExecutionResult(
                status="SUCCESS",
                step_index=step_index,
                tool_result=tool_results[0] if tool_results else None,
                message_history=self.message_history.copy(),
            )

        except Exception as e:
            logger.error(
                f"Error executing step {step_index}: {step.name}",
                exc_info=True,
            )
            return ExecutionResult(
                status="FAILED",
                step_index=step_index,
                error_message=str(e),
                message_history=self.message_history.copy(),
            )

    def execute_all(self) -> list[ExecutionResult]:
        """Execute all steps in the trajectory until completion or pause.

        Returns:
            List of ExecutionResult for all executed steps

        Execution stops when:
        - All steps are completed
        - A step fails
        - A non-cacheable step is encountered
        """
        results: list[ExecutionResult] = []

        while True:
            result = self.execute_next_step()
            results.append(result)

            # Stop if we've completed, failed, or need agent
            if result.status in ["COMPLETED", "FAILED", "NEEDS_AGENT"]:
                break

        return results

    def should_pause_for_agent(self, step: ToolUseBlockParam) -> bool:
        """Check if execution should pause for agent intervention.

        Args:
            step: The tool use block to check

        Returns:
            True if agent should execute this step, False if it can be cached

        Currently checks if the tool is marked as non-cacheable.
        """
        # Get the tool from toolbox
        tool = self.toolbox._tool_map.get(step.name)

        if tool is None:
            # Tool not found in regular tools, might be MCP tool
            # For now, assume MCP tools are cacheable
            return False

        # Check if tool is marked as non-cacheable
        return not tool.is_cacheable

    def get_current_step_index(self) -> int:
        """Get the index of the current step.

        Returns:
            Current step index
        """
        return self.current_step_index

    def get_remaining_trajectory(self) -> list[ToolUseBlockParam]:
        """Get the remaining steps in the trajectory.

        Returns:
            List of tool use blocks that haven't been executed yet
        """
        return self.trajectory[self.current_step_index :]

    def skip_current_step(self) -> None:
        """Skip the current step and move to the next one.

        Useful when the agent manually executes a non-cacheable step.
        """
        if self.current_step_index < len(self.trajectory):
            self.current_step_index += 1

    def _should_skip_step(self, step: ToolUseBlockParam) -> bool:
        """Check if a step should be skipped during execution.

        Args:
            step: The tool use block to check

        Returns:
            True if step should be skipped, False otherwise

        Note: As of v0.1, no steps are skipped. All tools in the trajectory
        are executed, including screenshots and trajectory retrieval tools.
        """
        return False

    def validate_step_visually(
        self, step: ToolUseBlockParam, current_screenshot: Any = None
    ) -> tuple[bool, str | None]:
        """Hook for visual validation of cached steps using aHash comparison.

        This is an extension point for future visual validation implementation.
        Currently returns (True, None) - no validation performed.

        Future implementation will:
        1. Check if step has visual_validation_required=True
        2. Compute aHash of current screen region
        3. Compare with stored visual_hash
        4. Return validation result based on Hamming distance threshold

        Args:
            step: The trajectory step to validate
            current_screenshot: Optional current screen capture (future use)

        Returns:
            Tuple of (is_valid: bool, error_message: str | None)
            - (True, None) if validation passes or is disabled
            - (False, error_msg) if validation fails

        Example future implementation:
            if not self.visual_validation_enabled:
                return True, None

            if not step.visual_validation_required:
                return True, None

            if step.visual_hash is None:
                return True, None  # No hash stored, skip validation

            # Capture current screen region
            current_hash = compute_ahash(current_screenshot)

            # Compare hashes
            distance = hamming_distance(step.visual_hash, current_hash)
            threshold = 10  # Configurable

            if distance > threshold:
                return False, (
                    f"Visual validation failed: UI changed significantly "
                    f"(distance: {distance} > threshold: {threshold})"
                )

            return True, None
        """
        # Future: Implement aHash comparison
        # For now, always return True (no validation)
        return True, None
