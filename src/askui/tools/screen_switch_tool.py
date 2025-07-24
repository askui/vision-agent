from askui.models.shared.tools import Tool
from askui.tools.agent_os import AgentOs, DisplayInformation


class ScreenSwitchTool(Tool):
    """
    Tool to change the screen.
    """

    def __init__(self, agent_os: AgentOs) -> None:
        # We need to determine the number of displays available to provide context to the agent
        # indicating that screen switching can only be done this number of times.
        displays: list[DisplayInformation] = agent_os.get_display_information().displays

        super().__init__(
            name="screen_switch",
            description=f"""
            This tool is useful for switching between multiple displays to find information not present on the current active screen.
            If more than one display is available, this tool cycles through them.
            Number of displays available: {len(displays)}.
            """,
        )
        self._agent_os: AgentOs = agent_os
        self._displays: list[DisplayInformation] = displays

    def __call__(self) -> None:
        """
        Cycles to the next display if there are multiple displays.
        This tool is useful to switch between multiple displays if some information is not found on the current display.
        """
        if len(self._displays) <= 1:
            return

        active_display_id: int = self._agent_os.get_active_display()

        current_display_index: int = next(
            i for i, d in enumerate(self._displays) if d.display_id == active_display_id
        )
        # if current_index is the last index, wrap around to the first index
        next_index: int = (current_display_index + 1) % len(self._displays)

        self._agent_os.set_display(self._displays[next_index].display_id)
