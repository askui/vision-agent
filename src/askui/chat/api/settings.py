from pathlib import Path

from fastmcp.mcp_config import StdioMCPServer
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from askui.chat.api.mcp_configs.models import McpConfig, RemoteMCPServer
from askui.chat.api.telemetry.integrations.fastapi.settings import TelemetrySettings
from askui.chat.api.telemetry.logs.settings import LogFilter, LogSettings
from askui.utils.datetime_utils import now


class DbSettings(BaseModel):
    """Database configuration settings."""

    url: str = Field(
        default_factory=lambda: f"sqlite:///{(Path.cwd().absolute() / 'askui_chat.db').as_posix()}",
        description="Database URL for SQLAlchemy connection",
    )


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
        description="Base directory for chat data (used during migration)",
    )
    db: DbSettings = Field(default_factory=DbSettings)
    host: str = Field(
        default="127.0.0.1",
        description="Host for the chat API",
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
    model: str = Field(
        default="askui/claude-haiku-4-5-20251001",
        description="Default model to use for chat interactions",
    )
    allow_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:4200",
            "https://app.caesr.ai",
            "https://app-dev.caesr.ai",
            "https://hub.askui.com",
            "https://hub-dev.askui.com",
        ],
        description="CORS allowed origins for the chat API",
    )
    telemetry: TelemetrySettings = Field(
        default_factory=lambda: TelemetrySettings(
            log=LogSettings(
                filters=[
                    LogFilter(type="equals", key="path", value="/v1/health"),
                    LogFilter(type="equals", key="path", value="/v1/metrics"),
                    LogFilter(type="equals", key="method", value="OPTIONS"),
                ],
            ),
        ),
    )
