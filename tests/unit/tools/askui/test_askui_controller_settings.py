import pathlib
import sys
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from askui.tools.askui.askui_controller_settings import AskUiControllerSettings


class TestAskUiControllerSettings:
    """Test suite for AskUiControllerSettings."""

    def test_controller_path_setting_takes_precedence(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Test that ASKUI_CONTROLLER_PATH takes precedence over other settings."""
        controller_path = tmp_path / "controller.exe"
        controller_path.touch()

        with patch.dict(
            "os.environ", {"ASKUI_CONTROLLER_PATH": str(controller_path)}, clear=True
        ):
            settings = AskUiControllerSettings()
            assert settings.controller_path == controller_path

    def test_component_registry_file_resolution(self, tmp_path: pathlib.Path) -> None:
        """Test resolution via component registry file."""
        registry_file = tmp_path / "registry.json"
        controller_path = tmp_path / "controller.exe"
        controller_path.touch()

        registry_content = {
            "DefinitionVersion": 1,
            "InstalledPackages": {
                "{aed1b543-e856-43ad-b1bc-19365d35c33e}": {
                    "Executables": {"AskUIRemoteDeviceController": str(controller_path)}
                }
            },
        }

        import json

        registry_file.write_text(json.dumps(registry_content))

        with patch.dict(
            "os.environ",
            {"ASKUI_COMPONENT_REGISTRY_FILE": str(registry_file)},
            clear=True,
        ):
            settings = AskUiControllerSettings()
            assert settings.controller_path == controller_path

    def test_installation_directory_resolution(self, tmp_path: pathlib.Path) -> None:
        """Test resolution via installation directory."""
        installation_dir = tmp_path / "installation"
        installation_dir.mkdir()

        # Create the expected path structure based on platform
        if sys.platform == "win32":
            controller_path = (
                installation_dir
                / "Binaries"
                / "resources"
                / "assets"
                / "binaries"
                / "AskuiRemoteDeviceController.exe"
            )
        elif sys.platform == "darwin":
            controller_path = (
                installation_dir
                / "Binaries"
                / "askui-ui-controller.app"
                / "Contents"
                / "Resources"
                / "assets"
                / "binaries"
                / "AskuiRemoteDeviceController"
            )
        else:  # linux
            controller_path = (
                installation_dir
                / "Binaries"
                / "resources"
                / "assets"
                / "binaries"
                / "AskuiRemoteDeviceController"
            )

        controller_path.parent.mkdir(parents=True, exist_ok=True)
        controller_path.touch()

        with patch.dict(
            "os.environ",
            {"ASKUI_INSTALLATION_DIRECTORY": str(installation_dir)},
            clear=True,
        ):
            settings = AskUiControllerSettings()
            assert settings.controller_path == controller_path

    def test_no_environment_variables_raises_error(self) -> None:
        """Test that ValueError is raised when no environment variables are set."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(
                ValueError, match="Either ASKUI_COMPONENT_REGISTRY_FILE"
            ):
                AskUiControllerSettings()

    def test_build_controller_path_windows(self) -> None:
        """Test _build_controller_path for Windows platform."""
        with patch("sys.platform", "win32"):
            with patch.dict(
                "os.environ", {"ASKUI_CONTROLLER_PATH": "/tmp/test"}, clear=True
            ):
                settings = AskUiControllerSettings()
                installation_dir = pathlib.Path("/test/installation")
                expected_path = (
                    installation_dir
                    / "Binaries"
                    / "resources"
                    / "assets"
                    / "binaries"
                    / "AskuiRemoteDeviceController.exe"
                )
                assert (
                    settings._build_controller_path(installation_dir) == expected_path
                )

    def test_build_controller_path_darwin(self) -> None:
        """Test _build_controller_path for macOS platform."""
        with patch("sys.platform", "darwin"):
            with patch.dict(
                "os.environ", {"ASKUI_CONTROLLER_PATH": "/tmp/test"}, clear=True
            ):
                settings = AskUiControllerSettings()
                installation_dir = pathlib.Path("/test/installation")
                expected_path = (
                    installation_dir
                    / "Binaries"
                    / "askui-ui-controller.app"
                    / "Contents"
                    / "Resources"
                    / "assets"
                    / "binaries"
                    / "AskuiRemoteDeviceController"
                )
                assert (
                    settings._build_controller_path(installation_dir) == expected_path
                )

    def test_build_controller_path_linux(self) -> None:
        """Test _build_controller_path for Linux platform."""
        with patch("sys.platform", "linux"):
            with patch.dict(
                "os.environ", {"ASKUI_CONTROLLER_PATH": "/tmp/test"}, clear=True
            ):
                settings = AskUiControllerSettings()
                installation_dir = pathlib.Path("/test/installation")
                expected_path = (
                    installation_dir
                    / "Binaries"
                    / "resources"
                    / "assets"
                    / "binaries"
                    / "AskuiRemoteDeviceController"
                )
                assert (
                    settings._build_controller_path(installation_dir) == expected_path
                )

    def test_build_controller_path_unsupported_platform(self) -> None:
        """Test _build_controller_path for unsupported platform."""
        with patch("sys.platform", "unsupported"):
            with patch.dict(
                "os.environ", {"ASKUI_CONTROLLER_PATH": "/tmp/test"}, clear=True
            ):
                settings = AskUiControllerSettings()
                installation_dir = pathlib.Path("/test/installation")
                with pytest.raises(
                    NotImplementedError, match='Platform "unsupported" not supported'
                ):
                    settings._build_controller_path(installation_dir)

    def test_invalid_component_registry_file(self, tmp_path: pathlib.Path) -> None:
        """Test handling of invalid component registry file."""
        registry_file = tmp_path / "invalid.json"
        registry_file.write_text("invalid json")

        with patch.dict(
            "os.environ",
            {"ASKUI_COMPONENT_REGISTRY_FILE": str(registry_file)},
            clear=True,
        ):
            settings = AskUiControllerSettings()
            # Should return None when registry file is invalid
            with pytest.raises(ValidationError):
                settings._find_remote_device_controller_by_component_registry_file()

    def test_missing_component_registry_file(self, tmp_path: pathlib.Path) -> None:
        """Test handling of missing component registry file."""
        registry_file = tmp_path / "missing.json"

        with patch.dict(
            "os.environ",
            {"ASKUI_COMPONENT_REGISTRY_FILE": str(registry_file)},
            clear=True,
        ):
            settings = AskUiControllerSettings()
            # Should raise FileNotFoundError when registry file doesn't exist
            with pytest.raises(FileNotFoundError):
                settings._find_remote_device_controller_by_component_registry_file()

    def test_controller_executable_not_found(self, tmp_path: pathlib.Path) -> None:
        """Test error when controller executable doesn't exist."""
        controller_path = tmp_path / "nonexistent.exe"

        with patch.dict(
            "os.environ", {"ASKUI_CONTROLLER_PATH": str(controller_path)}, clear=True
        ):
            settings = AskUiControllerSettings()
            with pytest.raises(
                FileNotFoundError,
                match="AskUIRemoteDeviceController executable does not exist",
            ):
                _ = settings.controller_path

    def test_controller_path_cached_property(self, tmp_path: pathlib.Path) -> None:
        """Test that controller_path is cached."""
        controller_path = tmp_path / "controller.exe"
        controller_path.touch()

        with patch.dict(
            "os.environ", {"ASKUI_CONTROLLER_PATH": str(controller_path)}, clear=True
        ):
            settings = AskUiControllerSettings()

            # First call should resolve the path
            first_result = settings.controller_path
            assert first_result == controller_path

            # Second call should use cached result
            second_result = settings.controller_path
            assert second_result == controller_path
            assert first_result is second_result

    def test_priority_order_controller_path_first(self, tmp_path: pathlib.Path) -> None:
        """Test that controller_path_setting takes priority over other methods."""
        controller_path = tmp_path / "controller.exe"
        controller_path.touch()

        registry_file = tmp_path / "registry.json"
        registry_file.write_text('{"DefinitionVersion": 1, "InstalledPackages": {}}')

        installation_dir = tmp_path / "installation"
        installation_dir.mkdir()

        with patch.dict(
            "os.environ",
            {
                "ASKUI_CONTROLLER_PATH": str(controller_path),
                "ASKUI_COMPONENT_REGISTRY_FILE": str(registry_file),
                "ASKUI_INSTALLATION_DIRECTORY": str(installation_dir),
            },
            clear=True,
        ):
            settings = AskUiControllerSettings()
            assert settings.controller_path == controller_path

    def test_priority_order_component_registry_second(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Test that component registry takes priority over installation directory."""
        registry_file = tmp_path / "registry.json"
        controller_path = tmp_path / "controller.exe"
        controller_path.touch()

        registry_content = {
            "DefinitionVersion": 1,
            "InstalledPackages": {
                "{aed1b543-e856-43ad-b1bc-19365d35c33e}": {
                    "Executables": {"AskUIRemoteDeviceController": str(controller_path)}
                }
            },
        }

        import json

        registry_file.write_text(json.dumps(registry_content))

        installation_dir = tmp_path / "installation"
        installation_dir.mkdir()

        with patch.dict(
            "os.environ",
            {
                "ASKUI_COMPONENT_REGISTRY_FILE": str(registry_file),
                "ASKUI_INSTALLATION_DIRECTORY": str(installation_dir),
            },
            clear=True,
        ):
            settings = AskUiControllerSettings()
            assert settings.controller_path == controller_path

    def test_installation_directory_fallback(self, tmp_path: pathlib.Path) -> None:
        """Test that installation directory is used as fallback."""
        installation_dir = tmp_path / "installation"
        installation_dir.mkdir()

        # Create the expected path structure
        if sys.platform == "win32":
            controller_path = (
                installation_dir
                / "Binaries"
                / "resources"
                / "assets"
                / "binaries"
                / "AskuiRemoteDeviceController.exe"
            )
        elif sys.platform == "darwin":
            controller_path = (
                installation_dir
                / "Binaries"
                / "askui-ui-controller.app"
                / "Contents"
                / "Resources"
                / "assets"
                / "binaries"
                / "AskuiRemoteDeviceController"
            )
        else:  # linux
            controller_path = (
                installation_dir
                / "Binaries"
                / "resources"
                / "assets"
                / "binaries"
                / "AskuiRemoteDeviceController"
            )

        controller_path.parent.mkdir(parents=True, exist_ok=True)
        controller_path.touch()

        with patch.dict(
            "os.environ",
            {"ASKUI_INSTALLATION_DIRECTORY": str(installation_dir)},
            clear=True,
        ):
            settings = AskUiControllerSettings()
            assert settings.controller_path == controller_path

    def test_none_values_return_none(self) -> None:
        """Test that None values are handled correctly."""
        # Create a settings instance with mocked environment
        with patch.dict(
            "os.environ", {"ASKUI_CONTROLLER_PATH": "/tmp/test"}, clear=True
        ):
            settings = AskUiControllerSettings()

            # Mock the methods to return None
            with (
                patch.object(settings, "component_registry_file", None),
                patch.object(settings, "installation_directory", None),
            ):
                assert (
                    settings._find_remote_device_controller_by_installation_directory()
                    is None
                )
                # Note: _find_remote_device_controller_by_component_registry_file will
                # raise
                # FileNotFoundError when component_registry_file is None, so we test
                # that separately

    def test_assertion_error_when_no_controller_found(self) -> None:
        """Test that assertion error is raised when no controller is found."""
        # Create a settings instance with mocked environment
        with patch.dict(
            "os.environ", {"ASKUI_CONTROLLER_PATH": "/tmp/test"}, clear=True
        ):
            settings = AskUiControllerSettings()

            # Mock all resolution methods to return None
            with (
                patch.object(
                    settings,
                    "_find_remote_device_controller_by_component_registry_file",
                    return_value=None,
                ),
                patch.object(
                    settings,
                    "_find_remote_device_controller_by_installation_directory",
                    return_value=None,
                ),
                patch.object(settings, "controller_path_setting", None),
            ):
                with pytest.raises(
                    AssertionError, match="No AskUI Remote Device Controller found"
                ):
                    _ = settings.controller_path

    def test_controller_args_default_value(self) -> None:
        """Test that controller_args is set correctly with default value."""
        settings = AskUiControllerSettings(component_registry_file="/dummy")
        assert settings.controller_args == "--showOverlay true"

    def test_controller_args_constructor(self) -> None:
        """Test that controller_args is set correctly with constructor."""
        settings = AskUiControllerSettings(
            controller_args="--showOverlay false", component_registry_file="/dummy"
        )
        assert settings.controller_args == "--showOverlay false"

    def test_controller_args_with_environment_variable(self) -> None:
        """Test that controller_args is set correctly with environment variable."""
        with patch.dict(
            "os.environ",
            {
                "ASKUI_CONTROLLER_ARGS": "--showOverlay false",
            },
            clear=True,
        ):
            settings = AskUiControllerSettings(component_registry_file="/dummy")
            assert settings.controller_args == "--showOverlay false"

    def test_controller_args_with_invalid_arg(self) -> None:
        """Test that controller_args validation raises ValueError."""
        with pytest.raises(
            ValueError, match="--showOverlay must be followed by 'true' or 'false'"
        ):
            AskUiControllerSettings(controller_args="--showOverlay")
