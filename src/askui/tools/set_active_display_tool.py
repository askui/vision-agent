from askui.models.shared.tools import Tool
from askui.tools.agent_os import AgentOs


class SetActiveDisplayTool(Tool):
    def __init__(self, agent_os: AgentOs) -> None:
        super().__init__(
            name="set_active_display",
            description="""
                Set the display screen from which screenshots are taken and on which
                actions are performed.
            """,
            input_schema={
                "type": "object",
                "properties": {
                    "display_id": {
                        "type": "integer",
                    },
                },
                "required": ["display_id"],
            },
        )
        self._agent_os: AgentOs = agent_os

    def __call__(self, display_id: int) -> None:
        self._agent_os.set_display(display_id)
