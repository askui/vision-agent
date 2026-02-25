import logging
import time
from pathlib import Path
from typing import Any

from pydantic import validate_call
from typing_extensions import override

from ..models.shared.settings import CacheExecutionSettings
from ..models.shared.tools import Tool, ToolCollection
from ..utils.caching.cache_manager import CacheManager
from ..utils.caching.cache_parameter_handler import CacheParameterHandler

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
                "available trajectory files."
            ),
        )
        self._cache_dir = Path(cache_dir)
        self._trajectories_format = trajectories_format
        self.is_cacheable = True

    @override
    @validate_call
    def __call__(self) -> list[str]:  # type: ignore
        if not Path.is_dir(self._cache_dir):
            error_msg = f"Trajectories directory not found: {self._cache_dir}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        available = [
            str(f)
            for f in self._cache_dir.iterdir()
            if str(f).endswith(self._trajectories_format)
        ]

        if not available:
            msg = f"No trajectory files found in {self._cache_dir}"
            logger.info(msg)

        return available


class ExecuteCachedTrajectory(Tool):
    """
    Execute a predefined trajectory to fast-forward through UI interactions
    """

    def __init__(self, settings: CacheExecutionSettings | None = None) -> None:
        super().__init__(
            name="execute_cached_executions_tool",
            description=(
                "Execute a pre-recorded trajectory to automatically perform a "
                "sequence of UI interactions. This tool replays mouse movements, "
                "clicks, and typing actions from a previously successful execution.\n\n"
                "Before using this tool:\n"
                "1. Use retrieve_available_trajectories_tool to see which "
                "trajectory files are available\n"
                "2. Select the appropriate trajectory file path from the "
                "returned list\n"
                "3. If the trajectory contains parameters (e.g., {{target_url}}), "
                "provide values for them in the parameter_values parameter\n"
                "4. Pass the full file path to this tool\n\n"
                "Cache parameters allow dynamic values to be injected during "
                "execution. For example, if a trajectory types '{{target_url}}', "
                "you must provide parameter_values={'target_url': 'https://...'}.\n\n"
                "The trajectory will be executed step-by-step, and you should "
                "verify the results afterward. Note: Trajectories may fail if "
                "the UI state has changed since they were recorded."
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
                    "parameter_values": {
                        "type": "object",
                        "description": (
                            "Optional dictionary mapping parameter names to "
                            "their values. Required if the trajectory contains "
                            "parameters like {{variable}}. Example: "
                            "{'target_url': 'https://example.com'}"
                        ),
                        "additionalProperties": {"type": "string"},
                    },
                },
                "required": ["trajectory_file"],
            },
        )
        if not settings:
            settings = CacheExecutionSettings()
        self._settings = settings

    def set_toolbox(self, toolbox: ToolCollection) -> None:
        """Set the AgentOS/AskUiControllerClient reference for executing actions."""
        self._toolbox = toolbox

    @override
    @validate_call
    def __call__(
        self,
        trajectory_file: str,
        parameter_values: dict[str, Any] | None = None,
    ) -> str:
        if not hasattr(self, "_toolbox"):
            error_msg = "Toolbox not set. Call set_toolbox() first."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        if not Path(trajectory_file).is_file():
            error_msg = (
                f"Trajectory file not found: {trajectory_file}\n"
                "Use retrieve_available_trajectories_tool to see available files."
            )
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Load trajectory
        cache_file = CacheManager.read_cache_file(Path(trajectory_file))
        trajectory = cache_file.trajectory
        parameter_values = parameter_values or {}

        # Validate parameters
        is_valid, missing_params = CacheParameterHandler.validate_parameters(
            trajectory, parameter_values
        )
        if not is_valid:
            error_msg = (
                f"Missing required parameter values: {missing_params}. "
                f"The cache file expects these parameters. "
                f"Available parameters in cache: {cache_file.cache_parameters}"
            )
            logger.error(error_msg)
            return error_msg

        info_msg = f"Executing cached trajectory from {trajectory_file}"
        logger.info(info_msg)
        for step in trajectory:
            # Skip non-action tools (screenshots, cache management tools)
            if (
                "screenshot" in step.name
                or step.name.startswith("retrieve_available_trajectories_tool")
                or step.name.startswith("execute_cached_executions_tool")
            ):
                continue

            # Substitute parameters in the step before execution
            substituted_step = CacheParameterHandler.substitute_parameters(
                step, parameter_values
            )

            try:
                results = self._toolbox.run([substituted_step])
                # Check for tool execution errors
                if results and hasattr(results[0], "is_error") and results[0].is_error:
                    error_content = getattr(results[0], "content", "Unknown error")
                    error_msg = f"Tool error during cached execution: {error_content}"
                    logger.error(error_msg)
                    return (
                        f"An error occurred while executing the trajectory from "
                        f"{trajectory_file}: {error_content}. Please verify the UI "
                        "state and continue without cache."
                    )
            except Exception as e:
                error_msg = f"An error occurred during the cached execution: {e}"
                logger.exception(error_msg)
                return (
                    f"An error occurred while executing the trajectory from "
                    f"{trajectory_file}. Please verify the UI state and "
                    "continue without cache."
                )
            time.sleep(self._settings.delay_time_between_action)

        logger.info("Finished executing cached trajectory")
        return (
            f"Successfully executed trajectory from {trajectory_file}. "
            "Please verify the UI state."
        )
