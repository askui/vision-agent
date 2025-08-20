from typing import Literal

from fastmcp.mcp_config import RemoteMCPServer, StdioMCPServer
from pydantic import BaseModel, ConfigDict, Field

from askui.chat.api.models import McpConfigId
from askui.utils.datetime_utils import UnixDatetime, now
from askui.utils.id_utils import generate_time_ordered_id
from askui.utils.not_given import NOT_GIVEN, BaseModelWithNotGiven, NotGiven

McpServer = StdioMCPServer | RemoteMCPServer


class McpConfigCreateParams(BaseModel):
    """Parameters for creating an MCP configuration."""

    name: str
    mcp_server: McpServer


class McpConfigModifyParams(BaseModelWithNotGiven):
    """Parameters for modifying an MCP configuration."""

    name: str | NotGiven = NOT_GIVEN
    mcp_server: McpServer | NotGiven = Field(default=NOT_GIVEN)


class McpConfig(BaseModel):
    """An MCP configuration that can be stored and managed."""

    id: McpConfigId = Field(
        default_factory=lambda: generate_time_ordered_id("mcp_config")
    )
    created_at: UnixDatetime = Field(default_factory=now)
    name: str
    object: Literal["mcp_config"] = "mcp_config"
    mcp_server: McpServer = Field(description="The MCP server configuration")

    @classmethod
    def create(cls, params: McpConfigCreateParams) -> "McpConfig":
        return cls(
            id=generate_time_ordered_id("mcp_config"),
            created_at=now(),
            **params.model_dump(),
        )

    def modify(self, params: McpConfigModifyParams) -> "McpConfig":
        return McpConfig.model_validate(
            {
                **self.model_dump(),
                **params.model_dump(),
            }
        )
