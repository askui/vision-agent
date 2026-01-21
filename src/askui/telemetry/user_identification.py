import base64
import logging
import os
import types
from functools import cached_property
from typing import Type, cast

import httpx
from pydantic import BaseModel, Field, HttpUrl, SecretStr
from typing_extensions import Self

logger = logging.getLogger(__name__)


def get_askui_token_from_env() -> SecretStr | None:
    askui_token = os.environ.get("ASKUI_TOKEN")
    if not askui_token:
        return None
    return SecretStr(askui_token)


class UserIdentificationSettings(BaseModel):
    """Settings for user identification"""

    api_url: HttpUrl = HttpUrl("https://workspaces.askui.com/api/v1")
    # retrieving directly through environment variable to circumvent pydantic-settings
    # env_prefix
    askui_token: SecretStr | None = Field(default=get_askui_token_from_env())
    askui_workspace_id: str | None = Field(default=os.environ.get("ASKUI_WORKSPACE_ID"))
    disable_ssl_verification: bool = Field(
        default=(os.environ.get("ASKUI_DISABLE_SSL_VERIFICATION", "False") == "True"),
        description="Whether to disable SSL verification for the AskUI Workspaces API.",
    )

    @cached_property
    def askui_token_encoded(self) -> str | None:
        if not self.askui_token:
            return None
        return base64.b64encode(self.askui_token.get_secret_value().encode()).decode()


class UserIdentification:
    def __init__(self, settings: UserIdentificationSettings):
        self._settings = settings
        self._enabled = self._settings.askui_token and self._settings.askui_workspace_id
        if not self._enabled:
            logger.debug(
                "User identification disabled. Set the `ASKUI_TOKEN` and "
                "`ASKUI_WORKSPACE_ID` environment variables to allow user to be "
                "identified."
            )
            return

        self._client = httpx.Client(
            timeout=30.0,
            verify=not self._settings.disable_ssl_verification,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        self._client.close()

    def get_user_id(self) -> str | None:
        if not self._enabled:
            return None

        try:
            response = self._client.get(
                f"{self._settings.api_url}/workspace-memberships",
                params={
                    "workspace_id": self._settings.askui_workspace_id,
                    "expand": "user",
                },
                headers={
                    "Authorization": f"Basic {self._settings.askui_token_encoded}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            return cast(
                "str | None",
                response.json().get("data", [{}])[0].get("user", {}).get("id"),
            )
        except httpx.HTTPError as e:
            logger.debug("Failed to identify user", extra={"error": str(e)})
        except Exception as e:  # noqa: BLE001 - We want to catch all other exceptions here
            logger.debug(
                "Unexpected error while identifying user",
                extra={"error": str(e)},
            )

        return None
