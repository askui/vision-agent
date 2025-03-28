import base64
import os
from typing import Any
import httpx
from pydantic import BaseModel, Field, HttpUrl, SecretStr
from askui.logger import logger


def get_askui_token_from_env() -> SecretStr | None:
    askui_token = os.environ.get("ASKUI_TOKEN")
    if not askui_token:
        return None
    return SecretStr(askui_token)


class UserIdentificationSettings(BaseModel):
    """Settings for user identification"""

    enabled: bool = True
    api_url: HttpUrl = HttpUrl("https://workspaces.askui.com/api/v1")
    askui_token: SecretStr | None = Field(default=get_askui_token_from_env())

    @property
    def askui_token_encoded(self) -> str | None:
        if not self.askui_token:
            return None
        return base64.b64encode(self.askui_token.get_secret_value().encode()).decode()


class UserIdentification:
    def __init__(self, settings: UserIdentificationSettings):
        self._settings = settings
        self._client = httpx.Client(timeout=30.0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._client.close()

    def identify(self, anonymous_id: str, traits: dict[str, Any] | None = None) -> None:
        """Identify the user with the given anonymous ID and traits

        This method will send the anonymous ID and traits to the user identification service
        and associate the user that the askui access token belongs to with those.
        
        Args:
            anonymous_id: The anonymous ID of the user
            askui_access_token: The access token of the user
            traits: The traits of the user
        """
        logger.debug(f"ASKUI_TOKEN: {self._settings.askui_token and self._settings.askui_token.get_secret_value()}")
        if not self._settings.enabled or not self._settings.askui_token:
            return

        try:
            response = self._client.post(
                f"{self._settings.api_url}/analytics/identify",
                json={
                    "anonymousId": anonymous_id,
                    "traits": traits or {}
                },
                headers={
                    "Authorization": f"Basic {self._settings.askui_token_encoded}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            logger.debug(f"Successfully identified user with anonymous ID {anonymous_id}")
        except httpx.HTTPError as e:
            logger.debug(f"Failed to identify user: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error while identifying user: {e}")
