import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import validate_call
from typing_extensions import override

from ..models.shared.settings import CachedExecutionToolSettings
from ..models.shared.tools import Tool, ToolCollection
from ..utils.caching.cache_execution_manager import CacheExecutionManager
from ..utils.caching.cache_manager import CacheManager
from ..utils.caching.cache_parameter_handler import CacheParameterHandler
from ..utils.caching.cache_writer import CacheWriter

if TYPE_CHECKING:
    from ..models.shared.agent_message_param import ToolUseBlockParam
    from ..models.shared.settings import CacheFile
    from ..utils.caching.trajectory_executor import TrajectoryExecutor

logger = logging.getLogger()


class RetrieveCachedTestExecutions(Tool):
    """
    List all available trajectory files that can be used for fast-forward execution
    """

    def __init__(self, cache_dir: str, trajectories_format: str = ".json") -> None:
        super().__init__(
            name="retrieve_available_trajectories_tool",
            description=(
                "Use this tool to list all available pre-recorded trajectory "
                "files in the trajectories directory. These trajectories "
                "represent successful UI interaction sequences that can be "
                "replayed using the execute_trajectory_tool. Call this tool "
                "first to see which trajectories are available before "
                "executing one. The tool returns a list of file paths to "
                "available trajectory files.\n\n"
                "By default, only valid (non-invalidated) caches are returned. "
                "Set include_invalid=True to see all caches including those "
                "marked as invalid due to repeated failures."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "include_invalid": {
                        "type": "boolean",
                        "description": (
                            "Whether to include invalid/invalidated caches in "
                            "the results. Default is False (only show valid "
                            "caches)."
                        ),
                        "default": False,
                    },
                },
                "required": [],
            },
        )
        self._cache_dir = Path(cache_dir)
        self._trajectories_format = trajectories_format

    @override
    @validate_call
    def __call__(self, include_invalid: bool = False) -> list[str]:  # type: ignore
        logger.info(
            "Retrieving cached trajectories from %s (include_invalid=%s)",
            self._cache_dir,
            include_invalid,
        )

        if not Path.is_dir(self._cache_dir):
            error_msg = f"Trajectories directory not found: {self._cache_dir}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        all_files = [
            f
            for f in self._cache_dir.iterdir()
            if str(f).endswith(self._trajectories_format)
        ]
        logger.debug("Found %d total cache files", len(all_files))

        if not include_invalid:
            # Filter out invalid caches
            valid_files = []
            invalid_count = 0
            unreadable_count = 0
            for f in all_files:
                try:
                    cache_file = CacheWriter.read_cache_file(f)
                    if cache_file.metadata.is_valid:
                        valid_files.append(str(f))
                    else:
                        invalid_count += 1
                        logger.debug(
                            "Excluding invalid cache: %s (reason: %s)",
                            f.name,
                            cache_file.metadata.invalidation_reason,
                        )
                except Exception:  # noqa: PERF203
                    unreadable_count += 1
                    logger.exception("Failed to read cache file %s", f.name)
                    # If we can't read it, exclude it
                    continue
            available = valid_files
            logger.info(
                "Found %d valid cache(s), excluded %d invalid, %d unreadable",
                len(valid_files),
                invalid_count,
                unreadable_count,
            )
        else:
            available = [str(f) for f in all_files]
            logger.info("Retrieved %d cache file(s) (all included)", len(available))

        if not available:
            if include_invalid:
                warning_msg = f"Warning: No trajectory files found in {self._cache_dir}"
            else:
                warning_msg = (
                    f"Warning: No valid trajectory files found in "
                    f"{self._cache_dir}. "
                    "Try include_invalid=True to see all caches."
                )
            logger.warning(warning_msg)

        return available


