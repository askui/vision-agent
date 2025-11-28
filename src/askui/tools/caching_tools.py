import logging
import time
from pathlib import Path

from pydantic import validate_call
from typing_extensions import override

from ..models.shared.tools import Tool, ToolCollection
from ..utils.cache_writer import CacheWriter

logger = logging.getLogger()


class RetrieveCachedTestExecutions(Tool):
    """
    List all available trajectory files that can be used for fast-forward execution
    """

    def __init__(self, cache_dir: str, trajectories_format: str = ".json") -> None:
        super().__init__(
            name="retrieve_available_trajectories_tool",
            description="""
            Use this tool to list all available pre-recorded trajectory files in the trajectories directory.
            These trajectories represent successful UI interaction sequences that can be replayed using the execute_trajectory_tool.
            Call this tool first to see which trajectories are available before executing one.
            The tool returns a list of file paths to available trajectory files.
            """,
        )
        self._cache_dir = Path(cache_dir)
        self._trajectories_format = trajectories_format

    @override
    @validate_call
    def __call__(self) -> list[str]:  # type: ignore
        if not Path.is_dir(self._cache_dir):
            raise FileNotFoundError(
                f"Trajectories directory not found: {self._cache_dir}"
            )

        available = [
            str(f)
            for f in self._cache_dir.iterdir()
            if str(f).endswith(self._trajectories_format)
        ]

        if not available:
            logger.warning(f"Warning: No trajectory files found in {self._cache_dir}")

        return available


class ExecuteCachedExecution(Tool):
    """
    Execute a predefined trajectory to fast-forward through UI interactions
    """

    def __init__(self) -> None:
        super().__init__(
            name="execute_cached_executions_tool",
            description="""
            Execute a pre-recorded trajectory to automatically perform a sequence of UI interactions.
            This tool replays mouse movements, clicks, and typing actions from a previously successful execution.

            Before using this tool:
            1. Use retrieve_available_trajectories_tool to see which trajectory files are available
            2. Select the appropriate trajectory file path from the returned list
            3. Pass the full file path to this tool

            The trajectory will be executed step-by-step, and you should verify the results afterward.
            Note: Trajectories may fail if the UI state has changed since they were recorded.
            """,
            input_schema={
                "type": "object",
                "properties": {
                    "trajectory_file": {
                        "type": "string",
                        "description": "Full path to the trajectory file (use retrieve_available_trajectories_tool to find available files)",
                    },
                },
                "required": ["trajectory_file"],
            },
        )

    def set_toolbox(self, toolbox: ToolCollection) -> None:
        """Set the AgentOS/AskUiControllerClient reference for executing UI actions"""
        self._toolbox = toolbox

    @override
    @validate_call
    def __call__(self, trajectory_file: str) -> str:
        if not hasattr(self, "_toolbox"):
            raise RuntimeError("Toolbox not set. Call set_toolbox() first.")

        if not Path(trajectory_file).is_file():
            raise FileNotFoundError(
                f"Trajectory file not found: {trajectory_file}\n"
                f"Use retrieve_available_trajectories_tool to see available files."
            )

        # Load and execute trajectory
        trajectory = CacheWriter.read_cache_file(Path(trajectory_file))
        logger.info(f"Executing cached trajectory from {trajectory_file}")
        for step in trajectory:
            if (
                "screenshot" in step.name
                or step.name == "retrieve_available_trajectories_tool"
            ):
                continue
            try:
                self._toolbox.run([step])
            except Exception as e:
                logger.warning(f"An error occured during the cached execution: {e}")
                return f"An error occured while executing the trajectory from {trajectory_file}. Please verify the UI state and continue without cache."
            time.sleep(2)

        logger.info("Finished executing cached trajectory")
        return f"Successfully executed trajectory from {trajectory_file}. Please verify the UI state."
