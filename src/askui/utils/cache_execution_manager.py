"""Manager for cache execution flow and state."""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from askui.models.shared.agent_message_param import MessageParam, TextBlockParam
from askui.models.shared.agent_on_message_cb import OnMessageCb
from askui.models.shared.truncation_strategies import TruncationStrategy
from askui.reporting import Reporter
from askui.utils.trajectory_executor import ExecutionResult

if TYPE_CHECKING:
    from askui.models.shared.settings import CacheFile
    from askui.utils.trajectory_executor import TrajectoryExecutor

logger = logging.getLogger(__name__)


class CacheExecutionManager:
    """Manages cache execution flow, state, and metadata updates.

    This class encapsulates all cache-related logic, keeping the Agent class
    focused on conversation orchestration.
    """

    def __init__(self, reporter: Reporter) -> None:
        """Initialize cache execution manager.

        Args:
            reporter: Reporter for logging messages and actions
        """
        self._reporter = reporter
        # Cache execution state
        self._executing_from_cache: bool = False
        self._cache_executor: "TrajectoryExecutor | None" = None
        self._cache_file_path: str | None = None
        self._cache_file: "CacheFile | None" = None
        # Track cache verification after execution completes
        self._cache_verification_pending: bool = False

    def reset_state(self) -> None:
        """Reset cache execution state."""
        self._executing_from_cache = False
        self._cache_executor = None
        self._cache_file_path = None
        self._cache_file = None
        self._cache_verification_pending = False
        logger.debug("Reset cache execution state")

    def activate_execution(
        self,
        executor: "TrajectoryExecutor",
        cache_file: "CacheFile",
        cache_file_path: str,
    ) -> None:
        """Activate cache execution mode.

        Args:
            executor: The trajectory executor to use
            cache_file: The cache file being executed
            cache_file_path: Path to the cache file
        """
        self._cache_executor = executor
        self._cache_file = cache_file
        self._cache_file_path = cache_file_path
        self._executing_from_cache = True

    def get_cache_info(self) -> tuple["CacheFile | None", str | None]:
        """Get current cache file and path.

        Returns:
            Tuple of (cache_file, cache_file_path)
        """
        return (self._cache_file, self._cache_file_path)

    def is_cache_verification_pending(self) -> bool:
        """Check if cache verification is pending.

        Returns:
            True if verification is pending
        """
        return self._cache_verification_pending

    def clear_cache_state(self) -> None:
        """Clear cache execution state after verification."""
        self._cache_verification_pending = False
        self._cache_file = None
        self._cache_file_path = None

    def handle_execution_step(
        self,
        on_message: OnMessageCb,
        truncation_strategy: TruncationStrategy,
        agent_class_name: str,
    ) -> bool:
        """Handle cache execution step.

        Args:
            on_message: Callback for messages
            truncation_strategy: Message truncation strategy
            agent_class_name: Name of agent class for reporting

        Returns:
            True if cache step was handled and caller should recurse,
            False if should continue with normal flow
        """
        if not (self._executing_from_cache and self._cache_executor):
            return False

        logger.debug("Executing next step from cache")
        result: ExecutionResult = self._cache_executor.execute_next_step()

        if result.status == "SUCCESS":
            return self._handle_cache_success(
                result,
                on_message,
                truncation_strategy,
                agent_class_name,
            )
        if result.status == "NEEDS_AGENT":
            return self._handle_cache_needs_agent(
                result,
                on_message,
                truncation_strategy,
                agent_class_name,
            )
        if result.status == "COMPLETED":
            return self._handle_cache_completed(truncation_strategy)
        # result.status == "FAILED"
        return self._handle_cache_failed(result)

    def _handle_cache_success(
        self,
        result: ExecutionResult,
        on_message: OnMessageCb,
        truncation_strategy: TruncationStrategy,
        agent_class_name: str,
    ) -> bool:
        """Handle successful cache step execution.

        Returns:
            True if messages were added and caller should recurse,
            False otherwise
        """
        if len(result.message_history) < 2:
            return False

        assistant_msg = result.message_history[-2]
        user_msg = result.message_history[-1]

        # Add assistant message (tool use)
        message_by_assistant = self._call_on_message(
            on_message, assistant_msg, truncation_strategy.messages
        )
        if message_by_assistant is None:
            return True

        truncation_strategy.append_message(message_by_assistant)
        self._reporter.add_message(
            agent_class_name, message_by_assistant.model_dump(mode="json")
        )

        # Add user message (tool result)
        user_msg_processed = self._call_on_message(
            on_message, user_msg, truncation_strategy.messages
        )
        if user_msg_processed is None:
            return True

        truncation_strategy.append_message(user_msg_processed)

        # Return True to indicate caller should recurse
        return True

    def _handle_cache_needs_agent(
        self,
        result: ExecutionResult,
        on_message: OnMessageCb,
        truncation_strategy: TruncationStrategy,
        agent_class_name: str,
    ) -> bool:
        """Handle cache execution pausing for non-cacheable tool.

        Injects a user message explaining that cache execution paused and
        what the agent needs to execute next.

        Returns:
            False to indicate normal agent flow should continue
        """
        logger.info(
            "Paused cache execution at step %d "
            "(non-cacheable tool - agent will handle this step)",
            result.step_index,
        )
        self._executing_from_cache = False

        # Get the tool that needs to be executed
        tool_to_execute = result.tool_result  # This is the ToolUseBlockParam

        # Create a user message explaining what needs to be done
        if tool_to_execute:
            instruction_message = MessageParam(
                role="user",
                content=[
                    TextBlockParam(
                        type="text",
                        text=(
                            f"Cache execution paused at step {result.step_index}. "
                            f"The previous steps were executed successfully from cache. "
                            f"The next step requires the '{tool_to_execute.name}' tool, "
                            f"which cannot be executed from cache. "
                            f"Please execute this tool with the necessary parameters."
                        ),
                    )
                ],
            )

            # Add the instruction message to truncation strategy
            instruction_msg = self._call_on_message(
                on_message, instruction_message, truncation_strategy.messages
            )
            if instruction_msg:
                truncation_strategy.append_message(instruction_msg)

        return False  # Fall through to normal agent API call

    def _handle_cache_completed(self, truncation_strategy: TruncationStrategy) -> bool:
        """Handle cache execution completion."""
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
                        "The cached trajectory execution has completed. "
                        "Please verify if the execution correctly achieved "
                        "the target system state. "
                        "Use the verify_cache_execution tool to report "
                        "your verification result."
                    ),
                )
            ],
        )
        truncation_strategy.append_message(verification_request)
        logger.debug("Injected cache verification request message")
        return False  # Fall through to let agent verify execution

    def _handle_cache_failed(self, result: ExecutionResult) -> bool:
        """Handle cache execution failure."""
        logger.error(
            "✗ Cache execution failed at step %d: %s",
            result.step_index,
            result.error_message,
        )
        self._executing_from_cache = False

        # Update cache metadata
        if self._cache_file and self._cache_file_path:
            self.update_metadata_on_failure(
                step_index=result.step_index,
                error_message=result.error_message or "Unknown error",
            )

        return False  # Fall through to let agent continue

    def _call_on_message(
        self,
        on_message: OnMessageCb | None,
        message: MessageParam,
        messages: list[MessageParam],
    ) -> MessageParam | None:
        """Call on_message callback if provided."""
        if on_message is None:
            return message
        from askui.models.shared.agent_on_message_cb import OnMessageCbParam

        return on_message(OnMessageCbParam(message=message, messages=messages))

    def update_metadata_on_completion(self, success: bool) -> None:
        """Update cache metadata after execution completion.

        Args:
            success: Whether the execution was successful
        """
        if not self._cache_file or not self._cache_file_path:
            return

        try:
            from askui.utils.cache_manager import CacheManager

            cache_manager = CacheManager()
            cache_manager.record_execution_attempt(self._cache_file, success=success)

            # Write updated metadata back to disk
            cache_path = Path(self._cache_file_path)
            with cache_path.open("w") as f:
                json.dump(
                    self._cache_file.model_dump(mode="json"),
                    f,
                    indent=2,
                    default=str,
                )
            logger.debug("Updated cache metadata: %s", cache_path.name)
        except Exception:
            logger.exception("Failed to update cache metadata")

    def update_metadata_on_failure(self, step_index: int, error_message: str) -> None:
        """Update cache metadata after execution failure.

        Args:
            step_index: The step index where failure occurred
            error_message: The error message
        """
        if not self._cache_file or not self._cache_file_path:
            return

        try:
            from askui.utils.cache_manager import CacheManager

            cache_manager = CacheManager()
            cache_manager.record_execution_attempt(self._cache_file, success=False)
            cache_manager.record_step_failure(
                self._cache_file,
                step_index=step_index,
                error_message=error_message,
            )

            # Check if cache should be invalidated
            should_inv, reason = cache_manager.should_invalidate(
                self._cache_file, step_index=step_index
            )
            if should_inv and reason:
                logger.warning("Cache invalidated: %s", reason)
                cache_manager.invalidate_cache(self._cache_file, reason=reason)

            # Write updated metadata back to disk
            cache_path = Path(self._cache_file_path)
            with cache_path.open("w") as f:
                json.dump(
                    self._cache_file.model_dump(mode="json"),
                    f,
                    indent=2,
                    default=str,
                )
            logger.debug("Updated cache metadata after failure: %s", cache_path.name)
        except Exception:
            logger.exception("Failed to update cache metadata")