class ExecuteCachedTrajectory(Tool):
    """
    Execute or continue a predefined trajectory to fast-forward through UI interactions
    """

    def __init__(
        self,
        toolbox: ToolCollection,
        settings: CachedExecutionToolSettings | None = None,
    ) -> None:
        super().__init__(
            name="execute_cached_executions_tool",
            description=(
                "Activate cache execution mode to replay a pre-recorded "
                "trajectory. This tool sets up the agent to execute cached UI "
                "interactions step-by-step.\n\n"
                "Before using this tool:\n"
                "1. Use retrieve_available_trajectories_tool to see which "
                "trajectory files are available\n"
                "2. Select the appropriate trajectory file path from the "
                "returned list\n"
                "3. If the trajectory contains parameters (e.g., "
                "{{current_date}}), provide values for them in the "
                "parameter_values parameter\n"
                "4. Pass the full file path to this tool\n\n"
                "Cache parameters allow dynamic values to be injected during "
                "execution. For example, if a trajectory types "
                "'{{current_date}}', you must provide "
                "parameter_values={'current_date': '2025-12-11'}.\n\n"
                "To continue from a specific step (e.g., after manually "
                "handling a non-cacheable step), use the start_from_step_index "
                "parameter. By default, execution starts from the beginning "
                "(step 0).\n\n"
                "Once activated, the agent will execute cached steps "
                "automatically. If a non-cacheable step is encountered, the "
                "agent will be asked to handle it manually before resuming "
                "cache execution."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "trajectory_file": {
                        "type": "string",
                        "description": (
                            "Full path to the trajectory file (use "
                            "retrieve_available_trajectories_tool to find "
                            "available files)"
                        ),
                    },
                    "start_from_step_index": {
                        "type": "integer",
                        "description": (
                            "Optional: The step index to start or resume "
                            "execution from (0-based). Use 0 (default) to start "
                            "from the beginning. Use a higher index to continue "
                            "from a specific step, e.g., after manually handling "
                            "a non-cacheable step."
                        ),
                        "default": 0,
                    },
                    "parameter_values": {
                        "type": "object",
                        "description": (
                            "Optional dictionary mapping parameter names to "
                            "their values. Required if the trajectory contains "
                            "parameters like {{variable}}. Example: "
                            "{'current_date': '2025-12-11', 'user_name': 'Alice'}"
                        ),
                        "additionalProperties": {"type": "string"},
                        "default": {},
                    },
                },
                "required": ["trajectory_file"],
            },
        )
        if not settings:
            settings = CachedExecutionToolSettings()
        self._settings = settings
        self._cache_execution_manager: CacheExecutionManager | None = None
        self._toolbox = toolbox

    def set_cache_execution_manager(
        self, cache_execution_manager: CacheExecutionManager
    ) -> None:
        """Set the agent reference for cache execution mode activation.

        Args:
            agent: The Agent instance that will execute the cached trajectory
        """
        self._cache_execution_manager = cache_execution_manager

    def _validate_trajectory_file(self, trajectory_file: str) -> str | None:
        """Validate that trajectory file exists.

        Args:
            trajectory_file: Path to the trajectory file

        Returns:
            Error message if validation fails, None otherwise
        """
        if not Path(trajectory_file).is_file():
            error_msg = (
                f"Trajectory file not found: {trajectory_file}\n"
                "Use retrieve_available_trajectories_tool to see "
                "available files."
            )
            logger.error(error_msg)
            return error_msg
        return None

    def _validate_step_index(
        self, start_from_step_index: int, trajectory_length: int
    ) -> str | None:
        """Validate step index is within bounds.

        Args:
            start_from_step_index: Index to start from
            trajectory_length: Total number of steps in trajectory

        Returns:
            Error message if validation fails, None otherwise
        """
        logger.debug(
            "Validating start_from_step_index=%d (trajectory has %d steps)",
            start_from_step_index,
            trajectory_length,
        )
        if start_from_step_index < 0 or start_from_step_index >= trajectory_length:
            error_msg = (
                f"Invalid start_from_step_index: {start_from_step_index}. "
                f"Trajectory has {trajectory_length} steps "
                f"(valid indices: 0-{trajectory_length - 1})."
            )
            logger.error(error_msg)
            return error_msg
        return None

    def _validate_parameters(
        self,
        trajectory: list["ToolUseBlockParam"],
        parameter_values: dict[str, str],
        cache_parameters: dict[str, str],
    ) -> str | None:
        """Validate parameter values.

        Args:
            trajectory: The cached trajectory
            parameter_values: User-provided parameter values
            cache_parameters: Parameters defined in cache file

        Returns:
            Error message if validation fails, None otherwise
        """
        logger.debug("Validating parameter values")
        is_valid, missing = CacheParameterHandler.validate_parameters(
            trajectory, parameter_values
        )
        if not is_valid:
            error_msg = (
                f"Missing required parameter values: {', '.join(missing)}\n"
                f"The trajectory contains the following parameters: "
                f"{', '.join(cache_parameters.keys())}\n"
                f"Please provide values for all parameters in the "
                f"parameter_values parameter."
            )
            logger.error(error_msg)
            return error_msg
        return None

    def _create_executor(
        self,
        cache_file: "CacheFile",
        parameter_values: dict[str, str],
        start_from_step_index: int,
    ) -> "TrajectoryExecutor":
        """Create and configure trajectory executor.

        Args:
            cache_file: The cache file to execute
            parameter_values: Parameter values to use
            start_from_step_index: Index to start execution from

        Returns:
            Configured TrajectoryExecutor instance
        """
        logger.debug(
            "Creating TrajectoryExecutor with delay=%ss",
            self._settings.delay_time_between_action,
        )

        # Import here to avoid circular dependency
        from askui.utils.caching.trajectory_executor import TrajectoryExecutor

        executor = TrajectoryExecutor(
            trajectory=cache_file.trajectory,
            toolbox=self._toolbox,
            parameter_values=parameter_values,
            delay_time=self._settings.delay_time_between_action,
        )

        # Set the starting position if continuing
        if start_from_step_index > 0:
            executor.current_step_index = start_from_step_index
            logger.debug(
                "Set executor start position to step %d", start_from_step_index
            )

        return executor

    def _format_success_message(
        self,
        trajectory_file: str,
        trajectory_length: int,
        start_from_step_index: int,
        parameter_count: int,
    ) -> str:
        """Format success message.

        Args:
            trajectory_file: Path to trajectory file
            trajectory_length: Total steps in trajectory
            start_from_step_index: Starting step index
            parameter_count: Number of parameters used

        Returns:
            Formatted success message
        """
        if start_from_step_index == 0:
            success_msg = (
                f"✓ Cache execution mode activated for "
                f"{Path(trajectory_file).name}. "
                f"Will execute {trajectory_length} cached steps."
            )
        else:
            remaining_steps = trajectory_length - start_from_step_index
            success_msg = (
                f"✓ Cache execution mode activated, resuming from step "
                f"{start_from_step_index}. "
                f"Will execute {remaining_steps} remaining cached steps."
            )

        if parameter_count > 0:
            success_msg += f" Using {parameter_count} parameter value(s)."

        return success_msg

    @override
    @validate_call
    def __call__(
        self,
        trajectory_file: str,
        start_from_step_index: int = 0,
        parameter_values: dict[str, str] | None = None,
    ) -> str:
        """Activate cache execution mode for the agent.

        This method validates the cache file and sets up the agent to execute
        cached steps. The actual execution happens in the agent's step loop.

        Returns:
            Success message indicating cache mode has been activated
        """
        if parameter_values is None:
            parameter_values = {}

        logger.info(
            "Activating cache execution mode: %s (start_from_step=%d)",
            Path(trajectory_file).name,
            start_from_step_index,
        )

        # Validate agent is set
        if not self._cache_execution_manager:
            error_msg = (
                "Cache Execution Manager not set. Call "
                "set_cache_execution_manager() first."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Validate trajectory file exists
        if error := self._validate_trajectory_file(trajectory_file):
            return error

        # Load cache file
        logger.debug("Loading cache file: %s", trajectory_file)
        cache_file = CacheWriter.read_cache_file(Path(trajectory_file))

        logger.debug(
            "Cache loaded: %d steps, %d parameters, valid=%s",
            len(cache_file.trajectory),
            len(cache_file.cache_parameters),
            cache_file.metadata.is_valid,
        )

        # Warn if cache is invalid
        if not cache_file.metadata.is_valid:
            warning_msg = (
                f"WARNING: Using invalid cache from "
                f"{Path(trajectory_file).name}. "
                f"Reason: {cache_file.metadata.invalidation_reason}. "
                "This cache may not work correctly."
            )
            logger.warning(warning_msg)

        # Validate step index
        if error := self._validate_step_index(
            start_from_step_index, len(cache_file.trajectory)
        ):
            return error

        # Validate parameters
        if error := self._validate_parameters(
            cache_file.trajectory, parameter_values, cache_file.cache_parameters
        ):
            return error

        # Create and configure executor
        executor = self._create_executor(
            cache_file, parameter_values, start_from_step_index
        )

        # Store executor and cache info in agent state
        self._cache_execution_manager.activate_execution(
            executor=executor,
            cache_file=cache_file,
            cache_file_path=trajectory_file,
        )

        # Format and return success message
        success_msg = self._format_success_message(
            trajectory_file,
            len(cache_file.trajectory),
            start_from_step_index,
            len(parameter_values),
        )
        logger.info(success_msg)
        return success_msg


class InspectCacheMetadata(Tool):
    """
    Inspect detailed metadata for a cached trajectory file
    """

    def __init__(self) -> None:
        super().__init__(
            name="inspect_cache_metadata_tool",
            description=(
                "Inspect and display detailed metadata for a cached trajectory file. "
                "This tool shows information about:\n"
                "- Cache version and creation timestamp\n"
                "- Execution statistics (attempts, last execution time)\n"
                "- Validity status and invalidation reason (if invalid)\n"
                "- Failure history with timestamps and error messages\n"
                "- Parameters and trajectory step count\n\n"
                "Use this tool to debug cache issues or understand why a cache "
                "might be failing or invalidated."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "trajectory_file": {
                        "type": "string",
                        "description": (
                            "Full path to the trajectory file to inspect. "
                            "Use retrieve_available_trajectories_tool to "
                            "find available files."
                        ),
                    },
                },
                "required": ["trajectory_file"],
            },
        )

    @override
    @validate_call
    def __call__(self, trajectory_file: str) -> str:
        logger.info("Inspecting cache metadata: %s", Path(trajectory_file).name)

        if not Path(trajectory_file).is_file():
            error_msg = (
                f"Trajectory file not found: {trajectory_file}\n"
                "Use retrieve_available_trajectories_tool to see available files."
            )
            logger.error(error_msg)
            return error_msg

        try:
            cache_file = CacheWriter.read_cache_file(Path(trajectory_file))
        except Exception:
            error_msg = f"Failed to read cache file {Path(trajectory_file).name}"
            logger.exception(error_msg)
            return error_msg

        metadata = cache_file.metadata
        logger.debug(
            "Metadata loaded: version=%s, valid=%s, attempts=%d, failures=%d",
            metadata.version,
            metadata.is_valid,
            metadata.execution_attempts,
            len(metadata.failures),
        )

        # Format the metadata into a readable string
        lines = [
            "=== Cache Metadata ===",
            f"File: {trajectory_file}",
            "",
            "--- Basic Info ---",
            f"Version: {metadata.version}",
            f"Created: {metadata.created_at}",
            f"Last Executed: {metadata.last_executed_at or 'Never'}",
            "",
            "--- Execution Statistics ---",
            f"Total Execution Attempts: {metadata.execution_attempts}",
            f"Total Failures: {len(metadata.failures)}",
            "",
            "--- Validity Status ---",
            f"Is Valid: {metadata.is_valid}",
        ]

        if not metadata.is_valid:
            lines.append(f"Invalidation Reason: {metadata.invalidation_reason}")

        lines.append("")
        lines.append("--- Trajectory Info ---")
        lines.append(f"Total Steps: {len(cache_file.trajectory)}")
        lines.append(f"Parameters: {len(cache_file.cache_parameters)}")
        if cache_file.cache_parameters:
            lines.append(
                f"Parameter Names: {', '.join(cache_file.cache_parameters.keys())}"
            )

        if metadata.failures:
            lines.append("")
            lines.append("--- Failure History ---")
            for i, failure in enumerate(metadata.failures, 1):
                lines.append(f"Failure {i}:")
                lines.append(f"  Timestamp: {failure.timestamp}")
                lines.append(f"  Step Index: {failure.step_index}")
                lines.append(
                    f"  Failure Count at Step: {failure.failure_count_at_step}"
                )
                lines.append(f"  Error: {failure.error_message}")

        return "\n".join(lines)


