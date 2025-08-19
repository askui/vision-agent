from fastapi import APIRouter, HTTPException, status

from askui.chat.api.mcp_configs.dependencies import McpConfigServiceDep
from askui.chat.api.mcp_configs.models import (
    McpConfig,
    McpConfigCreateParams,
    McpConfigModifyParams,
)
from askui.chat.api.mcp_configs.service import McpConfigService
from askui.chat.api.models import ListQueryDep, McpConfigId
from askui.utils.api_utils import LimitReachedError, ListQuery, ListResponse

router = APIRouter(prefix="/mcp-configs", tags=["mcp-configs"])


@router.get("", response_model_exclude_none=True)
def list_mcp_configs(
    query: ListQuery = ListQueryDep,
    mcp_config_service: McpConfigService = McpConfigServiceDep,
) -> ListResponse[McpConfig]:
    """List all MCP configurations."""
    return mcp_config_service.list_(query=query)


@router.post("", status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
def create_mcp_config(
    params: McpConfigCreateParams,
    mcp_config_service: McpConfigService = McpConfigServiceDep,
) -> McpConfig:
    """Create a new MCP configuration."""
    try:
        return mcp_config_service.create(params)
    except LimitReachedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/{mcp_config_id}", response_model_exclude_none=True)
def retrieve_mcp_config(
    mcp_config_id: McpConfigId,
    mcp_config_service: McpConfigService = McpConfigServiceDep,
) -> McpConfig:
    """Get an MCP configuration by ID."""
    try:
        return mcp_config_service.retrieve(mcp_config_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{mcp_config_id}", response_model_exclude_none=True)
def modify_mcp_config(
    mcp_config_id: McpConfigId,
    params: McpConfigModifyParams,
    mcp_config_service: McpConfigService = McpConfigServiceDep,
) -> McpConfig:
    """Update an MCP configuration."""
    try:
        return mcp_config_service.modify(mcp_config_id, params)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{mcp_config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mcp_config(
    mcp_config_id: McpConfigId,
    mcp_config_service: McpConfigService = McpConfigServiceDep,
) -> None:
    """Delete an MCP configuration."""
    try:
        mcp_config_service.delete(mcp_config_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
