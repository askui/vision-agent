from askui.models.shared import ComputerBaseTool
from askui.tools.computer_agent_os_facade import ComputerAgentOsFacade


class ComputerListDisplaysTool(ComputerBaseTool):
    def __init__(self, agent_os: ComputerAgentOsFacade | None = None) -> None:
        super().__init__(
            name="computer_list_displays",
            description="""
                List all the available displays on the computer.
            """,
            agent_os=agent_os,
        )

    def __call__(self) -> str:
        return self.agent_os.list_displays().model_dump_json(
            exclude={"data": {"__all__": {"size"}}},
        )
