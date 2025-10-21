from typing import Annotated, Any, Literal

from fastmcp.mcp_config import RemoteMCPServer as _RemoteMCPServer
from fastmcp.mcp_config import StdioMCPServer
from httpx import Auth
from pydantic import BaseModel, BeforeValidator, Field

from askui.chat.migrations.shared.models import UnixDatetimeV1, WorkspaceIdV1
from askui.chat.migrations.shared.utils import build_prefixer

McpConfigIdV1 = Annotated[
    str, Field(pattern=r"^mcpcnf_[a-z0-9]+$"), BeforeValidator(build_prefixer("mcpcnf"))
]


class RemoteMCPServerV1(_RemoteMCPServer):
    auth: Annotated[
        str | Literal["oauth"] | Auth | None,  # noqa: PYI051
        Field(
            description='Either a string representing a Bearer token or the literal "oauth" to use OAuth authentication.',
        ),
    ] = None


McpServerV1 = StdioMCPServer | RemoteMCPServerV1


class McpConfigV1(BaseModel):
    id: McpConfigIdV1
    object: Literal["mcp_config"] = "mcp_config"
    created_at: UnixDatetimeV1
    workspace_id: WorkspaceIdV1 | None = None
    name: str
    mcp_server: McpServerV1

    def to_db_dict(self) -> dict[str, Any]:
        return {
            **self.model_dump(exclude={"id", "object", "workspace_id"}),
            "id": self.id.removeprefix("mcpcnf_"),
            "workspace_id": str(self.workspace_id) if self.workspace_id else None,
        }
