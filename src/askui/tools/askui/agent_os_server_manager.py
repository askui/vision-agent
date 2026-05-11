from askui.tools.askui.agent_os_server import (
    AgentOsServer,
    RemoteAgentOsServer,
)


class AgentOsServerManager:
    """
    Manages a collection of `AgentOsServer` instances and tracks the currently
    active one.

    Constraints:
        - At most one local Agent OS server (where `is_local` is `True`) may be
          registered at a time.
        - Session GUIDs are unique across registered servers.
        - Computer ids (`AgentOsServer.computer_id`) are unique across registered
          servers.
        - Remote server addresses must be unique across registered remote servers.

    The first server added becomes the active one by default. Use `switch` to change
    the active server.

    Args:
        agent_os_servers (list[AgentOsServer] | None, optional): Initial servers
            to register.
    """

    def __init__(
        self,
        agent_os_servers: list[AgentOsServer] | None = None,
    ) -> None:
        self._servers: list[AgentOsServer] = []
        self._active_session_guid: str | None = None
        if agent_os_servers:
            for server in agent_os_servers:
                self.add(server)

    def add(self, server: AgentOsServer) -> AgentOsServer:
        """
        Register an Agent OS server.

        Args:
            server (AgentOsServer): The server to register.

        Returns:
            AgentOsServer: The registered server.

        Raises:
            ValueError: If a local server is already registered, the same session
                GUID or computer id is already registered, or a remote server with
                the same address is already registered.
        """
        if server.is_local and any(s.is_local for s in self._servers):
            existing = next(s for s in self._servers if s.is_local)
            error_msg = (
                "Cannot register a second local Agent OS server. At most one local "
                f"server is supported. Existing local server: "
                f"{existing.description!r} (computer_id={existing.computer_id!r}). "
                "Remove it first via `remove(computer_id)`."
            )
            raise ValueError(error_msg)
        if any(s.session_guid == server.session_guid for s in self._servers):
            error_msg = (
                f"An Agent OS server with session_guid={server.session_guid} is "
                "already registered. Each server must have a unique session GUID."
            )
            raise ValueError(error_msg)
        if any(s.computer_id == server.computer_id for s in self._servers):
            error_msg = (
                f"An Agent OS server with computer_id={server.computer_id!r} is "
                "already registered. Each server must have a unique computer_id."
            )
            raise ValueError(error_msg)
        if not server.is_local and any(
            (not s.is_local) and s.address == server.address for s in self._servers
        ):
            error_msg = (
                f"A remote Agent OS server with address {server.address!r} is "
                "already registered. Each remote server must have a unique address."
            )
            raise ValueError(error_msg)
        self._servers.append(server)
        if self._active_session_guid is None:
            self._active_session_guid = server.session_guid
        return server

    def add_remote(
        self,
        address: str,
        description: str,
    ) -> RemoteAgentOsServer:
        """
        Convenience method to construct and register a remote Agent OS server.

        Args:
            address (str): gRPC address of the remote Agent OS server.
            description (str): Human-readable description.

        Returns:
            RemoteAgentOsServer: The newly registered server.
        """
        server = RemoteAgentOsServer(address=address, description=description)
        self.add(server)
        return server

    def reset(self) -> None:
        """Remove all registered servers."""
        self._servers = []
        self._active_session_guid = None

    def remove(self, computer_id: str) -> None:
        """
        Remove a registered server by its `computer_id`.

        Args:
            computer_id (str): The computer id of the server to remove.

        Raises:
            KeyError: If no server with the given computer id is registered.
        """
        index = self._index_of(computer_id)
        removed = self._servers[index]
        del self._servers[index]
        if self._active_session_guid == removed.session_guid:
            self._active_session_guid = (
                self._servers[0].session_guid if self._servers else None
            )

    def list(self) -> list[AgentOsServer]:
        """Return a list of all registered servers."""
        return list(self._servers)

    def get(self, computer_id: str) -> AgentOsServer:
        """
        Return the registered server with the given `computer_id`.

        Raises:
            KeyError: If no server with the given computer id is registered.
        """
        return self._servers[self._index_of(computer_id)]

    def switch(self, computer_id: str) -> AgentOsServer:
        """
        Set the active server by its `computer_id`.

        Args:
            computer_id (str): The computer id of the server to activate.

        Returns:
            AgentOsServer: The newly active server.

        Raises:
            KeyError: If no server with the given computer id is registered.
        """
        server = self.get(computer_id)
        self._active_session_guid = server.session_guid
        return server

    @property
    def active(self) -> AgentOsServer | None:
        """The currently active server, or `None` if no servers are registered."""
        if self._active_session_guid is None:
            return None
        for server in self._servers:
            if server.session_guid == self._active_session_guid:
                return server
        return None

    def __len__(self) -> int:
        return len(self._servers)

    def _index_of(self, computer_id: str) -> int:
        for i, server in enumerate(self._servers):
            if server.computer_id == computer_id:
                return i
        registered = ", ".join(repr(s.computer_id) for s in self._servers) or "none"
        error_msg = (
            f"No Agent OS server with computer_id={computer_id!r} is registered. "
            f"Registered computer ids: {registered}. Use "
            "`list_agent_os_servers()` to inspect the registered servers."
        )
        raise KeyError(error_msg)


__all__ = ["AgentOsServerManager"]
