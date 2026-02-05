"""Trajectory executor for step-by-step cache execution.

This module provides the TrajectoryExecutor class that enables controlled
execution of cached trajectories with support for pausing at non-cacheable
steps, error handling, and agent intervention.
"""

import logging
import time
from typing import Any, Optional, Union

from PIL import Image
from pydantic import BaseModel, Field
from typing_extensions import Literal

from askui.models.shared.agent_message_param import (
    MessageParam,
    ToolUseBlockParam,
)
from askui.models.shared.tools import ToolCollection
from askui.tools.android.tools import AndroidScreenshotTool
from askui.tools.computer import ComputerScreenshotTool
from askui.utils.cache_parameter_handler import CacheParameterHandler
from askui.utils.visual_validation import (
    extract_region,
    get_validation_coordinate,
    validate_visual_hash,
)

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

    Supports pausing at non-cacheable steps, cache_parameter substitution,
    and collecting execution results for the agent to review.
    """

    def __init__(
        self,
        trajectory: list[ToolUseBlockParam],
        toolbox: ToolCollection,
        parameter_values: dict[str, str] | None = None,
        delay_time: float = 0.5,
        visual_validation_enabled: bool = False,
        visual_validation_threshold: int = 10,
        visual_hash_method: str = "phash",
        visual_validation_region_size: int = 100,
    ):
        """Initialize the trajectory executor.

        Args:
            trajectory: List of tool use blocks to execute
            toolbox: ToolCollection for executing tools
            parameter_values: Dict of parameter names to values
            delay_time: Seconds to wait between step executions
            visual_validation_enabled: Enable visual validation
            visual_validation_threshold: Hamming distance threshold (0-64)
            visual_hash_method: Hash method to use ('phash' or 'ahash')
            visual_validation_region_size: Size of square region to extract (in pixels)
        """
        self.trajectory = trajectory
        self.toolbox = toolbox
        self.parameter_values = parameter_values or {}
        self.delay_time = delay_time
        self.visual_validation_enabled = visual_validation_enabled
        self.visual_validation_threshold = visual_validation_threshold
        self.visual_hash_method = visual_hash_method
        self.visual_validation_region_size = visual_validation_region_size
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
        4. Substitute parameters
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
            logger.debug("Skipping step %d: %s", step_index, step.name)
            self.current_step_index += 1
            # Recursively execute next step
            return self.execute_next_step()

        # Check if step needs agent intervention (non-cacheable)
        if self.should_pause_for_agent(step):
            logger.info(
                "Pausing at step %d: %s (non-cacheable tool)",
                step_index,
                step.name,
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

        # Visual validation: verify UI state matches cached expectations
        # Compares stored visual hash with current screen region
        if self.visual_validation_enabled:
            is_valid, error_msg = self.validate_step_visually(step)
            if not is_valid:
                logger.warning(
                    "Visual validation failed at step %d: %s. "
                    "Handing execution back to agent.",
                    step_index,
                    error_msg,
                )
                return ExecutionResult(
                    status="FAILED",
                    step_index=step_index,
                    error_message=error_msg,
                    message_history=self.message_history.copy(),
                )

        # Substitute parameters
        substituted_step = CacheParameterHandler.substitute_parameters(
            step, self.parameter_values
        )

        # Execute the tool
        try:
            logger.debug("Executing step %d: %s", step_index, step.name)

            # Add assistant message (tool use) to history
            assistant_message = MessageParam(
                role="assistant",
                content=[substituted_step],
            )
            self.message_history.append(assistant_message)

            # Execute the tool
            tool_results = self.toolbox.run([substituted_step])

            # toolbox.run() returns a list of content blocks
            # (ToolResultBlockParam, etc.) We use these directly without
            # converting to strings - this preserves proper data types like
            # ImageBlockParam

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
            logger.exception("Error executing step %d: %s", step_index, step.name)
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
        tool = self.toolbox.tool_map.get(step.name)  # noqa: SLF001

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

    def _should_skip_step(self, _step: ToolUseBlockParam) -> bool:
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
        """Validate cached steps using visual hash comparison.

        Compares the current UI state against the stored visual hash to detect
        if the UI has changed significantly since the trajectory was recorded.

        Args:
            step: The trajectory step to validate
            current_screenshot: Optional current screen capture (will capture if None)

        Returns:
            Tuple of (is_valid: bool, error_message: str | None)
            - (True, None) if validation passes or is disabled
            - (False, error_msg) if validation fails
        """
        # Skip validation if disabled
        if not self.visual_validation_enabled:
            return True, None

        # Skip if no visual representation stored (implies no validation needed)
        if step.visual_representation is None:
            return True, None

        # Get coordinate for validation
        if not isinstance(step.input, dict):
            return True, None

        coordinate = get_validation_coordinate(step.input)
        if coordinate is None:
            logger.debug(
                "Could not extract coordinate from step %d for visual validation",
                self.current_step_index,
            )
            return True, None

        # Capture current screenshot if not provided
        if current_screenshot is None:
            screenshot_tool = self._get_screenshot_tool(step.name)
            if screenshot_tool is None:
                logger.warning("Could not find correct screenshot tool")
                return True, None

            current_screenshot = self._capture_screenshot(screenshot_tool)
            if current_screenshot is None:
                logger.warning(
                    "Could not capture screenshot for visual validation at step %d",
                    self.current_step_index,
                )
                # Unable to validate, but don't fail execution
                return True, None

        # Extract region around coordinate
        try:
            region = extract_region(
                current_screenshot, coordinate, size=self.visual_validation_region_size
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Error extracting region for visual validation at step %d: %s",
                self.current_step_index,
                e,
            )
            return True, None

        # Validate hash
        is_valid, error_msg, _distance = validate_visual_hash(
            stored_hash=step.visual_representation,
            current_image=region,
            threshold=self.visual_validation_threshold,
            hash_method=self.visual_hash_method,
        )

        # Only log if validation fails
        if not is_valid:
            logger.warning(
                "Visual validation failed at step %d: %s",
                self.current_step_index,
                error_msg,
            )

        return is_valid, error_msg

    def _get_screenshot_tool(
        self, step_name: str
    ) -> Union[ComputerScreenshotTool, AndroidScreenshotTool, None]:
        """
        Get the available screenshot tool for the correct device.

        Returns:
            Tool or None if no screenshot tool is found for the device
        """
        # Get the tools from toolbox
        tools = self.toolbox.get_tools()

        # Try to find a screenshot tool (computer or Android)
        screenshot_tool = None
        if "computer" in step_name:
            tool_name = "computer_screenshot"
        elif "android" in step_name:
            tool_name = "android_screenshot_tool"
        else:
            warning_msg = f"Cannot infer screenshot tool for step {step_name}"
            logger.warning(warning_msg)
            return None

        screenshot_tool = tools.get(tool_name)
        if screenshot_tool is not None:
            assert isinstance(
                screenshot_tool, (ComputerScreenshotTool, AndroidScreenshotTool)
            )
            logger.debug("Found screenshot tool: %s", tool_name)
            return screenshot_tool

        if screenshot_tool is None:
            logger.warning("No screenshot tool found in toolbox")
            return None

        return None

    def _capture_screenshot(
        self, screenshot_tool: Union[ComputerScreenshotTool, AndroidScreenshotTool]
    ) -> Image.Image | None:
        """Capture current screenshot using the available screenshot tool.

        Supports both computer and Android screenshot tools.

        Returns:
            PIL Image or None if screenshot capture fails
        """

        # Call the screenshot action
        try:
            # Try to call _screenshot() method directly if available
            if hasattr(screenshot_tool, "agent_os"):
                result = screenshot_tool.agent_os.screenshot()
            else:
                # Fallback to calling via __call__
                _, result = screenshot_tool()

            # Handle different return types
            # Computer tool returns Image.Image directly
            if isinstance(result, Image.Image):
                return result
            # Android tool returns tuple[str, Image.Image]
            if isinstance(result, tuple) and len(result) >= 2:
                if isinstance(result[1], Image.Image):
                    return result[1]

            logger.warning(
                "Screenshot action did not return an Image: %s", type(result)
            )
            return None  # noqa: TRY300
        except Exception:
            logger.exception("Error capturing screenshot")
            return None
