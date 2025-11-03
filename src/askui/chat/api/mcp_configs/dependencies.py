from fastapi import Depends

from askui.chat.api.db.session import SessionDep
from askui.chat.api.dependencies import SettingsDep
from askui.chat.api.mcp_configs.service import McpConfigService
from askui.chat.api.settings import Settings


def get_mcp_config_service(
    session: SessionDep, settings: Settings = SettingsDep
) -> McpConfigService:
    """Get McpConfigService instance."""
    return McpConfigService(session, settings.mcp_configs)


McpConfigServiceDep = Depends(get_mcp_config_service)
