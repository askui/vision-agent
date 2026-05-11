"""
Unit tests for `AskUiControllerClient`'s multi-server registration / routing
logic. These tests intentionally avoid exercising the gRPC code path (which
needs a real controller binary). They cover the in-memory bookkeeping done by
the client and its `AgentOsServerManager`.
"""

import pytest

from askui.tools.askui.agent_os_server import (
    LocalAgentOsServer,
    RemoteAgentOsServer,
)
from askui.tools.askui.agent_os_server_manager import AgentOsServerManager
from askui.tools.askui.askui_controller import AskUiControllerClient
from askui.tools.askui.exceptions import AskUiControllerError


def _make_local(
    description: str = "local", computer_id: str | None = None, display: int = 1
) -> LocalAgentOsServer:
    return LocalAgentOsServer(
        description=description,
        discover_service=False,
        computer_id=computer_id,
        display=display,
    )


def _make_remote(
    address: str = "1.2.3.4:23000",
    description: str = "remote",
    computer_id: str | None = None,
    display: int = 1,
) -> RemoteAgentOsServer:
    return RemoteAgentOsServer(
        address=address,
        description=description,
        computer_id=computer_id,
        display=display,
    )


class TestConstruction:
    def test_default_registers_single_local_server(self) -> None:
        client = AskUiControllerClient()
        servers = client.agent_os_server_manager.list()
        assert len(servers) == 1
        assert isinstance(servers[0], LocalAgentOsServer)

    def test_default_propagates_display_to_default_local_server(self) -> None:
        client = AskUiControllerClient(display=3)
        active = client.agent_os_server_manager.active
        assert active is not None
        assert active.display == 3

    def test_accepts_explicit_servers(self) -> None:
        a = _make_local(computer_id="local")
        b = _make_remote(computer_id="remote")
        client = AskUiControllerClient(agent_os_servers=[a, b])
        assert client.agent_os_server_manager.list() == [a, b]
        assert client.agent_os_server_manager.active is a

    def test_explicit_servers_keep_their_own_display(self) -> None:
        """Constructor's display arg only seeds the auto-created default server."""
        a = _make_local(computer_id="local", display=2)
        b = _make_remote(computer_id="remote", display=3)
        client = AskUiControllerClient(display=5, agent_os_servers=[a, b])
        assert client.agent_os_server_manager.get("local").display == 2
        assert client.agent_os_server_manager.get("remote").display == 3

    def test_is_connected_false_before_connect(self) -> None:
        client = AskUiControllerClient(agent_os_servers=[_make_remote()])
        assert client.is_connected is False


class TestActiveServer:
    def test_get_active_returns_first_registered(self) -> None:
        a = _make_local(computer_id="a")
        b = _make_remote(computer_id="b")
        client = AskUiControllerClient(agent_os_servers=[a, b])
        assert client.get_active_agent_os_server() is a

    def test_get_active_with_empty_manager_raises(self) -> None:
        client = AskUiControllerClient(agent_os_servers=[_make_remote()])
        client.agent_os_server_manager.reset()
        with pytest.raises(AskUiControllerError, match="No active Agent OS server"):
            client.get_active_agent_os_server(report=False)


class TestSwitchAgentOsServer:
    def test_switch_changes_active_when_disconnected(self) -> None:
        a = _make_local(computer_id="a")
        b = _make_remote(computer_id="b")
        client = AskUiControllerClient(agent_os_servers=[a, b])
        client.switch_agent_os_server("b")
        assert client.agent_os_server_manager.active is b

    def test_switch_unknown_computer_id_raises_keyerror(self) -> None:
        client = AskUiControllerClient(agent_os_servers=[_make_local(computer_id="a")])
        with pytest.raises(KeyError, match="missing"):
            client.switch_agent_os_server("missing")

    def test_switch_returns_the_new_active_server(self) -> None:
        a = _make_local(computer_id="a")
        b = _make_remote(computer_id="b")
        client = AskUiControllerClient(agent_os_servers=[a, b])
        result = client.switch_agent_os_server("b")
        assert result is b

    def test_per_server_display_preserved_across_switch(self) -> None:
        a = _make_local(computer_id="a", display=1)
        b = _make_remote(computer_id="b", display=4)
        client = AskUiControllerClient(agent_os_servers=[a, b])
        client.switch_agent_os_server("b")
        assert client.agent_os_server_manager.active.display == 4
        client.switch_agent_os_server("a")
        assert client.agent_os_server_manager.active.display == 1


class TestListAndReset:
    def test_list_returns_registered_servers(self) -> None:
        a = _make_local(computer_id="a")
        b = _make_remote(computer_id="b")
        client = AskUiControllerClient(agent_os_servers=[a, b])
        assert client.list_agent_os_servers() == [a, b]

    def test_reset_with_no_args_leaves_manager_empty(self) -> None:
        client = AskUiControllerClient(agent_os_servers=[_make_remote(computer_id="r")])
        client.reset_agent_os_servers()
        assert client.list_agent_os_servers() == []

    def test_reset_with_new_list_replaces_registrations(self) -> None:
        client = AskUiControllerClient(agent_os_servers=[_make_remote(computer_id="old")])
        new_server = _make_remote(address="9.9.9.9:23000", computer_id="new")
        client.reset_agent_os_servers([new_server])
        assert client.list_agent_os_servers() == [new_server]
        assert client.agent_os_server_manager.active is new_server


class TestAddAgentOsServerWhileDisconnected:
    def test_add_remote_appends_without_connecting(self) -> None:
        client = AskUiControllerClient(agent_os_servers=[_make_local(computer_id="l")])
        added = client.add_remote_agent_os_server(
            address="2.2.2.2:23000", description="r"
        )
        assert added in client.list_agent_os_servers()
        assert client.is_connected is False

    def test_add_already_constructed_server(self) -> None:
        client = AskUiControllerClient(agent_os_servers=[_make_local(computer_id="l")])
        extra = _make_remote(address="2.2.2.2:23000", computer_id="r")
        result = client.add_agent_os_server(extra)
        assert result is extra
        assert extra in client.list_agent_os_servers()


class TestTemporarySelect:
    def test_temporary_select_restores_previous_active(self) -> None:
        a = _make_local(computer_id="a")
        b = _make_remote(computer_id="b")
        client = AskUiControllerClient(agent_os_servers=[a, b])
        assert client.agent_os_server_manager.active is a
        with client.temporary_select("b"):
            assert client.agent_os_server_manager.active is b
        assert client.agent_os_server_manager.active is a

    def test_temporary_select_restores_previous_even_on_exception(self) -> None:
        a = _make_local(computer_id="a")
        b = _make_remote(computer_id="b")
        client = AskUiControllerClient(agent_os_servers=[a, b])
        with pytest.raises(RuntimeError, match="boom"), client.temporary_select("b"):
            assert client.agent_os_server_manager.active is b
            raise RuntimeError("boom")
        assert client.agent_os_server_manager.active is a

    def test_temporary_select_same_id_is_a_noop_around_yield(self) -> None:
        a = _make_local(computer_id="a")
        client = AskUiControllerClient(agent_os_servers=[a])
        with client.temporary_select("a"):
            assert client.agent_os_server_manager.active is a
        assert client.agent_os_server_manager.active is a


class TestUsesAgentOsServerManager:
    def test_underlying_manager_is_an_agent_os_server_manager(self) -> None:
        client = AskUiControllerClient(agent_os_servers=[_make_local(computer_id="l")])
        assert isinstance(client.agent_os_server_manager, AgentOsServerManager)
