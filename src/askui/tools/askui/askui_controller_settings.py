import pathlib
from functools import cached_property

from askui_agent_os import AgentOS
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RemoteDeviceController(BaseModel):
    askui_remote_device_controller: pathlib.Path = Field(
        alias="AskUIRemoteDeviceController"
    )


class Executables(BaseModel):
    executables: RemoteDeviceController = Field(alias="Executables")


class InstalledPackages(BaseModel):
    remote_device_controller_uuid: Executables = Field(
        alias="{aed1b543-e856-43ad-b1bc-19365d35c33e}"
    )


class AskUiComponentRegistry(BaseModel):
    definition_version: int = Field(alias="DefinitionVersion")
    installed_packages: InstalledPackages = Field(alias="InstalledPackages")


class AskUiControllerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ASKUI_",
    )

    controller_args: str | None = Field(
        default="--showOverlay false",
        description=(
            "Arguments to pass to the AskUI Remote Device Controller executable. "
            "Supported arguments: --showOverlay [true|false], --debugDraw [true|false],"
            "--configFile <AbsolutePathToConfigFile>.\n"
            "Examples:\n"
            "  --showOverlay false --configFile /path/to/config.json\n"
            "  --showOverlay false\n"
            "Default: --showOverlay false"
        ),
    )

    @field_validator("controller_args", mode="before")
    @classmethod
    def validate_controller_args(cls, value: str) -> str:
        """Ensure controller_args contains only supported flags and formats."""

        if not value:
            return value

        allowed_flags = ["--showOverlay", "--debugDraw", "--configFile"]

        args = value.split()
        for i, arg in enumerate(args):
            if arg.startswith("--") and arg not in allowed_flags:
                error_msg = f"Unsupported controller argument: {arg}"
                raise ValueError(error_msg)

            if arg in ("--showOverlay", "--debugDraw"):
                if i + 1 >= len(args) or args[i + 1] not in ("true", "false"):
                    error_msg = f"{arg} must be followed by 'true' or 'false'"
                    raise ValueError(error_msg)

            if arg == "--configFile":
                if i + 1 >= len(args):
                    error_msg = "--configFile must be followed by an absolute file path"
                    raise ValueError(error_msg)
                config_file_path = args[i + 1]
                if not pathlib.Path(config_file_path).is_file():
                    error_msg = f"Config file path '{config_file_path}' does not exist"
                    raise ValueError(error_msg)

        return value

    @cached_property
    def controller_path(self) -> pathlib.Path:
        return AgentOS.controller_path()


__all__ = ["AskUiControllerSettings"]
