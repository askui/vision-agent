from pathlib import Path

from fastmcp.mcp_config import MCPConfig

from askui.chat.api.mcp_configs.models import (
    McpConfig,
    McpConfigCreateParams,
    McpConfigId,
    McpConfigModifyParams,
)
from askui.chat.api.mcp_configs.seeds import SEEDS
from askui.chat.api.models import WorkspaceId
from askui.chat.api.utils import build_workspace_filter_fn
from askui.utils.api_utils import (
    LIST_LIMIT_MAX,
    ConflictError,
    ForbiddenError,
    LimitReachedError,
    ListQuery,
    ListResponse,
    NotFoundError,
    list_resources,
)


class McpConfigService:
    """Service for managing McpConfig resources with filesystem persistence."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._mcp_configs_dir = base_dir / "mcp_configs"

    def _get_mcp_config_path(
        self, mcp_config_id: McpConfigId, new: bool = False
    ) -> Path:
        mcp_config_path = self._mcp_configs_dir / f"{mcp_config_id}.json"
        exists = mcp_config_path.exists()
        if new and exists:
            error_msg = f"MCP configuration {mcp_config_id} already exists"
            raise ConflictError(error_msg)
        if not new and not exists:
            error_msg = f"MCP configuration {mcp_config_id} not found"
            raise NotFoundError(error_msg)
        return mcp_config_path

    def list_(
        self, workspace_id: WorkspaceId | None, query: ListQuery
    ) -> ListResponse[McpConfig]:
        return list_resources(
            self._mcp_configs_dir,
            query,
            McpConfig,
            filter_fn=build_workspace_filter_fn(workspace_id, McpConfig),
        )

    def retrieve(
        self, workspace_id: WorkspaceId | None, mcp_config_id: McpConfigId
    ) -> McpConfig:
        try:
            mcp_config_path = self._get_mcp_config_path(mcp_config_id)
            mcp_config = McpConfig.model_validate_json(mcp_config_path.read_text())
            if not (
                mcp_config.workspace_id is None
                or mcp_config.workspace_id == workspace_id
            ):
                error_msg = f"MCP configuration {mcp_config_id} not found"
                raise NotFoundError(error_msg)
        except FileNotFoundError as e:
            error_msg = f"MCP configuration {mcp_config_id} not found"
            raise NotFoundError(error_msg) from e
        else:
            return mcp_config

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
        mcp_config = McpConfig.create(workspace_id, params)
        self._save(mcp_config, new=True)
        return mcp_config

    def modify(
        self,
        workspace_id: WorkspaceId | None,
        mcp_config_id: McpConfigId,
        params: McpConfigModifyParams,
    ) -> McpConfig:
        mcp_config = self.retrieve(workspace_id, mcp_config_id)
        modified = mcp_config.modify(params)
        self._save(modified)
        return modified

    def delete(
        self,
        workspace_id: WorkspaceId | None,
        mcp_config_id: McpConfigId,
        force: bool = False,
    ) -> None:
        try:
            mcp_config = self.retrieve(workspace_id, mcp_config_id)
            if mcp_config.workspace_id is None and not force:
                error_msg = (
                    f"Default MCP configuration {mcp_config_id} cannot be deleted"
                )
                raise ForbiddenError(error_msg)
            self._get_mcp_config_path(mcp_config_id).unlink()
        except FileNotFoundError as e:
            error_msg = f"MCP configuration {mcp_config_id} not found"
            raise NotFoundError(error_msg) from e

    def _save(self, mcp_config: McpConfig, new: bool = False) -> None:
        self._mcp_configs_dir.mkdir(parents=True, exist_ok=True)
        mcp_config_file = self._get_mcp_config_path(mcp_config.id, new=new)
        mcp_config_file.write_text(
            mcp_config.model_dump_json(
                exclude_unset=True, exclude_none=True, exclude_defaults=True
            ),
            encoding="utf-8",
        )

    def seed(self) -> None:
        """Seed the MCP configuration service with default MCP configurations."""
        while True:
            list_response = self.list_(
                None, ListQuery(limit=LIST_LIMIT_MAX, order="asc")
            )
            for mcp_config in list_response.data:
                self.delete(None, mcp_config.id, force=True)
            if not list_response.has_more:
                break
        for seed in SEEDS:
            try:
                self._save(seed, new=True)
            except ConflictError:  # noqa: PERF203
                self._save(seed)
