import logging

import pytest
from typing_extensions import Literal

from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    ImageBlockParam,
    MessageParam,
    TextBlockParam,
    ToolResultBlockParam,
)
from askui.models.shared.truncation_strategies import (
    LatestImageOnlyTruncationStrategy,
    LatestImageOnlyTruncationStrategyFactory,
    SimpleTruncationStrategy,
    SimpleTruncationStrategyFactory,
)


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


def _create_mixed_message(
    role: Literal["user", "assistant"], text: str, image_data: str = "image_data"
) -> MessageParam:
    """Helper to create a message with both text and image."""
    return MessageParam(
        role=role,
        content=[
            TextBlockParam(type="text", text=text),
            ImageBlockParam(
                type="image",
                source=Base64ImageSourceParam(
                    type="base64", media_type="image/png", data=image_data
                ),
            ),
        ],
    )


def _create_tool_result_with_image(image_data: str = "image_data") -> MessageParam:
    """Helper to create a message with a tool_result containing an image."""
    return MessageParam(
        role="user",
        content=[
            ToolResultBlockParam(
                type="tool_result",
                tool_use_id="tool_123",
                content=[
                    ImageBlockParam(
                        type="image",
                        source=Base64ImageSourceParam(
                            type="base64", media_type="image/png", data=image_data
                        ),
                    )
                ],
            )
        ],
    )


def _has_image_in_message(message: MessageParam) -> bool:
    """Helper to check if a message contains images."""
    if not isinstance(message.content, list):
        return False

    for block in message.content:
        if block.type == "image":
            return True
        if block.type == "tool_result" and isinstance(block.content, list):
            for inner_block in block.content:
                if inner_block.type == "image":
                    return True
    return False


def _has_placeholder_in_message(message: MessageParam) -> bool:
    """Helper to check if a message contains image removal placeholders."""
    if not isinstance(message.content, list):
        return False

    for block in message.content:
        if block.type == "text" and block.text == "[Image removed to save tokens]":
            return True
        if block.type == "tool_result" and isinstance(block.content, list):
            for inner_block in block.content:
                if (
                    inner_block.type == "text"
                    and inner_block.text == "[Image removed to save tokens]"
                ):
                    return True
    return False


