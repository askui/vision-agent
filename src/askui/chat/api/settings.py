from pathlib import Path

from fastmcp.mcp_config import RemoteMCPServer, StdioMCPServer
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from askui.chat.api.mcp_configs.models import McpConfig
from askui.utils.datetime_utils import now


def _get_default_mcp_configs(chat_api_host: str, chat_api_port: int) -> list[McpConfig]:
    return [
        McpConfig(
            id="mcpcnf_68ac2c4edc4b2f27faa5a252",
            created_at=now(),
            name="askui_chat",
            mcp_server=RemoteMCPServer(
                url=f"http://{chat_api_host}:{chat_api_port}/mcp/sse",
                transport="sse",
            ),
        ),
        McpConfig(
            id="mcpcnf_68ac2c4edc4b2f27faa5a251",
            created_at=now(),
            name="playwright",
            mcp_server=StdioMCPServer(
                command="npx",
                args=[
                    "@playwright/mcp@latest",
                    "--isolated",
                ],
            ),
        ),
    ]


class Settings(BaseSettings):
    """Settings for the chat API."""

    model_config = SettingsConfigDict(
        env_prefix="ASKUI__CHAT_API__", env_nested_delimiter="__"
    )

    data_dir: Path = Field(
        default_factory=lambda: Path.cwd() / "chat",
        description="Base directory for storing chat data",
    )
    host: str = Field(
        default="127.0.0.1",
        description="Host for the chat API",
    )
    log_level: str | int = Field(
        default="info",
        description="Log level for the chat API",
    )
    port: int = Field(
        default=9261,
        description="Port for the chat API",
        ge=1024,
        le=65535,
    )
    mcp_configs: list[McpConfig] = Field(
        default_factory=lambda data: _get_default_mcp_configs(
            data["host"], data["port"]
        ),
        description=(
            "Global MCP configurations used to "
            "connect to MCP servers shared across all workspaces."
        ),
    )
