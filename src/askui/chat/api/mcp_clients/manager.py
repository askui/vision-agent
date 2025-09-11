import types
from datetime import timedelta
from typing import Any, Type

import anyio
import mcp
from fastmcp import Client
from fastmcp.client.client import CallToolResult, ProgressHandler
from fastmcp.exceptions import ToolError
from fastmcp.mcp_config import MCPConfig

from askui.chat.api.mcp_configs.service import McpConfigService
from askui.chat.api.models import WorkspaceId

McpServerName = str


class McpServerConnectionError(Exception):
    """Exception raised when a MCP server connection fails."""

    def __init__(self, mcp_server_name: McpServerName, error: Exception):
        super().__init__(f"Failed to connect to MCP server: {mcp_server_name}: {error}")
        self.mcp_server_name = mcp_server_name
        self.error = error


class McpClientManager:
    def __init__(
        self, mcp_clients: dict[McpServerName, Client[Any]] | None = None
    ) -> None:
        self._mcp_clients = mcp_clients or {}
        self._tools: dict[McpServerName, list[mcp.types.Tool]] = {}

    @classmethod
    def from_config(cls, mcp_config: MCPConfig) -> "McpClientManager":
        mcp_clients: dict[McpServerName, Client[Any]] = {
            mcp_server_name: Client(mcp_server_config.to_transport())
            for mcp_server_name, mcp_server_config in mcp_config.mcpServers.items()
        }
        return cls(mcp_clients)

    async def connect(self) -> "McpClientManager":
        for mcp_server_name, mcp_client in self._mcp_clients.items():
            try:
                await mcp_client._connect()  # noqa: SLF001
            except Exception as e:  # noqa: PERF203
                raise McpServerConnectionError(mcp_server_name, e) from e
        return self

    async def disconnect(self, force: bool = False) -> None:
        for mcp_client in self._mcp_clients.values():
            if mcp_client.is_connected():
                await mcp_client._disconnect(force)  # noqa: SLF001

    async def list_tools(
        self,
    ) -> list[mcp.types.Tool]:
        tools: list[mcp.types.Tool] = []
        for mcp_server_name, mcp_client in self._mcp_clients.items():
            if mcp_server_name not in self._tools:
                self._tools[mcp_server_name] = await mcp_client.list_tools()
            tools.extend(self._tools[mcp_server_name])
        return tools

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        timeout: timedelta | float | None = None,  # noqa: ASYNC109
        progress_handler: ProgressHandler | None = None,
        raise_on_error: bool = True,
    ) -> CallToolResult:
        for mcp_server_name, tools in self._tools.items():  # Make lookup faster
            for tool in tools:
                if tool.name == name:
                    return await self._mcp_clients[mcp_server_name].call_tool(
                        name,
                        arguments,
                        timeout,
                        progress_handler,
                        raise_on_error,
                    )
        error_msg = f"Unknown tool: {name}"
        if raise_on_error:
            raise ToolError(error_msg)
        return CallToolResult(
            content=[mcp.types.TextContent(type="text", text=error_msg)],
            structured_content=None,
            data=None,
            is_error=True,
        )

    async def __aenter__(self) -> "McpClientManager":
        return await self.connect()

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        await self.disconnect()


McpClientManagerKey = str


class McpClientManagerManager:
    _mcp_client_managers: dict[McpClientManagerKey, McpClientManager | None] = {}
    _lock: anyio.Lock = anyio.Lock()

    def __init__(self, mcp_config_service: McpConfigService) -> None:
        self._mcp_config_service = mcp_config_service

    async def get_mcp_client_manager(
        self, workspace_id: WorkspaceId | None
    ) -> McpClientManager | None:
        key: McpClientManagerKey = (
            f"workspace_{workspace_id}" if workspace_id else "global"
        )
        if key in McpClientManagerManager._mcp_client_managers:
            return McpClientManagerManager._mcp_client_managers[key]

        fast_mcp_config = self._mcp_config_service.retrieve_fast_mcp_config(
            workspace_id
        )
        if not fast_mcp_config:
            McpClientManagerManager._mcp_client_managers[key] = None
            return None

        async with McpClientManagerManager._lock:
            if key not in McpClientManagerManager._mcp_client_managers:
                try:
                    mcp_client_manager = McpClientManager.from_config(fast_mcp_config)
                    McpClientManagerManager._mcp_client_managers[key] = (
                        mcp_client_manager
                    )
                    await mcp_client_manager.connect()
                except Exception:
                    if key in McpClientManagerManager._mcp_client_managers:
                        if (
                            _mcp_client_manager
                            := McpClientManagerManager._mcp_client_managers[key]
                        ):
                            await _mcp_client_manager.disconnect(force=True)
                        del McpClientManagerManager._mcp_client_managers[key]
                    raise
            return McpClientManagerManager._mcp_client_managers[key]

    async def disconnect_all(self, force: bool = False) -> None:
        async with McpClientManagerManager._lock:
            for (
                mcp_client_manager
            ) in McpClientManagerManager._mcp_client_managers.values():
                if mcp_client_manager:
                    await mcp_client_manager.disconnect(force)
