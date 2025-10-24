from fastmcp.mcp_config import MCPConfig
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from askui.chat.api.db.queries import list_all
from askui.chat.api.mcp_configs.models import (
    McpConfig,
    McpConfigCreate,
    McpConfigId,
    McpConfigModify,
)
from askui.chat.api.mcp_configs.orms import McpConfigOrm
from askui.chat.api.models import WorkspaceId
from askui.utils.api_utils import (
    LIST_LIMIT_MAX,
    ForbiddenError,
    LimitReachedError,
    ListQuery,
    ListResponse,
    NotFoundError,
)


class McpConfigService:
    """Service for managing McpConfig resources with database persistence."""

    def __init__(self, session: Session, seeds: list[McpConfig]) -> None:
        self._session = session
        self._seeds = seeds

    def list_(
        self, workspace_id: WorkspaceId | None, query: ListQuery
    ) -> ListResponse[McpConfig]:
        q = self._session.query(McpConfigOrm).filter(
            or_(
                McpConfigOrm.workspace_id == workspace_id,
                McpConfigOrm.workspace_id.is_(None),
            ),
        )
        orms: list[McpConfigOrm]
        orms, has_more = list_all(q, query, McpConfigOrm.id)
        data = [orm.to_model() for orm in orms]
        return ListResponse(
            data=data,
            has_more=has_more,
            first_id=data[0].id if data else None,
            last_id=data[-1].id if data else None,
        )

    def _find_by_id(
        self, workspace_id: WorkspaceId | None, mcp_config_id: McpConfigId
    ) -> McpConfigOrm:
        mcp_config_orm: McpConfigOrm | None = (
            self._session.query(McpConfigOrm)
            .filter(
                McpConfigOrm.id == mcp_config_id,
                or_(
                    McpConfigOrm.workspace_id == workspace_id,
                    McpConfigOrm.workspace_id.is_(None),
                ),
            )
            .first()
        )
        if mcp_config_orm is None:
            error_msg = f"MCP configuration {mcp_config_id} not found"
            raise NotFoundError(error_msg)
        return mcp_config_orm

    def retrieve(
        self, workspace_id: WorkspaceId | None, mcp_config_id: McpConfigId
    ) -> McpConfig:
        mcp_config_model = self._find_by_id(workspace_id, mcp_config_id)
        return mcp_config_model.to_model()

    def retrieve_fast_mcp_config(
        self, workspace_id: WorkspaceId | None
    ) -> MCPConfig | None:
        list_response = self.list_(
            workspace_id=workspace_id,
            query=ListQuery(limit=LIST_LIMIT_MAX, order="asc"),
        )
        mcp_servers_dict = {
            mcp_config.name: mcp_config.mcp_server for mcp_config in list_response.data
        }
        return MCPConfig(mcpServers=mcp_servers_dict) if mcp_servers_dict else None

    def create(
        self, workspace_id: WorkspaceId | None, params: McpConfigCreate
    ) -> McpConfig:
        try:
            mcp_config = McpConfig.create(workspace_id, params)
            mcp_config_model = McpConfigOrm.from_model(mcp_config)
            self._session.add(mcp_config_model)
            self._session.commit()
        except IntegrityError as e:
            if "MCP configuration limit reached" in str(e):
                raise LimitReachedError(str(e)) from e
            raise
        else:
            return mcp_config

    def modify(
        self,
        workspace_id: WorkspaceId | None,
        mcp_config_id: McpConfigId,
        params: McpConfigModify,
        force: bool = False,
    ) -> McpConfig:
        mcp_config_model = self._find_by_id(workspace_id, mcp_config_id)
        if mcp_config_model.workspace_id is None and not force:
            error_msg = f"Default MCP configuration {mcp_config_id} cannot be modified"
            raise ForbiddenError(error_msg)
        mcp_config_model.update(params.model_dump())
        self._session.commit()
        self._session.refresh(mcp_config_model)
        return mcp_config_model.to_model()

    def delete(
        self,
        workspace_id: WorkspaceId | None,
        mcp_config_id: McpConfigId,
        force: bool = False,
    ) -> None:
        # Use a single query to find and delete atomically
        mcp_config_model = (
            self._session.query(McpConfigOrm)
            .filter(
                McpConfigOrm.id == mcp_config_id,
                or_(
                    McpConfigOrm.workspace_id == workspace_id,
                    McpConfigOrm.workspace_id.is_(None),
                ),
            )
            .first()
        )

        if mcp_config_model is None:
            error_msg = f"MCP configuration {mcp_config_id} not found"
            raise NotFoundError(error_msg)

        if mcp_config_model.workspace_id is None and not force:
            error_msg = f"Default MCP configuration {mcp_config_id} cannot be deleted"
            raise ForbiddenError(error_msg)

        self._session.delete(mcp_config_model)
        self._session.commit()

    def seed(self) -> None:
        """Seed the MCP configuration service with default MCP configurations."""
        for seed in self._seeds:
            self._session.query(McpConfigOrm).filter(
                McpConfigOrm.id == seed.id
            ).delete()
            self._session.add(McpConfigOrm.from_model(seed))
            self._session.commit()
