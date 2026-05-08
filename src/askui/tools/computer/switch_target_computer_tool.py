from askui.models.shared import ComputerBaseTool
from askui.tools.agent_os import AgentOs


class ComputerSwitchTargetComputerTool(ComputerBaseTool):
    def __init__(self, agent_os: AgentOs | None = None) -> None:
        super().__init__(
            name="switch_target_computer",
            description="""
                Switch the active target computer (controller server) by its
                session GUID. Future agent-os actions are routed to the newly
                selected target. Use `list_target_computers` to discover the
                available session GUIDs.
            """,
            input_schema={
                "type": "object",
                "properties": {
                    "session_guid": {
                        "type": "string",
                    },
                },
                "required": ["session_guid"],
            },
            agent_os=agent_os,
        )

    def __call__(self, session_guid: str) -> str:
        return repr(self.agent_os.switch_target_computer(session_guid))