class RevalidateCache(Tool):
    """
    Manually mark a cache as valid (reset invalidation)
    """

    def __init__(self) -> None:
        super().__init__(
            name="revalidate_cache_tool",
            description=(
                "Manually mark a cache as valid, resetting any previous invalidation. "
                "Use this tool when:\n"
                "- A cache was invalidated but the underlying issue has been fixed\n"
                "- You want to give a previously failing cache another chance\n"
                "- You've manually verified the cache should work now\n\n"
                "This will:\n"
                "- Set is_valid=True\n"
                "- Clear the invalidation_reason\n"
                "- Keep existing failure history (for debugging)\n"
                "- Keep execution attempt counters\n\n"
                "Note: The cache can still be auto-invalidated again if it "
                "continues to fail."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "trajectory_file": {
                        "type": "string",
                        "description": (
                            "Full path to the trajectory file to revalidate. "
                            "Use retrieve_available_trajectories_tool with "
                            "include_invalid=True to find invalidated caches."
                        ),
                    },
                },
                "required": ["trajectory_file"],
            },
        )

    @override
    @validate_call
    def __call__(self, trajectory_file: str) -> str:
        if not Path(trajectory_file).is_file():
            error_msg = (
                f"Trajectory file not found: {trajectory_file}\n"
                "Use retrieve_available_trajectories_tool to see available files."
            )
            logger.error(error_msg)
            return error_msg

        try:
            cache_file = CacheWriter.read_cache_file(Path(trajectory_file))
        except Exception:
            error_msg = f"Failed to read cache file {trajectory_file}"
            logger.exception(error_msg)
            return error_msg

        # Mark cache as valid
        cache_manager = CacheManager()
        was_invalid = not cache_file.metadata.is_valid
        previous_reason = cache_file.metadata.invalidation_reason

        cache_manager.mark_cache_valid(cache_file)

        # Write back to disk
        try:
            cache_path = Path(trajectory_file)
            with cache_path.open("w") as f:
                json.dump(
                    cache_file.model_dump(mode="json"),
                    f,
                    indent=2,
                    default=str,
                )
        except Exception:
            error_msg = f"Failed to write cache file {trajectory_file}"
            logger.exception(error_msg)
            return error_msg

        if was_invalid:
            logger.info("Cache revalidated: %s", trajectory_file)
            return (
                f"Successfully revalidated cache: {trajectory_file}\n"
                f"Previous invalidation reason was: {previous_reason}\n"
                "The cache is now marked as valid and can be used again."
            )
        logger.info("Cache was already valid: %s", trajectory_file)
        return f"Cache {trajectory_file} was already valid. No changes made."


