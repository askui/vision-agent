from typing import Literal

from fastmcp.mcp_config import RemoteMCPServer, StdioMCPServer
from pydantic import BaseModel

from askui.chat.api.models import McpConfigId, WorkspaceId, WorkspaceResource
from askui.utils.datetime_utils import UnixDatetime, now
from askui.utils.id_utils import generate_time_ordered_id
from askui.utils.not_given import NOT_GIVEN, BaseModelWithNotGiven, NotGiven

McpServer = StdioMCPServer | RemoteMCPServer


class McpConfigBase(BaseModel):
    """Base MCP configuration model."""

    name: str
    mcp_server: McpServer


class McpConfigCreateParams(McpConfigBase):
    """Parameters for creating an MCP configuration."""


class McpConfigModifyParams(BaseModelWithNotGiven):
    """Parameters for modifying an MCP configuration."""

    name: str | NotGiven = NOT_GIVEN
    mcp_server: McpServer | NotGiven = NOT_GIVEN


class McpConfig(McpConfigBase, WorkspaceResource):
    """An MCP configuration that can be stored and managed."""

    id: McpConfigId
    object: Literal["mcp_config"] = "mcp_config"
    created_at: UnixDatetime

    @classmethod
    def create(
        cls, workspace_id: WorkspaceId, params: McpConfigCreateParams
    ) -> "McpConfig":
        return cls(
            id=generate_time_ordered_id("mcpcnf"),
            created_at=now(),
            workspace_id=workspace_id,
            **params.model_dump(),
        )

    def modify(self, params: McpConfigModifyParams) -> "McpConfig":
        return McpConfig.model_validate(
            {
                **self.model_dump(),
                **params.model_dump(),
            }
        )
