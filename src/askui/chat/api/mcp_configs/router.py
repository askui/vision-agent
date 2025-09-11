from typing import Annotated

from fastapi import APIRouter, Header, status

from askui.chat.api.dependencies import ListQueryDep
from askui.chat.api.mcp_configs.dependencies import McpConfigServiceDep
from askui.chat.api.mcp_configs.models import (
    McpConfig,
    McpConfigCreateParams,
    McpConfigModifyParams,
)
from askui.chat.api.mcp_configs.service import McpConfigService
from askui.chat.api.models import McpConfigId, WorkspaceId
from askui.utils.api_utils import ListQuery, ListResponse

router = APIRouter(prefix="/mcp-configs", tags=["mcp-configs"])


@router.get("", response_model_exclude_none=True)
def list_mcp_configs(
    askui_workspace: Annotated[WorkspaceId | None, Header()],
    query: ListQuery = ListQueryDep,
    mcp_config_service: McpConfigService = McpConfigServiceDep,
) -> ListResponse[McpConfig]:
    return mcp_config_service.list_(workspace_id=askui_workspace, query=query)


@router.post("", status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
def create_mcp_config(
    params: McpConfigCreateParams,
    askui_workspace: Annotated[WorkspaceId, Header()],
    mcp_config_service: McpConfigService = McpConfigServiceDep,
) -> McpConfig:
    """Create a new MCP configuration."""
    return mcp_config_service.create(workspace_id=askui_workspace, params=params)


@router.get("/{mcp_config_id}", response_model_exclude_none=True)
def retrieve_mcp_config(
    mcp_config_id: McpConfigId,
    askui_workspace: Annotated[WorkspaceId | None, Header()],
    mcp_config_service: McpConfigService = McpConfigServiceDep,
) -> McpConfig:
    """Get an MCP configuration by ID."""
    return mcp_config_service.retrieve(
        workspace_id=askui_workspace, mcp_config_id=mcp_config_id
    )


@router.post("/{mcp_config_id}", response_model_exclude_none=True)
def modify_mcp_config(
    mcp_config_id: McpConfigId,
    params: McpConfigModifyParams,
    askui_workspace: Annotated[WorkspaceId, Header()],
    mcp_config_service: McpConfigService = McpConfigServiceDep,
) -> McpConfig:
    """Update an MCP configuration."""
    return mcp_config_service.modify(
        workspace_id=askui_workspace, mcp_config_id=mcp_config_id, params=params
    )


@router.delete("/{mcp_config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mcp_config(
    mcp_config_id: McpConfigId,
    askui_workspace: Annotated[WorkspaceId | None, Header()],
    mcp_config_service: McpConfigService = McpConfigServiceDep,
) -> None:
    """Delete an MCP configuration."""
    mcp_config_service.delete(workspace_id=askui_workspace, mcp_config_id=mcp_config_id)
