"""Integration tests for Agent.act() with different truncation strategies."""

import logging
from typing_extensions import Literal
from unittest.mock import Mock

import pytest

from askui.models.shared.agent import Agent
from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    ImageBlockParam,
    MessageParam,
)
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.settings import ActSettings, TruncationStrategySettings


def _create_text_message(role: Literal["user", "assistant"], text: str) -> MessageParam:
    """Helper to create a simple text message."""
    return MessageParam(role=role, content=text)


def _create_image_message(
    role: Literal["user", "assistant"], image_data: str = "image_data"
) -> MessageParam:
    """Helper to create a message with an image."""
    return MessageParam(
        role=role,
        content=[
            ImageBlockParam(
                type="image",
                source=Base64ImageSourceParam(
                    type="base64", media_type="image/png", data=image_data
                ),
            )
        ],
    )


class TestAgentTruncationStrategyIntegration:
    """Integration tests for Agent with truncation strategies."""

    def _create_mock_messages_api(self) -> MessagesApi:
        """Create a mock MessagesApi that returns a simple response."""
        mock_api = Mock(spec=MessagesApi)
        # Mock the create_message to return a simple assistant response
        mock_api.create_message.return_value = MessageParam(
            role="assistant",
            content="Response",
            stop_reason="end_turn",
        )
        return mock_api

    def test_agent_uses_default_simple_truncation_strategy(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that Agent uses SimpleTruncationStrategy by default."""
        mock_api = self._create_mock_messages_api()
        agent = Agent(messages_api=mock_api)

        messages = [_create_text_message("user", "Hello")]

        with caplog.at_level(logging.WARNING):
            agent.act(
                messages=messages,
                model="claude-3-5-sonnet-20241022",
            )

        # Verify no warning about experimental strategy
        assert not any(
            "experimental LatestImageOnlyTruncationStrategy" in record.message
            for record in caplog.records
        )

        # Verify API was called
        mock_api.create_message.assert_called_once()

    def test_agent_uses_simple_strategy_when_explicitly_set(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that Agent uses SimpleTruncationStrategy when explicitly set."""
        mock_api = self._create_mock_messages_api()
        agent = Agent(messages_api=mock_api)

        messages = [_create_text_message("user", "Hello")]
        settings = ActSettings(truncation=TruncationStrategySettings(strategy="simple"))

        with caplog.at_level(logging.WARNING):
            agent.act(
                messages=messages,
                model="claude-3-5-sonnet-20241022",
                settings=settings,
            )

        # Verify no warning about experimental strategy
        assert not any(
            "experimental LatestImageOnlyTruncationStrategy" in record.message
            for record in caplog.records
        )

        # Verify API was called
        mock_api.create_message.assert_called_once()

    def test_agent_uses_latest_image_only_strategy_when_configured(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that Agent uses LatestImageOnlyTruncationStrategy when configured."""
        mock_api = self._create_mock_messages_api()
        agent = Agent(messages_api=mock_api)

        messages = [_create_text_message("user", "Hello")]
        settings = ActSettings(
            truncation=TruncationStrategySettings(strategy="latest_image_only")
        )

        with caplog.at_level(logging.WARNING):
            agent.act(
                messages=messages,
                model="claude-3-5-sonnet-20241022",
                settings=settings,
            )

        # Verify warning about experimental strategy was logged
        assert any(
            "experimental LatestImageOnlyTruncationStrategy" in record.message
            for record in caplog.records
        )

        # Verify API was called
        mock_api.create_message.assert_called_once()

    def test_agent_latest_image_only_strategy_removes_old_images(self) -> None:
        """Test that latest_image_only strategy actually removes old images."""
        mock_api = self._create_mock_messages_api()
        agent = Agent(messages_api=mock_api)

        messages = [
            _create_image_message("user", "old_image"),
            _create_text_message("assistant", "Response"),
            _create_image_message("user", "new_image"),
        ]

        settings = ActSettings(
            truncation=TruncationStrategySettings(strategy="latest_image_only")
        )

        agent.act(
            messages=messages,
            model="claude-3-5-sonnet-20241022",
            settings=settings,
        )

        # Get the messages that were sent to the API
        call_args = mock_api.create_message.call_args
        sent_messages = call_args.kwargs["messages"]

        # First message should have image replaced
        assert isinstance(sent_messages[0].content, list)
        assert not any(block.type == "image" for block in sent_messages[0].content)
        assert any(
            block.type == "text" and block.text == "[Image removed to save tokens]"
            for block in sent_messages[0].content
        )

        # Last message should keep the image
        assert isinstance(sent_messages[2].content, list)
        assert any(block.type == "image" for block in sent_messages[2].content)

    def test_agent_simple_strategy_preserves_all_images(self) -> None:
        """Test that simple strategy preserves all images."""
        mock_api = self._create_mock_messages_api()
        agent = Agent(messages_api=mock_api)

        messages = [
            _create_image_message("user", "image1"),
            _create_text_message("assistant", "Response"),
            _create_image_message("user", "image2"),
        ]

        settings = ActSettings(truncation=TruncationStrategySettings(strategy="simple"))

        agent.act(
            messages=messages,
            model="claude-3-5-sonnet-20241022",
            settings=settings,
        )

        # Get the messages that were sent to the API
        call_args = mock_api.create_message.call_args
        sent_messages = call_args.kwargs["messages"]

        # Both messages should still have images
        assert isinstance(sent_messages[0].content, list)
        assert any(block.type == "image" for block in sent_messages[0].content)

        assert isinstance(sent_messages[2].content, list)
        assert any(block.type == "image" for block in sent_messages[2].content)

    def test_agent_can_switch_strategies_between_act_calls(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that different strategies can be used for different act() calls."""
        mock_api = self._create_mock_messages_api()
        agent = Agent(messages_api=mock_api)

        messages = [_create_text_message("user", "Hello")]

        # First call with simple strategy
        settings_simple = ActSettings(
            truncation=TruncationStrategySettings(strategy="simple")
        )
        with caplog.at_level(logging.WARNING):
            caplog.clear()
            agent.act(
                messages=messages.copy(),
                model="claude-3-5-sonnet-20241022",
                settings=settings_simple,
            )

            # No warning for simple strategy
            assert not any(
                "experimental LatestImageOnlyTruncationStrategy" in record.message
                for record in caplog.records
            )

        # Second call with latest_image_only strategy
        settings_latest = ActSettings(
            truncation=TruncationStrategySettings(strategy="latest_image_only")
        )
        with caplog.at_level(logging.WARNING):
            caplog.clear()
            agent.act(
                messages=messages.copy(),
                model="claude-3-5-sonnet-20241022",
                settings=settings_latest,
            )

            # Warning for experimental strategy
            assert any(
                "experimental LatestImageOnlyTruncationStrategy" in record.message
                for record in caplog.records
            )

        # Verify both calls were made
        assert mock_api.create_message.call_count == 2

    def test_backwards_compatibility_with_no_settings(self) -> None:
        """Test that Agent works without any settings (backwards compatibility)."""
        mock_api = self._create_mock_messages_api()
        agent = Agent(messages_api=mock_api)

        messages = [_create_text_message("user", "Hello")]

        # Should work without settings parameter
        agent.act(
            messages=messages,
            model="claude-3-5-sonnet-20241022",
        )

        # Verify API was called
        mock_api.create_message.assert_called_once()
