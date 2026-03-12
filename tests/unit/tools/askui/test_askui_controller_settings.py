from unittest.mock import patch

import pytest

from askui.tools.askui.askui_controller_settings import AskUiControllerSettings


class TestAskUiControllerSettings:
    """Test suite for AskUiControllerSettings."""

    def test_controller_args_default_value(self) -> None:
        """Test that controller_args is set correctly with default value."""
        settings = AskUiControllerSettings()
        assert settings.controller_args == "--showOverlay false"

    def test_controller_args_constructor(self) -> None:
        """Test that controller_args is set correctly with constructor."""
        settings = AskUiControllerSettings(controller_args="--showOverlay false")
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
            settings = AskUiControllerSettings()
            assert settings.controller_args == "--showOverlay false"

    def test_controller_args_with_invalid_arg(self) -> None:
        """Test that controller_args validation raises ValueError."""
        with pytest.raises(
            ValueError, match="--showOverlay must be followed by 'true' or 'false'"
        ):
            AskUiControllerSettings(controller_args="--showOverlay")
