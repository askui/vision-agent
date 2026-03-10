"""Callback for terminating the agentic loop after a maximum number of steps."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from askui.models.exceptions import MaxStepsReachedError
from askui.models.shared.conversation_callback import ConversationCallback

if TYPE_CHECKING:
    from askui.models.shared.conversation import Conversation


class MaxStepsCallback(ConversationCallback):
    """Terminates the agentic loop after a maximum number of steps.

    Args:
        max_steps (int): The maximum number of steps before the loop is terminated.

    Raises:
        MaxStepsReachedError: When the step limit is reached.

    Example:
        ```python
        from askui import ComputerAgent, MaxStepsCallback

        with ComputerAgent(callbacks=[MaxStepsCallback(max_steps=10)]) as agent:
            agent.act("Open the settings menu")
        ```
    """

    def __init__(self, max_steps: int) -> None:
        self._max_steps = max_steps

    @override
    def on_step_start(self, conversation: Conversation, step_index: int) -> None:
        if step_index >= self._max_steps:
            raise MaxStepsReachedError(self._max_steps)