class InvalidateCache(Tool):
    """
    Manually mark a cache as invalid
    """

    def __init__(self) -> None:
        super().__init__(
            name="invalidate_cache_tool",
            description=(
                "Manually mark a cache as invalid with a custom reason. "
                "Use this tool when:\n"
                "- You've determined a cache is no longer reliable\n"
                "- The UI has changed and the cached actions won't work\n"
                "- You want to prevent automatic execution of a problematic cache\n\n"
                "This will:\n"
                "- Set is_valid=False\n"
                "- Record your custom invalidation reason\n"
                "- Keep all existing metadata (failures, execution attempts)\n"
                "- Hide the cache from default trajectory listings\n\n"
                "The cache can later be revalidated using revalidate_cache_tool "
                "if the issue is resolved."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "trajectory_file": {
                        "type": "string",
                        "description": (
                            "Full path to the trajectory file to "
                            "invalidate. "
                            "Use retrieve_available_trajectories_tool to "
                            "find available files."
                        ),
                    },
                    "reason": {
                        "type": "string",
                        "description": (
                            "Reason for invalidating this cache. "
                            "Be specific about why "
                            "this cache should not be used "
                            "(e.g., 'UI changed - button moved', "
                            "'Workflow outdated', 'Replaced by new cache')."
                        ),
                    },
                },
                "required": ["trajectory_file", "reason"],
            },
        )

    @override
    @validate_call
    def __call__(self, trajectory_file: str, reason: str) -> str:
        if not Path(trajectory_file).is_file():
            error_msg = (
                f"Trajectory file not found: {trajectory_file}\n"
                "Use retrieve_available_trajectories_tool to see available files."
            )
            logger.error(error_msg)
            return error_msg

        try:
            cache_file = CacheWriter.read_cache_file(Path(trajectory_file))
        except Exception:
            error_msg = f"Failed to read cache file {trajectory_file}"
            logger.exception(error_msg)
            return error_msg

        # Mark cache as invalid
        cache_manager = CacheManager()
        was_valid = cache_file.metadata.is_valid

        cache_manager.invalidate_cache(cache_file, reason=reason)

        # Write back to disk
        try:
            cache_path = Path(trajectory_file)
            with cache_path.open("w") as f:
                json.dump(
                    cache_file.model_dump(mode="json"),
                    f,
                    indent=2,
                    default=str,
                )
        except Exception:
            error_msg = f"Failed to write cache file {trajectory_file}"
            logger.exception(error_msg)
            return error_msg

        logger.info("Cache manually invalidated: %s", trajectory_file)

        if was_valid:
            return (
                f"Successfully invalidated cache: {trajectory_file}\n"
                f"Reason: {reason}\n"
                "The cache will not appear in default trajectory listings. "
                "Use revalidate_cache_tool to restore it if needed."
            )
        return (
            f"Cache {trajectory_file} was already invalid.\n"
            f"Updated invalidation reason to: {reason}"
        )


