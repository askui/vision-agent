from pathlib import Path

from pydantic import ValidationError

from askui.utils.api_utils import (
    LIST_LIMIT_MAX,
    ConflictError,
    LimitReachedError,
    ListQuery,
    ListResponse,
    NotFoundError,
    list_resources,
)

from .models import McpConfig, McpConfigCreateParams, McpConfigId, McpConfigModifyParams


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

    def list_(self, query: ListQuery) -> ListResponse[McpConfig]:
        return list_resources(self._mcp_configs_dir, query, McpConfig)

    def retrieve(self, mcp_config_id: McpConfigId) -> McpConfig:
        try:
            mcp_config_path = self._get_mcp_config_path(mcp_config_id)
            return McpConfig.model_validate_json(mcp_config_path.read_text())
        except FileNotFoundError as e:
            error_msg = f"MCP configuration {mcp_config_id} not found"
            raise NotFoundError(error_msg) from e

    def _check_limit(self) -> None:
        limit = LIST_LIMIT_MAX
        list_result = self.list_(ListQuery(limit=limit))
        if len(list_result.data) >= limit:
            error_msg = (
                "MCP configuration limit reached. "
                f"You may only have {limit} MCP configurations. "
                "You can delete some MCP configurations to create new ones. "
            )
            raise LimitReachedError(error_msg)

    def create(self, params: McpConfigCreateParams) -> McpConfig:
        self._check_limit()
        mcp_config = McpConfig.create(params)
        self._save(mcp_config, new=True)
        return mcp_config

    def modify(
        self, mcp_config_id: McpConfigId, params: McpConfigModifyParams
    ) -> McpConfig:
        mcp_config = self.retrieve(mcp_config_id)
        modified = mcp_config.modify(params)
        self._save(modified)
        return modified

    def delete(self, mcp_config_id: McpConfigId) -> None:
        try:
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
