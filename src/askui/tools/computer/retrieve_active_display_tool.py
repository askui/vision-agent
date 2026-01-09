from askui.models.shared import ComputerBaseTool
from askui.tools.computer_agent_os_facade import ComputerAgentOsFacade


class ComputerRetrieveActiveDisplayTool(ComputerBaseTool):
    def __init__(self, agent_os: ComputerAgentOsFacade | None = None) -> None:
        super().__init__(
            name="computer_retrieve_active_display",
            description="""
                Retrieve the currently active display on the computer.
                The display is used to take screenshots and perform actions.
            """,
            agent_os=agent_os,
        )

    def __call__(self) -> str:
        return str(
            self.agent_os.retrieve_active_display().model_dump_json(exclude={"size"})
        )
