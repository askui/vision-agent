from typing import Any

from askui.models.shared import ComputerBaseTool
from askui.models.shared.tool_tags import ToolTags
from askui.tools.agent_os import AgentOs
from askui.tools.agent_os_type_error import AgentOsTypeError
from askui.tools.android.agent_os import AndroidAgentOs
from askui.tools.askui.askui_controller import AskUiControllerClient


class AskUiComputerBaseTool(ComputerBaseTool):
    """
    Base tool for AskUI computer tools.
    Tools that can only operate with the AskUiControllerClient as agent_os.
    """

    def __init__(
        self,
        agent_os: AgentOs | None = None,
        required_tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            required_tags=[ToolTags.ASKUI_CONTROLLER.value] + (required_tags or []),
            agent_os=agent_os,
            **kwargs,
        )

    @property
    def agent_os(self) -> AskUiControllerClient:
        """Get the agent OS.

        Returns:
            AgentOs: The agent OS instance.
        """
        agent_os = super().agent_os
        if not isinstance(agent_os, AskUiControllerClient):
            raise AgentOsTypeError(
                expected_type=AskUiControllerClient,
                actual_type=type(agent_os),
            )
        return agent_os

    @agent_os.setter
    def agent_os(self, agent_os: AgentOs | AndroidAgentOs) -> None:
        """Set the agent OS facade.

        Args:
            agent_os (AgentOs | AndroidAgentOs): The agent OS facade instance to set.

        Raises:
            TypeError: If the agent OS is not an AgentOs instance.
        """
        if not isinstance(agent_os, AskUiControllerClient):
            raise AgentOsTypeError(
                expected_type=AskUiControllerClient,
                actual_type=type(agent_os),
            )
        self._agent_os = agent_os
