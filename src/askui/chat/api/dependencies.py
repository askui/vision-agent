import os
from typing import Annotated, Optional

from fastapi import Depends, Header
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID4

from askui.chat.api.settings import Settings


def get_settings() -> Settings:
    """Get ChatApiSettings instance."""
    return Settings()


SettingsDep = Depends(get_settings)


http_bearer = HTTPBearer(scheme_name="Bearer", auto_error=False)
api_key_header = APIKeyHeader(
    name="Authorization", auto_error=False, scheme_name="Basic"
)


def get_authorization(
    bearer_auth: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(http_bearer)
    ] = None,
    api_key_auth: Annotated[Optional[str], Depends(api_key_header)] = None,
) -> Optional[str]:
    if bearer_auth:
        return f"{bearer_auth.scheme} {bearer_auth.credentials}"
    if api_key_auth:
        return api_key_auth
    return None


def set_env_from_headers(
    authorization: Annotated[Optional[str], Depends(get_authorization)] = None,
    askui_workspace: Annotated[UUID4 | None, Header()] = None,
) -> None:
    """
    Set environment variables from Authorization and AskUI-Workspace headers.

    Args:
        authorization (str | None, optional): Authorization header.
            Defaults to `None`.
        askui_workspace (UUID4 | None, optional): Workspace ID from AskUI-Workspace header.
            Defaults to `None`.
    """
    if authorization:
        os.environ["ASKUI__AUTHORIZATION"] = authorization
    if askui_workspace:
        os.environ["ASKUI_WORKSPACE_ID"] = str(askui_workspace)


SetEnvFromHeadersDep = Depends(set_env_from_headers)
