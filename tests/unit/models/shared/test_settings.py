import pytest
from pydantic import ValidationError

from askui.models.shared.settings import ActSettings, TruncationStrategySettings


class TestTruncationStrategySettings:
    """Tests for TruncationStrategySettings."""

    def test_default_strategy_is_simple(self) -> None:
        """Test that the default truncation strategy is 'simple'."""
        settings = TruncationStrategySettings()
        assert settings.strategy == "simple"

    def test_can_set_simple_strategy(self) -> None:
        """Test that 'simple' strategy can be explicitly set."""
        settings = TruncationStrategySettings(strategy="simple")
        assert settings.strategy == "simple"

    def test_can_set_latest_image_only_strategy(self) -> None:
        """Test that 'latest_image_only' strategy can be set."""
        settings = TruncationStrategySettings(strategy="latest_image_only")
        assert settings.strategy == "latest_image_only"

    def test_rejects_invalid_strategy(self) -> None:
        """Test that invalid strategy values are rejected."""
        with pytest.raises(ValidationError):
            TruncationStrategySettings(strategy="invalid_strategy")  # pyright: ignore[reportArgumentType]

    def test_serialization(self) -> None:
        """Test that settings can be serialized."""
        settings = TruncationStrategySettings(strategy="latest_image_only")
        serialized = settings.model_dump()
        assert serialized == {"strategy": "latest_image_only"}

    def test_deserialization(self) -> None:
        """Test that settings can be deserialized."""
        data = {"strategy": "simple"}
        settings = TruncationStrategySettings(**data)
        assert settings.strategy == "simple"


class TestActSettings:
    """Tests for ActSettings integration with TruncationStrategySettings."""

    def test_default_act_settings_has_default_truncation(self) -> None:
        """Test that ActSettings has default truncation settings."""
        settings = ActSettings()
        assert settings.truncation.strategy == "simple"

    def test_can_set_truncation_strategy_in_act_settings(self) -> None:
        """Test that truncation strategy can be set in ActSettings."""
        settings = ActSettings(
            truncation=TruncationStrategySettings(strategy="latest_image_only")
        )
        assert settings.truncation.strategy == "latest_image_only"

    def test_act_settings_serialization_includes_truncation(self) -> None:
        """Test that ActSettings serialization includes truncation settings."""
        settings = ActSettings(
            truncation=TruncationStrategySettings(strategy="latest_image_only")
        )
        serialized = settings.model_dump()
        assert "truncation" in serialized
        assert serialized["truncation"]["strategy"] == "latest_image_only"

    def test_act_settings_deserialization_with_truncation(self) -> None:
        """Test that ActSettings can be deserialized with truncation settings."""
        data = {
            "messages": {"max_tokens": 4096},
            "truncation": {"strategy": "latest_image_only"},
        }
        settings = ActSettings(**data)
        assert settings.truncation.strategy == "latest_image_only"
        assert settings.messages.max_tokens == 4096
