from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AskUiControllerClientSettings(BaseSettings):
    """
    Settings for the AskUI Remote Device Controller client.
    """

    model_config = SettingsConfigDict(
        env_prefix="ASKUI_CONTOLLER_CLIENT_",
    )

    server_address: str = Field(
        default="localhost:23000",
        description="Address of the AskUI Remote Device Controller server.",
    )

    server_autostart: bool = Field(
        default=True,
        description="Whether to automatically start the AskUI Remote Device"
        "Controller server. Defaults to True.",
    )


__all__ = ["AskUiControllerClientSettings"]
