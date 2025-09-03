from fastmcp.mcp_config import RemoteMCPServer

from askui.chat.api.dependencies import get_settings
from askui.chat.api.mcp_configs.models import McpConfig
from askui.utils.datetime_utils import now

settings = get_settings()


ASKUI_CHAT_MCP = McpConfig(
    id="mcpcnf_68ac2c4edc4b2f27faa5a252",
    created_at=now(),
    name="AskUI Chat MCP",
    mcp_server=RemoteMCPServer(
        url=f"http://{settings.host}:{settings.port}/mcp/sse",
        transport="sse",
    ),
)


SEEDS = [ASKUI_CHAT_MCP]
