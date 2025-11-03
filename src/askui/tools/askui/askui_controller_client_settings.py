from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AskUiControllerClientSettings(BaseSettings):
    """
    Settings for the AskUI Remote Device Controller client.
    """

    model_config = SettingsConfigDict(
        validate_by_name=True,
    )

    server_address: str = Field(
        default="localhost:23000",
        validation_alias="ASKUI_CONTROLLER_SERVER_ADDRESS",
        description="Address of the AskUI Remote Device Controller server.",
    )

    server_autostart: bool = Field(
        default=True,
        validation_alias="ASKUI_CONTOLLER_CLIENT_CONTROLLER_AUTOSTART",
        description="Whether to automatically start the AskUI Remote Device"
        "Controller server. Defaults to True.",
    )


__all__ = ["AskUiControllerClientSettings"]
