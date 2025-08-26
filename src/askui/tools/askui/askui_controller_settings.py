import pathlib
import sys
from functools import cached_property

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


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

    component_registry_file: pathlib.Path | None = None
    installation_directory: pathlib.Path | None = Field(
        None,
        deprecated="ASKUI_INSTALLATION_DIRECTORY has been deprecated in favor of "
        "ASKUI_COMPONENT_REGISTRY_FILE and ASKUI_CONTROLLER_PATH. You may be using an "
        "outdated AskUI Suite. If you think so, reinstall to upgrade the AskUI Suite "
        "(see https://docs.askui.com/01-tutorials/00-installation).",
    )
    controller_path_setting: pathlib.Path | None = Field(
        None,
        validation_alias="ASKUI_CONTROLLER_PATH",
        description="Path to the AskUI Remote Device Controller executable. Takes "
        "precedence over ASKUI_COMPONENT_REGISTRY_FILE and ASKUI_INSTALLATION_DIRECTORY"
        ".",
    )
    controller_args: str | None = Field(
        default="--showOverlay true",
        description=(
            "Arguments to pass to the AskUI Remote Device Controller executable. "
            "Supported arguments: --showOverlay [true|false], --debugDraw [true|false],"
            "--configFile <AbsolutePathToConfigFile>.\n"
            "Examples:\n"
            "  --showOverlay false --configFile /path/to/config.json\n"
            "  --showOverlay false\n"
            "Default: --showOverlay true"
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

    @model_validator(mode="after")
    def validate_either_component_registry_or_installation_directory_is_set(
        self,
    ) -> "Self":
        if (
            self.component_registry_file is None
            and self.installation_directory is None
            and self.controller_path_setting is None
        ):
            error_msg = (
                "Either ASKUI_COMPONENT_REGISTRY_FILE, ASKUI_INSTALLATION_DIRECTORY, "
                "or ASKUI_CONTROLLER_PATH environment variable must be set"
            )
            raise ValueError(error_msg)
        return self

    def _find_remote_device_controller_by_installation_directory(
        self,
    ) -> pathlib.Path | None:
        if self.installation_directory is None:
            return None

        return self._build_controller_path(self.installation_directory)

    def _build_controller_path(
        self, installation_directory: pathlib.Path
    ) -> pathlib.Path:
        match sys.platform:
            case "win32":
                return (
                    installation_directory
                    / "Binaries"
                    / "resources"
                    / "assets"
                    / "binaries"
                    / "AskuiRemoteDeviceController.exe"
                )
            case "darwin":
                return (
                    installation_directory
                    / "Binaries"
                    / "askui-ui-controller.app"
                    / "Contents"
                    / "Resources"
                    / "assets"
                    / "binaries"
                    / "AskuiRemoteDeviceController"
                )
            case "linux":
                return (
                    installation_directory
                    / "Binaries"
                    / "resources"
                    / "assets"
                    / "binaries"
                    / "AskuiRemoteDeviceController"
                )
            case _:
                error_msg = (
                    f'Platform "{sys.platform}" not supported by '
                    "AskUI Remote Device Controller"
                )
                raise NotImplementedError(error_msg)

    def _find_remote_device_controller_by_component_registry_file(
        self,
    ) -> pathlib.Path | None:
        if self.component_registry_file is None:
            return None

        component_registry = AskUiComponentRegistry.model_validate_json(
            self.component_registry_file.read_text()
        )
        return (
            component_registry.installed_packages.remote_device_controller_uuid.executables.askui_remote_device_controller  # noqa: E501
        )

    @cached_property
    def controller_path(self) -> pathlib.Path:
        result = (
            self.controller_path_setting
            or self._find_remote_device_controller_by_component_registry_file()
            or self._find_remote_device_controller_by_installation_directory()
        )
        assert result is not None, (
            "No AskUI Remote Device Controller found. Please set the "
            "ASKUI_COMPONENT_REGISTRY_FILE, ASKUI_INSTALLATION_DIRECTORY, or "
            "ASKUI_CONTROLLER_PATH environment variable."
        )
        if not result.is_file():
            error_msg = (
                "AskUIRemoteDeviceController executable does not exist under "
                f"`{result}`"
            )
            raise FileNotFoundError(error_msg)
        return result


__all__ = ["AskUiControllerSettings"]
