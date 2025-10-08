from pathlib import Path
from typing import Callable

from askui.chat.api.db.query_builder import QueryBuilder
from askui.chat.api.mcp_configs.models import McpConfigModel
from askui.chat.api.mcp_configs.schemas import (
    McpConfig,
    McpConfigCreateParams,
    McpConfigId,
    McpConfigModifyParams,
)
from askui.chat.api.models import WorkspaceId
from askui.utils.api_utils import (
    LIST_LIMIT_MAX,
    ForbiddenError,
    LimitReachedError,
    ListQuery,
    ListResponse,
    NotFoundError,
)
from fastmcp.mcp_config import MCPConfig
from sqlalchemy.orm import Session


class McpConfigService:
    """Service for managing McpConfig resources with SQLAlchemy persistence."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        base_dir: Path,
        seeds: list[McpConfig],
    ) -> None:
        self._session_factory = session_factory
        self._base_dir = base_dir
        self._seeds = seeds

    def _to_pydantic(self, db_model: McpConfigModel) -> McpConfig:
        """Convert SQLAlchemy model to Pydantic model."""
        return db_model.to_pydantic()

    def list_(
        self, workspace_id: WorkspaceId | None, query: ListQuery
    ) -> ListResponse[McpConfig]:
        with self._session_factory() as session:
            q = session.query(McpConfigModel)

            # Filter by workspace
            if workspace_id is not None:
                q = q.filter(McpConfigModel.workspace_id == str(workspace_id))
            else:
                q = q.filter(McpConfigModel.workspace_id.is_(None))

            # Apply list query parameters
            q = QueryBuilder.apply_list_query(
                q, McpConfigModel, query, McpConfigModel.created_at, McpConfigModel.id
            )

            # Apply limit
            limit = query.limit or 20
            q = q.limit(limit + 1)  # +1 to check if there are more

            results = q.all()
            return QueryBuilder.build_list_response(results, limit, self._to_pydantic)

    def retrieve(
        self, workspace_id: WorkspaceId | None, mcp_config_id: McpConfigId
    ) -> McpConfig:
        with self._session_factory() as session:
            db_config = (
                session.query(McpConfigModel)
                .filter(McpConfigModel.id == mcp_config_id)
                .first()
            )
            if not db_config:
                error_msg = f"MCP configuration {mcp_config_id} not found"
                raise NotFoundError(error_msg)

            # Check workspace access
            if not (
                db_config.workspace_id is None
                or db_config.workspace_id == str(workspace_id)
            ):
                error_msg = f"MCP configuration {mcp_config_id} not found"
                raise NotFoundError(error_msg)

            return self._to_pydantic(db_config)

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

    def _check_limit(self, workspace_id: WorkspaceId | None) -> None:
        limit = LIST_LIMIT_MAX
        list_result = self.list_(workspace_id, ListQuery(limit=limit))
        if len(list_result.data) >= limit:
            error_msg = (
                "MCP configuration limit reached. "
                f"You may only have {limit} MCP configurations. "
                "You can delete some MCP configurations to create new ones. "
            )
            raise LimitReachedError(error_msg)

    def create(
        self, workspace_id: WorkspaceId, params: McpConfigCreateParams
    ) -> McpConfig:
        self._check_limit(workspace_id)
        with self._session_factory() as session:
            db_config = McpConfigModel.from_create_params(params, workspace_id)
            session.add(db_config)
            session.commit()
            session.refresh(db_config)
            return self._to_pydantic(db_config)

    def modify(
        self,
        workspace_id: WorkspaceId | None,
        mcp_config_id: McpConfigId,
        params: McpConfigModifyParams,
    ) -> McpConfig:
        with self._session_factory() as session:
            db_config = (
                session.query(McpConfigModel)
                .filter(McpConfigModel.id == mcp_config_id)
                .first()
            )
            if not db_config:
                error_msg = f"MCP configuration {mcp_config_id} not found"
                raise NotFoundError(error_msg)

            # Check workspace access
            if not (
                db_config.workspace_id is None
                or db_config.workspace_id == str(workspace_id)
            ):
                error_msg = f"MCP configuration {mcp_config_id} not found"
                raise NotFoundError(error_msg)

            if db_config.workspace_id is None:
                error_msg = (
                    f"Default MCP configuration {mcp_config_id} cannot be modified"
                )
                raise ForbiddenError(error_msg)

            # Update fields
            if params.name is not None:
                db_config.name = params.name
            if params.mcp_server is not None:
                db_config.mcp_server = params.mcp_server

            session.commit()
            session.refresh(db_config)
            return self._to_pydantic(db_config)

    def delete(
        self,
        workspace_id: WorkspaceId | None,
        mcp_config_id: McpConfigId,
        force: bool = False,
    ) -> None:
        with self._session_factory() as session:
            db_config = (
                session.query(McpConfigModel)
                .filter(McpConfigModel.id == mcp_config_id)
                .first()
            )
            if not db_config:
                error_msg = f"MCP configuration {mcp_config_id} not found"
                if not force:
                    raise NotFoundError(error_msg)
                return

            # Check workspace access
            if not (
                db_config.workspace_id is None
                or db_config.workspace_id == str(workspace_id)
            ):
                error_msg = f"MCP configuration {mcp_config_id} not found"
                if not force:
                    raise NotFoundError(error_msg)
                return

            if db_config.workspace_id is None and not force:
                error_msg = (
                    f"Default MCP configuration {mcp_config_id} cannot be deleted"
                )
                raise ForbiddenError(error_msg)

            session.delete(db_config)
            session.commit()

    def seed(self) -> None:
        """Seed the MCP configuration service with default MCP configurations."""
        with self._session_factory() as session:
            for seed in self._seeds:
                # Check if config already exists
                existing_config = (
                    session.query(McpConfigModel)
                    .filter(McpConfigModel.id == seed.id)
                    .first()
                )
                if not existing_config:
                    db_config = McpConfigModel.from_pydantic(seed)
                    session.add(db_config)

            session.commit()
            session.commit()
