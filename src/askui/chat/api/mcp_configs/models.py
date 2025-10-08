"""MCP Config database model."""

from askui.chat.api.db.base import Base
from askui.chat.api.db.types import McpConfigId
from askui.chat.api.mcp_configs.schemas import McpConfig
from sqlalchemy import JSON, Column, DateTime, String


class McpConfigModel(Base):
    """MCP Config database model."""

    __tablename__ = "mcp_configs"
    id = Column(McpConfigId, primary_key=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    name = Column(String, nullable=False)
    mcp_server = Column(JSON, nullable=False)

    def to_pydantic(self) -> McpConfig:
        """Convert to Pydantic model."""
        data = {
            "id": self.id,  # Prefix is handled by the specialized type
            "workspace_id": self.workspace_id,
            "created_at": self.created_at,
            "name": self.name,
            "mcp_server": self.mcp_server,
        }
        return McpConfig.model_validate(data)

    @classmethod
    def from_pydantic(cls, mcp_config: McpConfig) -> "McpConfigModel":
        """Create from Pydantic model."""
        return cls(
            id=mcp_config.id,
            workspace_id=str(mcp_config.workspace_id)
            if mcp_config.workspace_id
            else None,
            created_at=mcp_config.created_at,
            name=mcp_config.name,
            mcp_server=mcp_config.mcp_server.model_dump(),
        )
