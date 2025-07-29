import pathlib
import sys
from functools import cached_property

from pydantic import BaseModel, Field, model_validator
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
