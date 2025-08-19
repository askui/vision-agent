from fastmcp.client.transports import StdioTransport
from fastmcp.mcp_config import StdioMCPServer as FastMCPStdioMCPServer


class StdioMCPServer(FastMCPStdioMCPServer):
    keep_alive: bool = False

    def to_transport(self) -> StdioTransport:
        from fastmcp.client.transports import StdioTransport

        return StdioTransport(
            command=self.command,
            args=self.args,
            env=self.env,
            cwd=self.cwd,
            keep_alive=self.keep_alive,
        )
