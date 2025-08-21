from pathlib import Path

from pydantic import ValidationError

from askui.utils.api_utils import (
    LIST_LIMIT_MAX,
    ConflictError,
    LimitReachedError,
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

    def find(self, query: ListQuery) -> ListResponse[McpConfig]:
        """List all available MCP configs.

        Args:
            query (ListQuery): Query parameters for listing MCP configs

        Returns:
            ListResponse[McpConfig]: ListResponse containing MCP configs sorted by
                creation date
        """
        if not self._mcp_configs_dir.exists():
            return ListResponse(data=[])

        mcp_config_files = list(self._mcp_configs_dir.glob("*.json"))
        mcp_configs: list[McpConfig] = []
        for f in mcp_config_files:
            with f.open("r", encoding="utf-8") as file:
                mcp_configs.append(McpConfig.model_validate_json(file.read()))

        # Sort by creation date
        mcp_configs = sorted(
            mcp_configs, key=lambda m: m.created_at, reverse=(query.order == "desc")
        )

        # Apply before/after filters
        if query.after:
            mcp_configs = [m for m in mcp_configs if m.id > query.after]
        if query.before:
            mcp_configs = [m for m in mcp_configs if m.id < query.before]

        # Apply limit
        mcp_configs = mcp_configs[: query.limit]

        return ListResponse(
            data=mcp_configs,
            first_id=mcp_configs[0].id if mcp_configs else None,
            last_id=mcp_configs[-1].id if mcp_configs else None,
            has_more=len(mcp_config_files) > query.limit,
        )

    def find_one(self, mcp_config_id: McpConfigId) -> McpConfig:
        """Retrieve an MCP config by ID.

        Args:
            mcp_config_id: ID of MCP config to retrieve

        Returns:
            McpConfig object

        Raises:
            FileNotFoundError: If MCP config doesn't exist
        """
        mcp_config_file = self._mcp_configs_dir / f"{mcp_config_id}.json"
        if not mcp_config_file.exists():
            error_msg = f"MCP config {mcp_config_id} not found"
            raise FileNotFoundError(error_msg)

        with mcp_config_file.open("r", encoding="utf-8") as f:
            return McpConfig.model_validate_json(f.read())

    def _check_limit(self) -> None:
        limit = LIST_LIMIT_MAX
        list_result = self.find(ListQuery(limit=limit))
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
        mcp_config = self.find_one(mcp_config_id)
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
