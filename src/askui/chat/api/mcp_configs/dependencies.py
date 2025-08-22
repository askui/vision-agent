from pathlib import Path

from fastapi import Depends

from askui.chat.api.dependencies import WorkspaceDirDep
from askui.chat.api.mcp_configs.service import McpConfigService


def get_mcp_config_service(workspace_dir: Path = WorkspaceDirDep) -> McpConfigService:
    """Get McpConfigService instance."""
    return McpConfigService(workspace_dir)


McpConfigServiceDep = Depends(get_mcp_config_service)
