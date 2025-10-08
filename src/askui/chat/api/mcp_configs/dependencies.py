from askui.chat.api.dependencies import SessionFactoryDep, SettingsDep
from askui.chat.api.mcp_configs.service import McpConfigService
from askui.chat.api.settings import Settings
from fastapi import Depends


def get_mcp_config_service(
    session_factory=SessionFactoryDep, settings: Settings = SettingsDep
) -> McpConfigService:
    """Get McpConfigService instance."""
    return McpConfigService(session_factory, settings.data_dir, settings.mcp_configs)


McpConfigServiceDep = Depends(get_mcp_config_service)