class VerifyCacheExecution(Tool):
    """Tool for agent to explicitly report cache execution verification results."""

    def __init__(self) -> None:
        super().__init__(
            name="verify_cache_execution",
            description=(
                "IMPORTANT: Call this tool immediately after reviewing a "
                "cached trajectory execution.\n\n"
                "Report whether the cached execution successfully achieved "
                "the target system state. You MUST call this tool to complete "
                "the cache verification process.\n\n"
                "Set success=True if:\n"
                "- The cached execution correctly achieved the intended goal\n"
                "- The final state matches what was expected\n"
                "- No corrections or additional actions were needed\n\n"
                "Set success=False if:\n"
                "- The execution did not achieve the target state\n"
                "- You had to make corrections or perform additional actions\n"
                "- The final state is incorrect or incomplete"
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "description": (
                            "True if cached execution correctly "
                            "achieved target state, "
                            "False if execution was incorrect or "
                            "corrections were needed"
                        ),
                    },
                    "verification_notes": {
                        "type": "string",
                        "description": (
                            "Brief explanation of what you verified. "
                            "If success=False, describe what was "
                            "wrong and what corrections you made."
                        ),
                    },
                },
                "required": ["success", "verification_notes"],
            },
        )
        self.is_cacheable = False  # Verification is not cacheable
        self._cache_execution_manager: CacheExecutionManager | None = None

    def set_cache_execution_manager(
        self, cache_execution_manager: CacheExecutionManager
    ) -> None:
        """Set the agent reference for cache execution mode activation.

        Args:
            agent: The Agent instance that will execute the cached trajectory
        """
        self._cache_execution_manager = cache_execution_manager

    @override
    @validate_call
    def __call__(self, success: bool, verification_notes: str) -> str:
        """Record cache verification result.

        Args:
            success: Whether cache execution achieved target state
            verification_notes: Explanation of verification result

        Returns:
            Confirmation message
        """
        logger.info(
            "Cache verification reported: success=%s, notes=%s",
            success,
            verification_notes,
        )
        if not self._cache_execution_manager:
            error_msg = (
                "Cache Execution Manager not set. Cannot record verification result."
            )
            logger.error(error_msg)
            return error_msg

        # Check if there's a cache file to update (more reliable than checking flag)
        cache_file, cache_file_path = self._cache_execution_manager.get_cache_info()
        if not (cache_file and cache_file_path):
            warning_msg = (
                "No cache file to update. "
                "Verification tool called without recent cache execution."
            )
            logger.warning(warning_msg)
            return warning_msg

        # Debug log if verification flag wasn't explicitly set
        # (This can happen if verification is called directly without the flag,
        # but we still proceed since we have the cache file)
        if not self._cache_execution_manager.is_cache_verification_pending():
            logger.debug(
                "Verification flag not set, but cache file exists. "
                "This is normal for direct verification calls."
            )

        # Update cache metadata based on verification result
        if success:
            self._cache_execution_manager.update_metadata_on_completion(success=True)
            result_msg = f"✓ Cache verification successful: {verification_notes}"
            logger.info(result_msg)
        else:
            error_msg = (
                f"Cache execution did not lead to target system state: "
                f"{verification_notes}"
            )
            self._cache_execution_manager.update_metadata_on_failure(
                step_index=-1,  # -1 indicates verification failure
                error_message=error_msg,
            )
            result_msg = (
                f"✗ Cache verification failed: {verification_notes}\n\n"
                "The cached trajectory did not achieve the target system "
                "state correctly. You should now continue to complete the "
                "task manually from the current state. Use your tools to "
                "finish achieving the goal, taking into account what the "
                "cache attempted to do and what corrections are needed."
            )
            logger.warning(result_msg)

        # Clear verification flag and cache references after verification
        self._cache_execution_manager.clear_cache_state()

        return result_msg
