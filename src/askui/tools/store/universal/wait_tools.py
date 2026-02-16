import logging
import time
from typing import Callable

from askui.models.shared.tools import Tool

logger = logging.getLogger(__name__)


class WaitingForTool(Tool):
    """
    Tool for waiting until a specific condition is met.

    This tool periodically checks a user-provided exit criterion and waits until
    the condition returns True or the maximum wait time is reached. It is useful
    for scenarios where the agent needs to wait for an external event or state
    change, such as waiting for a process to complete, a file to appear, or a
    system to become available.

    Args:
        exit_criterion (Callable[[], bool]): A callable that takes no arguments
            and returns a boolean. The tool will keep waiting until this callable
            returns True.
        condition_description (str): A human-readable description of what condition
            is being checked. This is shown to the agent so it understands what
            it is waiting for.

    Example:
        ```python
        from askui import VisionAgent
        from askui.tools.store.universal import WaitingForTool

        def check_file_exists():
            return os.path.exists("/path/to/expected/file.txt")

        with VisionAgent() as agent:
            agent.act(
                "Wait for the download to complete",
                tools=[WaitingForTool(
                    exit_criterion=check_file_exists,
                    condition_description="the file /path/to/expected/file.txt exists"
                )]
            )
        ```
    """

    def __init__(
        self, exit_criterion: Callable[[], bool], condition_description: str
    ) -> None:
        super().__init__(
            name="wait_for_tool",
            description=(
                f"Waits until {condition_description}. This tool periodically checks "
                "the condition and returns when it is met or the timeout is reached."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "max_wait_time": {
                        "type": "integer",
                        "description": (
                            "The maximum wait time in minutes before timing out. "
                            "Defaults to 10 minutes if not specified."
                        ),
                    },
                    "check_interval": {
                        "type": "integer",
                        "description": (
                            "The interval time in seconds between two checks. "
                            "Defaults to 10 seconds if not specified."
                        ),
                    },
                },
                "required": [],
            },
        )
        self._exit_criterion = exit_criterion

    def __call__(self, max_wait_time: int = 10, check_interval: int = 10) -> str:
        """
        Wait for the exit criterion to be met.

        Args:
            max_wait_time (int): The maximum wait time in minutes before timing out.
                Defaults to 10 minutes.
            check_interval (int): The interval time in seconds between two checks.
                Defaults to 10 seconds.

        Returns:
            str: A message indicating whether the condition was met or the timeout
                was reached.
        """
        latest_end_time = time.time() + max_wait_time * 60
        msg = f"Waiting for condition to be met (max {max_wait_time} minutes)..."
        logger.info(msg)
        while True:
            # Check wait exit criterion
            finished_waiting = self._exit_criterion()
            # Evaluate exit criteria
            if finished_waiting:
                logger.info("Finished Waiting")
                return "Finished Waiting"

            if time.time() > latest_end_time:
                logger.warning("Maximum Waiting time reached")
                return (
                    f"The maximum waiting time of {max_wait_time} minutes was reached "
                    "without the exit criterion being met."
                )
            msg = f"Checking again in {check_interval} seconds..."
            logger.info(msg)
            time.sleep(check_interval)


class WaitingTool(Tool):
    """
    Tool for waiting (sleeping) for a specified amount of time.

    This tool pauses execution for a given duration. It is useful when the agent
    needs to wait for a fixed amount of time, such as waiting for a slow operation
    to complete, giving the system time to process, or implementing a delay between
    actions.

    Example:
        ```python
        from askui import VisionAgent
        from askui.tools.store.universal import WaitingTool

        with VisionAgent() as agent:
            agent.act(
                "Submit the form and wait 2 minutes for processing",
                tools=[WaitingTool()]
            )
        ```
    """

    def __init__(self) -> None:
        super().__init__(
            name="waiting_tool",
            description=("Waits (i.e. sleeps) for a specified time."),
            input_schema={
                "type": "object",
                "properties": {
                    "wait_time": {
                        "type": "integer",
                        "description": ("The wait time in minutes before timing out. "),
                    },
                },
                "required": ["wait_time"],
            },
        )

    def __call__(self, wait_time: int = 10) -> str:
        """
        Wait for the specified amount of time.

        Args:
            wait_time (int): The wait time in minutes. Defaults to 10 minutes.

        Returns:
            str: A confirmation message indicating that the wait has completed.
        """
        msg = f"Waiting for {wait_time} minutes..."
        logger.info(msg)
        time.sleep(wait_time * 60)
        logger.info("Finished waiting")
        return "Finished waiting"