class TestLatestImageOnlyTruncationStrategy:
    """Tests for LatestImageOnlyTruncationStrategy."""

    def test_keeps_only_latest_image_in_conversation(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that only the latest image is kept and older ones are replaced."""
        messages = [
            _create_text_message("user", "First message"),
            _create_image_message("user", "image1"),
            _create_text_message("assistant", "Response 1"),
            _create_image_message("user", "image2"),
            _create_text_message("assistant", "Response 2"),
            _create_image_message("user", "image3"),  # This should be kept
        ]

        with caplog.at_level(logging.WARNING):
            strategy = LatestImageOnlyTruncationStrategy(
                tools=None,
                system=None,
                messages=messages.copy(),
                model="claude-3-5-sonnet-20241022",
            )

        # Check warning was logged
        assert any(
            "experimental LatestImageOnlyTruncationStrategy" in record.message
            for record in caplog.records
        )

        result_messages = strategy.messages

        # First image should be replaced with placeholder
        assert not _has_image_in_message(result_messages[1])
        assert _has_placeholder_in_message(result_messages[1])

        # Second image should be replaced with placeholder
        assert not _has_image_in_message(result_messages[3])
        assert _has_placeholder_in_message(result_messages[3])

        # Third image (latest) should be kept
        assert _has_image_in_message(result_messages[5])
        assert not _has_placeholder_in_message(result_messages[5])

    def test_keeps_images_in_latest_message_with_multiple_images(self) -> None:
        """Test that all images in the latest message with images are kept."""
        messages = [
            _create_image_message("user", "old_image"),
            _create_text_message("assistant", "Response"),
            MessageParam(
                role="user",
                content=[
                    ImageBlockParam(
                        type="image",
                        source=Base64ImageSourceParam(
                            type="base64", media_type="image/png", data="new_image1"
                        ),
                    ),
                    ImageBlockParam(
                        type="image",
                        source=Base64ImageSourceParam(
                            type="base64", media_type="image/png", data="new_image2"
                        ),
                    ),
                ],
            ),
        ]

        strategy = LatestImageOnlyTruncationStrategy(
            tools=None,
            system=None,
            messages=messages.copy(),
            model="claude-3-5-sonnet-20241022",
        )

        result_messages = strategy.messages

        # First message image should be replaced
        assert _has_placeholder_in_message(result_messages[0])
        assert not _has_image_in_message(result_messages[0])

        # Last message should keep both images
        assert _has_image_in_message(result_messages[2])
        assert isinstance(result_messages[2].content, list)
        image_count = sum(
            1 for block in result_messages[2].content if block.type == "image"
        )
        assert image_count == 2

    def test_handles_images_in_tool_result_blocks(self) -> None:
        """Test that images inside tool_result blocks are handled correctly."""
        messages = [
            _create_tool_result_with_image("old_tool_image"),
            _create_text_message("assistant", "Response"),
            _create_tool_result_with_image("new_tool_image"),  # This should be kept
        ]

        strategy = LatestImageOnlyTruncationStrategy(
            tools=None,
            system=None,
            messages=messages.copy(),
            model="claude-3-5-sonnet-20241022",
        )

        result_messages = strategy.messages

        # First tool_result image should be replaced
        assert _has_placeholder_in_message(result_messages[0])
        assert not _has_image_in_message(result_messages[0])

        # Last tool_result image should be kept
        assert _has_image_in_message(result_messages[2])
        assert not _has_placeholder_in_message(result_messages[2])

    def test_handles_mixed_content_messages(self) -> None:
        """Test messages with both text and images."""
        messages = [
            _create_mixed_message("user", "Look at this", "image1"),
            _create_text_message("assistant", "I see it"),
            _create_mixed_message("user", "Now look at this", "image2"),
        ]

        strategy = LatestImageOnlyTruncationStrategy(
            tools=None,
            system=None,
            messages=messages.copy(),
            model="claude-3-5-sonnet-20241022",
        )

        result_messages = strategy.messages

        # First message: text should remain, image should be replaced
        assert isinstance(result_messages[0].content, list)
        text_blocks = [b for b in result_messages[0].content if b.type == "text"]
        assert len(text_blocks) == 2  # Original text + placeholder
        assert any(b.text == "Look at this" for b in text_blocks)
        assert any(b.text == "[Image removed to save tokens]" for b in text_blocks)
        assert not _has_image_in_message(result_messages[0])

        # Last message: both text and image should be kept
        assert isinstance(result_messages[2].content, list)
        assert any(
            b.type == "text" and b.text == "Now look at this"
            for b in result_messages[2].content
        )
        assert _has_image_in_message(result_messages[2])

    def test_handles_conversation_with_no_images(self) -> None:
        """Test that conversations with no images are not affected."""
        messages = [
            _create_text_message("user", "Hello"),
            _create_text_message("assistant", "Hi there"),
            _create_text_message("user", "How are you?"),
        ]

        strategy = LatestImageOnlyTruncationStrategy(
            tools=None,
            system=None,
            messages=messages.copy(),
            model="claude-3-5-sonnet-20241022",
        )

        result_messages = strategy.messages

        # All messages should remain unchanged
        assert len(result_messages) == 3
        assert not any(_has_image_in_message(msg) for msg in result_messages)
        assert not any(_has_placeholder_in_message(msg) for msg in result_messages)

    def test_handles_single_image_message(self) -> None:
        """Test conversation with only one image (should be kept)."""
        messages = [
            _create_text_message("user", "Hello"),
            _create_image_message("user", "only_image"),
            _create_text_message("assistant", "I see the image"),
        ]

        strategy = LatestImageOnlyTruncationStrategy(
            tools=None,
            system=None,
            messages=messages.copy(),
            model="claude-3-5-sonnet-20241022",
        )

        result_messages = strategy.messages

        # The single image should be kept
        assert _has_image_in_message(result_messages[1])
        assert not _has_placeholder_in_message(result_messages[1])

    def test_preserves_non_image_content_blocks(self) -> None:
        """Test that non-image content blocks are preserved correctly."""
        messages = [
            MessageParam(
                role="user",
                content=[
                    TextBlockParam(type="text", text="First text"),
                    ImageBlockParam(
                        type="image",
                        source=Base64ImageSourceParam(
                            type="base64", media_type="image/png", data="image1"
                        ),
                    ),
                    TextBlockParam(type="text", text="Second text"),
                ],
            ),
            _create_image_message("user", "image2"),
        ]

        strategy = LatestImageOnlyTruncationStrategy(
            tools=None,
            system=None,
            messages=messages.copy(),
            model="claude-3-5-sonnet-20241022",
        )

        result_messages = strategy.messages

        # First message: text blocks should be preserved, image replaced
        assert isinstance(result_messages[0].content, list)
        text_blocks = [b for b in result_messages[0].content if b.type == "text"]
        assert len(text_blocks) == 3  # Two original texts + placeholder
        assert any(b.text == "First text" for b in text_blocks)
        assert any(b.text == "Second text" for b in text_blocks)
        assert any(b.text == "[Image removed to save tokens]" for b in text_blocks)

    def test_inherits_simple_truncation_behavior(self) -> None:
        """Test that the strategy still inherits SimpleTruncationStrategy behavior."""
        # Create a conversation that would trigger truncation
        # Use small limits to trigger truncation
        messages = [_create_text_message("user", "Message")] * 100

        strategy = LatestImageOnlyTruncationStrategy(
            tools=None,
            system=None,
            messages=messages.copy(),
            model="claude-3-5-sonnet-20241022",
            max_messages=50,
            message_truncation_threshold=0.5,
        )

        # Strategy should be created successfully and inherit truncation logic
        assert isinstance(strategy, SimpleTruncationStrategy)
        assert isinstance(strategy, LatestImageOnlyTruncationStrategy)


class TestLatestImageOnlyTruncationStrategyFactory:
    """Tests for LatestImageOnlyTruncationStrategyFactory."""

    def test_creates_latest_image_only_strategy(self) -> None:
        """Test that factory creates LatestImageOnlyTruncationStrategy instance."""
        factory = LatestImageOnlyTruncationStrategyFactory()
        messages = [_create_text_message("user", "Hello")]

        strategy = factory.create_truncation_strategy(
            tools=None,
            system=None,
            messages=messages,
            model="claude-3-5-sonnet-20241022",
        )

        assert isinstance(strategy, LatestImageOnlyTruncationStrategy)
        assert isinstance(strategy, SimpleTruncationStrategy)

    def test_factory_can_be_instantiated_with_custom_parameters(self) -> None:
        """Test that factory accepts custom parameters."""
        custom_max_tokens = 50_000
        custom_threshold = 0.6

        factory = LatestImageOnlyTruncationStrategyFactory(
            max_input_tokens=custom_max_tokens,
            input_token_truncation_threshold=custom_threshold,
        )

        messages = [_create_text_message("user", "Hello")]

        # Verify the strategy can be created with custom parameters
        strategy = factory.create_truncation_strategy(
            tools=None,
            system=None,
            messages=messages,
            model="claude-3-5-sonnet-20241022",
        )

        # Verify it's the correct type
        assert isinstance(strategy, LatestImageOnlyTruncationStrategy)

    def test_factory_creates_functional_strategy(self) -> None:
        """Test that factory creates a working strategy instance."""
        factory = LatestImageOnlyTruncationStrategyFactory()
        messages = [
            _create_image_message("user", "image1"),
            _create_image_message("user", "image2"),
        ]

        strategy = factory.create_truncation_strategy(
            tools=None,
            system=None,
            messages=messages.copy(),
            model="claude-3-5-sonnet-20241022",
        )

        # Test that the strategy actually performs image removal
        result_messages = strategy.messages
        assert not _has_image_in_message(result_messages[0])
        assert _has_image_in_message(result_messages[1])


class TestSimpleTruncationStrategyFactory:
    """Tests for SimpleTruncationStrategyFactory to ensure backwards compatibility."""

    def test_creates_simple_strategy(self) -> None:
        """Test that factory creates SimpleTruncationStrategy instance."""
        factory = SimpleTruncationStrategyFactory()
        messages = [_create_text_message("user", "Hello")]

        strategy = factory.create_truncation_strategy(
            tools=None,
            system=None,
            messages=messages,
            model="claude-3-5-sonnet-20241022",
        )

        assert isinstance(strategy, SimpleTruncationStrategy)
        assert not isinstance(strategy, LatestImageOnlyTruncationStrategy)

    def test_simple_strategy_preserves_all_images(self) -> None:
        """Test that SimpleTruncationStrategy does NOT remove images."""
        factory = SimpleTruncationStrategyFactory()
        messages = [
            _create_image_message("user", "image1"),
            _create_text_message("assistant", "Response"),
            _create_image_message("user", "image2"),
        ]

        strategy = factory.create_truncation_strategy(
            tools=None,
            system=None,
            messages=messages.copy(),
            model="claude-3-5-sonnet-20241022",
        )

        result_messages = strategy.messages

        # All images should be preserved
        assert _has_image_in_message(result_messages[0])
        assert _has_image_in_message(result_messages[2])
        # No placeholders should be present
        assert not any(_has_placeholder_in_message(msg) for msg in result_messages)
