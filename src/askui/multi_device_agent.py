from typing import Annotated

from pydantic import Field

from askui.agent import ComputerAgent
from askui.agent_base import Agent
from askui.agent_settings import AgentSettings
from askui.android_agent import AndroidAgent
from askui.models.shared.tools import Tool
from askui.prompts.act_prompts import create_multidevice_agent_prompt
from askui.reporting import CompositeReporter, Reporter
from askui.retry import Retry


class MultiDeviceAgent(Agent):
    """
    Multi device agent that combines a computer and an Android agent.
    It can be used to perform actions on both devices simultaneously.

    Args:
        display (int, optional): The display number for computer screen
            interactions. Defaults to `1`.
        reporters (list[Reporter] | None, optional): List of reporter instances.
        tools (AgentToolbox | None, optional): Not supported; use `act_tools`.
        retry (Retry | None, optional): Retry instance for failed actions.
        act_tools (list[Tool] | None, optional): Additional tools for `act()`.
        android_device_sn (str | None, optional): Android device serial number
            to select on open.

    Example:
        ```python
        from askui import MultiDeviceAgent

        with MultiDeviceAgent(android_device_sn="emulator-5554") as agent:
            agent.computer.click("Start")
            agent.android.tap("OK")
            agent.act("Fill the form on the phone and submit from the desktop")
        ```
    """

    def __init__(
        self,
        desktop_display: Annotated[int, Field(ge=1)] = 1,
        android_device_sn: str | int = 0,
        reporters: list[Reporter] | None = None,
        retry: Retry | None = None,
        act_tools: list[Tool] | None = None,
        settings: AgentSettings | None = None,
    ) -> None:
        reporter = CompositeReporter(reporters=reporters)

        # Initialize the base agent
        super().__init__(
            reporter=reporter,
            retry=retry,
            settings=settings,
        )

        # Initialize the computer agent
        self._computer_agent = ComputerAgent(
            display=desktop_display,
            reporters=[reporter],
            settings=settings,
        )

        # Initialize the Android agent
        self._android_agent = AndroidAgent(
            device=android_device_sn,
            reporters=[reporter],
            settings=settings,
        )

        # Combine the tool collections of the computer and Android agents
        self.act_tool_collection = (
            self._computer_agent.act_tool_collection
            + self._android_agent.act_tool_collection
        )

        self.act_tool_collection.append_tool(*(act_tools or []))

        self.act_settings.messages.system = create_multidevice_agent_prompt()

    @property
    def computer(self) -> ComputerAgent:
        """The composed computer agent."""
        return self._computer_agent

    @property
    def android(self) -> AndroidAgent:
        """The composed Android agent."""
        return self._android_agent

    def close(self) -> None:
        self._computer_agent.act_agent_os_facade.disconnect()
        self._android_agent.act_agent_os_facade.disconnect()
        super().close()

    def open(self) -> None:
        self._computer_agent.open()
        self._android_agent.open()
        super().open()

    # Get and locate functions must be overridden and throw please use
    #   .computer_agent and .android_agent instead.
