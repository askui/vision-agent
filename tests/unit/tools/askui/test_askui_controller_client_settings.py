from unittest.mock import patch

import pytest
from pydantic import ValidationError

from askui.tools.askui.askui_controller_client_settings import (
    AskUiControllerClientSettings,
)


class TestAskUiControllerClientSettings:
    """Test suite for AskUiControllerClientSettings."""

    def test_defaults(self) -> None:
        """Defaults are applied when no environment variables are set."""
        with patch.dict("os.environ", {}, clear=True):
            settings = AskUiControllerClientSettings()
            assert settings.server_address == "localhost:23000"
            assert settings.server_autostart is True

    def test_server_address_from_env(self) -> None:
        """
        `ASKUI_CONTOLLER_CLIENT_SERVER_ADDRESS` overrides default for `server_address`.
        """
        with patch.dict(
            "os.environ",
            {"ASKUI_CONTOLLER_CLIENT_SERVER_ADDRESS": "127.0.0.1:24000"},
            clear=True,
        ):
            settings = AskUiControllerClientSettings()
            assert settings.server_address == "127.0.0.1:24000"

    def test_server_autostart_from_env_false(self) -> None:
        """`ASKUI_CONTOLLER_CLIENT_SERVER_AUTOSTART` parses boolean from env."""
        with patch.dict(
            "os.environ",
            {"ASKUI_CONTOLLER_CLIENT_SERVER_AUTOSTART": "False"},
            clear=True,
        ):
            settings = AskUiControllerClientSettings()
            assert settings.server_autostart is False

    def test_server_autostart_from_env_true(self) -> None:
        """Boolean true value is parsed correctly from environment variable."""
        with patch.dict(
            "os.environ",
            {"ASKUI_CONTOLLER_CLIENT_SERVER_AUTOSTART": "true"},
            clear=True,
        ):
            settings = AskUiControllerClientSettings()
            assert settings.server_autostart is True

    def test_server_address_from_constructor(self) -> None:
        """`server_address` is set correctly from constructor."""
        settings = AskUiControllerClientSettings(server_address="127.0.0.1:24000")
        assert settings.server_address == "127.0.0.1:24000"

    def test_server_autostart_from_constructor(self) -> None:
        """`server_autostart` is set correctly from constructor."""
        settings = AskUiControllerClientSettings(server_autostart=False)
        assert settings.server_autostart is False

    def test_autostart_from_env_with_invalid_value(self) -> None:
        """
        Test that ValidationError is raised when environment variable is invalid.
        """
        with patch.dict(
            "os.environ",
            {"ASKUI_CONTOLLER_CLIENT_SERVER_AUTOSTART": "invalid"},
            clear=True,
        ):
            with pytest.raises(ValidationError):
                AskUiControllerClientSettings()
