from unittest.mock import MagicMock

import pytest

from askui.tools.agent_os import AgentOs
from askui.tools.askui.agent_os_server import RemoteAgentOsServer
from askui.tools.computer import (
    ComputerGetActiveAgentOsServerTool,
    ComputerListAgentOsServersTool,
    ComputerSwitchAgentOsServerTool,
)


@pytest.fixture
def fake_agent_os() -> MagicMock:
    """A MagicMock that passes `isinstance(x, AgentOs)` checks."""
    return MagicMock(spec=AgentOs)


class TestComputerListAgentOsServersTool:
    def test_tool_name(self, fake_agent_os: MagicMock) -> None:
        tool = ComputerListAgentOsServersTool(agent_os=fake_agent_os)
        assert tool.base_name == "list_agent_os_servers"

    def test_returns_comma_separated_repr_of_servers(
        self, fake_agent_os: MagicMock
    ) -> None:
        a = RemoteAgentOsServer(
            address="1.1.1.1:23000", description="a", computer_id="a"
        )
        b = RemoteAgentOsServer(
            address="2.2.2.2:23000", description="b", computer_id="b"
        )
        fake_agent_os.list_agent_os_servers.return_value = [a, b]
        tool = ComputerListAgentOsServersTool(agent_os=fake_agent_os)
        out = tool()
        assert out == f"{a!r},{b!r}"

    def test_empty_list_yields_empty_string(self, fake_agent_os: MagicMock) -> None:
        fake_agent_os.list_agent_os_servers.return_value = []
        tool = ComputerListAgentOsServersTool(agent_os=fake_agent_os)
        assert tool() == ""


class TestComputerSwitchAgentOsServerTool:
    def test_tool_name(self, fake_agent_os: MagicMock) -> None:
        tool = ComputerSwitchAgentOsServerTool(agent_os=fake_agent_os)
        assert tool.base_name == "switch_agent_os_server"

    def test_input_schema_requires_computer_id(self, fake_agent_os: MagicMock) -> None:
        tool = ComputerSwitchAgentOsServerTool(agent_os=fake_agent_os)
        schema = tool.input_schema
        assert "computer_id" in schema["properties"]
        assert schema["required"] == ["computer_id"]

    def test_call_delegates_to_switch_agent_os_server(
        self, fake_agent_os: MagicMock
    ) -> None:
        switched = RemoteAgentOsServer(
            address="1.1.1.1:23000", description="new", computer_id="new"
        )
        fake_agent_os.switch_agent_os_server.return_value = switched
        tool = ComputerSwitchAgentOsServerTool(agent_os=fake_agent_os)
        out = tool(computer_id="new")
        fake_agent_os.switch_agent_os_server.assert_called_once_with("new")
        assert out == repr(switched)


class TestComputerGetActiveAgentOsServerTool:
    def test_tool_name(self, fake_agent_os: MagicMock) -> None:
        tool = ComputerGetActiveAgentOsServerTool(agent_os=fake_agent_os)
        assert tool.base_name == "get_active_agent_os_server"

    def test_is_not_cacheable(self, fake_agent_os: MagicMock) -> None:
        tool = ComputerGetActiveAgentOsServerTool(agent_os=fake_agent_os)
        assert tool.is_cacheable is False

    def test_call_returns_active_server_repr(self, fake_agent_os: MagicMock) -> None:
        active = RemoteAgentOsServer(
            address="1.1.1.1:23000", description="a", computer_id="a"
        )
        fake_agent_os.get_active_agent_os_server.return_value = active
        tool = ComputerGetActiveAgentOsServerTool(agent_os=fake_agent_os)
        out = tool()
        fake_agent_os.get_active_agent_os_server.assert_called_once_with()
        assert out == repr(active)
