from fastapi import Depends

from askui.chat.api.mcp_clients.manager import McpClientManagerManager
from askui.chat.api.mcp_configs.dependencies import McpConfigServiceDep
from askui.chat.api.mcp_configs.service import McpConfigService


def get_mcp_client_manager_manager(
    mcp_config_service: McpConfigService = McpConfigServiceDep,
) -> McpClientManagerManager:
    return McpClientManagerManager(mcp_config_service)


McpClientManagerManagerDep = Depends(get_mcp_client_manager_manager)
