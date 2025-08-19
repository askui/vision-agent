from pathlib import Path

from pydantic import ValidationError

from askui.utils.api_utils import (
    ConflictError,
    ListQuery,
    ListResponse,
    NotFoundError,
    list_resource_paths,
)

from .models import McpConfig, McpConfigCreateParams, McpConfigId, McpConfigModifyParams


class McpConfigService:
    """
    Service for managing McpConfig resources with filesystem persistence.

    Args:
        base_dir (Path): Base directory for storing MCP configuration data.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._mcp_configs_dir = base_dir / "mcp_configs"
        self._mcp_configs_dir.mkdir(parents=True, exist_ok=True)

    def list_(
        self,
        query: ListQuery,
    ) -> ListResponse[McpConfig]:
        mcp_config_paths = list_resource_paths(self._mcp_configs_dir, query)
        mcp_configs: list[McpConfig] = []
        for f in mcp_config_paths:
            try:
                mcp_config = McpConfig.model_validate_json(f.read_text())
                mcp_configs.append(mcp_config)
            except ValidationError:  # noqa: PERF203
                continue
        has_more = len(mcp_configs) > query.limit
        mcp_configs = mcp_configs[: query.limit]
        return ListResponse(
            data=mcp_configs,
            first_id=mcp_configs[0].id if mcp_configs else None,
            last_id=mcp_configs[-1].id if mcp_configs else None,
            has_more=has_more,
        )

    def retrieve(self, mcp_config_id: McpConfigId) -> McpConfig:
        mcp_config_file = self._mcp_configs_dir / f"{mcp_config_id}.json"
        if not mcp_config_file.exists():
            error_msg = f"MCP configuration {mcp_config_id} not found"
            raise NotFoundError(error_msg)
        return McpConfig.model_validate_json(mcp_config_file.read_text())

    def create(self, params: McpConfigCreateParams) -> McpConfig:
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
        mcp_config_file = self._mcp_configs_dir / f"{mcp_config_id}.json"
        if not mcp_config_file.exists():
            error_msg = f"MCP configuration {mcp_config_id} not found"
            raise NotFoundError(error_msg)
        mcp_config_file.unlink()

    def _save(self, mcp_config: McpConfig, new: bool = False) -> None:
        """Save an MCP configuration to the file system."""
        self._mcp_configs_dir.mkdir(parents=True, exist_ok=True)
        mcp_config_file = self._mcp_configs_dir / f"{mcp_config.id}.json"
        if new and mcp_config_file.exists():
            error_msg = f"MCP configuration {mcp_config.id} already exists"
            raise ConflictError(error_msg)
        with mcp_config_file.open("w", encoding="utf-8") as f:
            f.write(
                mcp_config.model_dump_json(
                    exclude_unset=True, exclude_none=True, exclude_defaults=True
                )
            )
