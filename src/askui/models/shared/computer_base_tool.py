from typing import Any

from askui.models.shared.tool_tags import ToolTags
from askui.models.shared.tools import ToolWithAgentOS
from askui.tools.agent_os import AgentOs
from askui.tools.android.agent_os import AndroidAgentOs


class ComputerBaseTool(ToolWithAgentOS):
    """Tool base class that has an AgentOs available."""

    def __init__(
        self,
        agent_os: AgentOs | None = None,
        required_tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            required_tags=[ToolTags.COMPUTER.value] + (required_tags or []),
            agent_os=agent_os,
            **kwargs,
        )

    @property
    def agent_os(self) -> AgentOs:
        """Get the agent OS.

        Returns:
            AgentOs: The agent OS instance.
        """
        agent_os = super().agent_os
        if not isinstance(agent_os, AgentOs):
            msg = (
                "Agent OS is not a ComputerAgentOs. "
                "Call `agent_os = ...` or initialize the tool with a "
                "ComputerAgentOs."
            )
            raise TypeError(msg)
        return agent_os

    @agent_os.setter
    def agent_os(self, agent_os: AgentOs | AndroidAgentOs) -> None:
        """Set the agent OS facade.

        Args:
            agent_os (AgentOs | AndroidAgentOs): The agent OS facade instance to set.

        Raises:
            TypeError: If the agent OS is not an AgentOs instance.
        """
        if not isinstance(agent_os, AgentOs):
            msg = (
                "Agent OS must be an AgentOs instance. "
                f"Got {type(agent_os).__name__} instead."
            )
            raise TypeError(msg)
        self._agent_os = agent_os
