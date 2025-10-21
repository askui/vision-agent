"""MCP configuration database model."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from askui.chat.api.db.orm.base import Base
from askui.chat.api.db.orm.types import UnixDatetime, create_prefixed_id_type
from askui.chat.api.mcp_configs.models import McpConfig

McpConfigId = create_prefixed_id_type("mcpcnf")


class McpConfigOrm(Base):
    """MCP configuration database model."""

    __tablename__ = "mcp_configs"

    id: Mapped[str] = mapped_column(McpConfigId, primary_key=True)
    workspace_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(UnixDatetime, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    mcp_server: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    @classmethod
    def from_model(cls, model: McpConfig) -> "McpConfigOrm":
        return cls(
            **model.model_dump(exclude={"object", "created_at"}),
            created_at=model.created_at,
        )

    def to_model(self) -> McpConfig:
        return McpConfig.model_validate(self, from_attributes=True)
