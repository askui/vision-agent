"""Unit tests for truncation strategies."""

from unittest.mock import MagicMock

from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    ContentBlockParam,
    ImageBlockParam,
    MessageParam,
    TextBlockParam,
    ToolResultBlockParam,
    ToolUseBlockParam,
    UrlImageSourceParam,
)
from askui.models.shared.truncation_strategies import (
    AskUITruncationStrategy,
)

IMAGE_REMOVED_PLACEHOLDER = "[Screenshot removed to reduce message history length]"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_base64_image_block() -> ImageBlockParam:
    return ImageBlockParam(
        source=Base64ImageSourceParam(data="abc123", media_type="image/png"),
    )


def _make_url_image_block() -> ImageBlockParam:
    return ImageBlockParam(
        source=UrlImageSourceParam(url="https://example.com/img.png"),
    )


def _make_tool_result_with_image(tool_use_id: str = "tool_1") -> ToolResultBlockParam:
    return ToolResultBlockParam(
        tool_use_id=tool_use_id,
        content=[
            TextBlockParam(text="result text"),
            _make_base64_image_block(),
        ],
    )


def _make_vlm_provider() -> MagicMock:
    provider = MagicMock()
    provider.create_message.return_value = MessageParam(
        role="assistant",
        content="Summary of the conversation.",
    )
    return provider


def _make_strategy(
    vlm_provider: MagicMock | None = None,
    n_images_to_keep: int = 3,
    n_messages_to_keep: int = 10,
    max_input_tokens: int = 100_000,
) -> AskUITruncationStrategy:
    return AskUITruncationStrategy(
        vlm_provider=vlm_provider or _make_vlm_provider(),
        n_images_to_keep=n_images_to_keep,
        n_messages_to_keep=n_messages_to_keep,
        max_input_tokens=max_input_tokens,
    )


def _get_cache_control(block: ContentBlockParam) -> object:
    """Safely get cache_control from a block (returns None for thinking blocks)."""
    return getattr(block, "cache_control", None)


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


class TestReset:
    def test_reset_creates_independent_lists(self) -> None:
        strategy = _make_strategy()
        msgs = [MessageParam(role="user", content="hello")]
        strategy.reset(msgs)
        assert strategy.full_messages is not strategy.truncated_messages

    def test_reset_none_clears_both(self) -> None:
        strategy = _make_strategy()
        strategy.reset([MessageParam(role="user", content="hello")])
        strategy.reset()
        assert strategy.full_messages == []
        assert strategy.truncated_messages == []

    def test_reset_populates_both_histories(self) -> None:
        strategy = _make_strategy()
        msgs = [
            MessageParam(role="user", content="hi"),
            MessageParam(role="assistant", content="hey"),
        ]
        strategy.reset(msgs)
        assert len(strategy.full_messages) == 2
        assert len(strategy.truncated_messages) == 2


# ---------------------------------------------------------------------------
# Append message
# ---------------------------------------------------------------------------


class TestAppendMessage:
    def test_appends_to_both_histories(self) -> None:
        strategy = _make_strategy()
        msg = MessageParam(role="user", content="hello")
        strategy.append_message(msg)
        assert len(strategy.full_messages) == 1
        assert len(strategy.truncated_messages) == 1

    def test_string_content_no_crash(self) -> None:
        strategy = _make_strategy()
        strategy.append_message(MessageParam(role="user", content="just text"))
        assert strategy.truncated_messages[0].content == "just text"


# ---------------------------------------------------------------------------
# Image removal
# ---------------------------------------------------------------------------


class TestRemoveImages:
    def test_strips_oldest_base64_images(self) -> None:
        strategy = _make_strategy(n_images_to_keep=1)
        # Append 3 messages each with a base64 image
        for i in range(3):
            role = "user" if i % 2 == 0 else "assistant"
            strategy.append_message(
                MessageParam(
                    role=role,
                    content=[_make_base64_image_block()],
                )
            )
        # Only the last image should remain; first two should be placeholders
        truncated = strategy.truncated_messages
        # Message 0: stripped
        assert isinstance(truncated[0].content, list)
        assert isinstance(truncated[0].content[0], TextBlockParam)
        assert truncated[0].content[0].text == IMAGE_REMOVED_PLACEHOLDER
        # Message 1: stripped
        assert isinstance(truncated[1].content, list)
        assert isinstance(truncated[1].content[0], TextBlockParam)
        assert truncated[1].content[0].text == IMAGE_REMOVED_PLACEHOLDER
        # Message 2: preserved
        assert isinstance(truncated[2].content, list)
        assert isinstance(truncated[2].content[0], ImageBlockParam)

    def test_skips_url_images(self) -> None:
        strategy = _make_strategy(n_images_to_keep=0)
        strategy.append_message(
            MessageParam(
                role="user",
                content=[_make_url_image_block()],
            )
        )
        # URL image should not be stripped
        content = strategy.truncated_messages[0].content
        assert isinstance(content, list)
        assert isinstance(content[0], ImageBlockParam)

    def test_strips_images_inside_tool_results(self) -> None:
        strategy = _make_strategy(n_images_to_keep=0)
        strategy.append_message(
            MessageParam(
                role="user",
                content=[_make_tool_result_with_image("tool_1")],
            )
        )
        content = strategy.truncated_messages[0].content
        assert isinstance(content, list)
        tool_result = content[0]
        assert isinstance(tool_result, ToolResultBlockParam)
        assert isinstance(tool_result.content, list)
        # First block is text (kept), second was image (stripped)
        assert isinstance(tool_result.content[0], TextBlockParam)
        assert tool_result.content[0].text == "result text"
        assert isinstance(tool_result.content[1], TextBlockParam)
        assert tool_result.content[1].text == IMAGE_REMOVED_PLACEHOLDER

    def test_preserves_non_image_blocks(self) -> None:
        strategy = _make_strategy(n_images_to_keep=0)
        strategy.append_message(
            MessageParam(
                role="user",
                content=[
                    TextBlockParam(text="keep me"),
                    _make_base64_image_block(),
                ],
            )
        )
        content = strategy.truncated_messages[0].content
        assert isinstance(content, list)
        assert isinstance(content[0], TextBlockParam)
        assert content[0].text == "keep me"

    def test_full_messages_unaffected_by_stripping(self) -> None:
        strategy = _make_strategy(n_images_to_keep=0)
        strategy.append_message(
            MessageParam(
                role="user",
                content=[_make_base64_image_block()],
            )
        )
        # Full history should still have the original image
        full_content = strategy.full_messages[0].content
        assert isinstance(full_content, list)
        assert isinstance(full_content[0], ImageBlockParam)

    def test_no_stripping_when_under_limit(self) -> None:
        strategy = _make_strategy(n_images_to_keep=5)
        strategy.append_message(
            MessageParam(
                role="user",
                content=[_make_base64_image_block()],
            )
        )
        content = strategy.truncated_messages[0].content
        assert isinstance(content, list)
        assert isinstance(content[0], ImageBlockParam)


# ---------------------------------------------------------------------------
# Cache breakpoints
# ---------------------------------------------------------------------------


class TestCacheBreakpoints:
    def test_breakpoint_on_last_user_message(self) -> None:
        strategy = _make_strategy()
        strategy.append_message(
            MessageParam(role="user", content=[TextBlockParam(text="hello")])
        )
        strategy.append_message(
            MessageParam(role="assistant", content=[TextBlockParam(text="hi")])
        )
        # Last user message (index 0) should have cache_control on its last block
        user_msg = strategy.truncated_messages[0]
        assert isinstance(user_msg.content, list)
        assert _get_cache_control(user_msg.content[-1]) is not None

    def test_breakpoint_at_image_removal_boundary(self) -> None:
        strategy = _make_strategy(n_images_to_keep=1)
        # Add messages with images - first two will be stripped
        strategy.append_message(
            MessageParam(
                role="user",
                content=[_make_base64_image_block()],
            )
        )
        strategy.append_message(
            MessageParam(
                role="assistant",
                content=[_make_base64_image_block()],
            )
        )
        strategy.append_message(
            MessageParam(
                role="user",
                content=[_make_base64_image_block()],
            )
        )
        # Boundary message (last stripped = index 1) should have cache_control
        boundary_msg = strategy.truncated_messages[1]
        assert isinstance(boundary_msg.content, list)
        assert _get_cache_control(boundary_msg.content[-1]) is not None

    def test_clears_previous_breakpoints(self) -> None:
        strategy = _make_strategy()
        # First append sets breakpoint on message 0
        strategy.append_message(
            MessageParam(role="user", content=[TextBlockParam(text="first")])
        )
        assert isinstance(strategy.truncated_messages[0].content, list)
        assert (
            _get_cache_control(strategy.truncated_messages[0].content[-1]) is not None
        )
        # Second append should clear old breakpoint and set on new last user
        strategy.append_message(
            MessageParam(role="assistant", content=[TextBlockParam(text="reply")])
        )
        strategy.append_message(
            MessageParam(role="user", content=[TextBlockParam(text="second")])
        )
        # Old user message (index 0) should have cache_control cleared
        # New user message (index 2) should have it set
        old_content = strategy.truncated_messages[0].content
        new_content = strategy.truncated_messages[2].content
        assert isinstance(old_content, list)
        assert isinstance(new_content, list)
        assert _get_cache_control(old_content[-1]) is None
        assert _get_cache_control(new_content[-1]) is not None


# ---------------------------------------------------------------------------
# Truncation / summarization
# ---------------------------------------------------------------------------


class TestTruncation:
    def test_truncate_replaces_history_with_summary(self) -> None:
        vlm = _make_vlm_provider()
        strategy = _make_strategy(vlm_provider=vlm, n_messages_to_keep=2)
        # Add enough messages to truncate
        for i in range(6):
            role = "user" if i % 2 == 0 else "assistant"
            strategy.append_message(MessageParam(role=role, content=f"msg {i}"))
        # Force truncation
        strategy.truncate()
        msgs = strategy.truncated_messages
        # First message should be the summary (user role)
        assert msgs[0].role == "user"
        assert msgs[0].content == "Summary of the conversation."
        # Last 2 messages preserved
        assert msgs[-1].content == "msg 5"
        assert msgs[-2].content == "msg 4"

    def test_truncate_inserts_synthetic_assistant_for_alternation(self) -> None:
        vlm = _make_vlm_provider()
        strategy = _make_strategy(vlm_provider=vlm, n_messages_to_keep=2)
        for i in range(6):
            role = "user" if i % 2 == 0 else "assistant"
            strategy.append_message(MessageParam(role=role, content=f"msg {i}"))
        strategy.truncate()
        msgs = strategy.truncated_messages
        # Summary (user) -> msgs[-2] is "msg 4" (user)
        # So a synthetic assistant should be inserted between
        assert msgs[0].role == "user"  # summary
        assert msgs[1].role == "assistant"  # synthetic
        assert "Understood" in str(msgs[1].content)
        assert msgs[2].role == "user"  # msg 4

    def test_truncate_skips_when_too_few_messages(self) -> None:
        strategy = _make_strategy(n_messages_to_keep=10)
        for i in range(4):
            role = "user" if i % 2 == 0 else "assistant"
            strategy.append_message(MessageParam(role=role, content=f"msg {i}"))
        strategy.truncate()
        # Should not truncate - still 4 messages
        assert len(strategy.truncated_messages) == 4

    def test_truncate_resets_image_boundary(self) -> None:
        strategy = _make_strategy(n_images_to_keep=0, n_messages_to_keep=2)
        strategy.append_message(
            MessageParam(
                role="user",
                content=[_make_base64_image_block()],
            )
        )
        strategy.append_message(
            MessageParam(
                role="assistant",
                content=[TextBlockParam(text="ok")],
            )
        )
        strategy.append_message(
            MessageParam(role="user", content=[TextBlockParam(text="more")])
        )
        strategy.append_message(
            MessageParam(
                role="assistant",
                content=[TextBlockParam(text="sure")],
            )
        )
        # _image_removal_boundary_index should be set after image stripping
        assert strategy._image_removal_boundary_index is not None  # noqa: SLF001
        strategy.truncate()
        assert strategy._image_removal_boundary_index is None  # noqa: SLF001

    def test_full_messages_preserved_after_truncation(self) -> None:
        vlm = _make_vlm_provider()
        strategy = _make_strategy(vlm_provider=vlm, n_messages_to_keep=2)
        for i in range(6):
            role = "user" if i % 2 == 0 else "assistant"
            strategy.append_message(MessageParam(role=role, content=f"msg {i}"))
        strategy.truncate()
        # Full messages should still have all 6
        assert len(strategy.full_messages) == 6
        # Truncated messages should be shorter
        assert len(strategy.truncated_messages) < 6

    def test_auto_truncation_on_token_limit(self) -> None:
        vlm = _make_vlm_provider()
        # Very low token threshold to trigger auto-truncation
        strategy = _make_strategy(
            vlm_provider=vlm,
            n_messages_to_keep=2,
            max_input_tokens=100,
        )
        # Add messages with enough text to exceed 100 * 0.7 = 70 token threshold
        strategy.append_message(MessageParam(role="user", content="x" * 300))
        strategy.append_message(MessageParam(role="assistant", content="y" * 300))
        strategy.append_message(MessageParam(role="user", content="z" * 300))
        # Should have been auto-truncated
        vlm.create_message.assert_called_once()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_messages_no_crash(self) -> None:
        strategy = _make_strategy()
        strategy.reset([])
        assert strategy.truncated_messages == []
        assert strategy.full_messages == []

    def test_single_message_with_many_images(self) -> None:
        strategy = _make_strategy(n_images_to_keep=1)
        content: list[ContentBlockParam] = [
            _make_base64_image_block() for _ in range(5)
        ]
        strategy.append_message(MessageParam(role="user", content=content))
        result = strategy.truncated_messages[0].content
        assert isinstance(result, list)
        # First 4 should be placeholders, last should be image
        placeholders = [b for b in result if isinstance(b, TextBlockParam)]
        images = [b for b in result if isinstance(b, ImageBlockParam)]
        assert len(placeholders) == 4
        assert len(images) == 1

    def test_mixed_base64_and_url_images(self) -> None:
        strategy = _make_strategy(n_images_to_keep=0)
        content: list[ContentBlockParam] = [
            _make_base64_image_block(),
            _make_url_image_block(),
            _make_base64_image_block(),
        ]
        strategy.append_message(MessageParam(role="user", content=content))
        result = strategy.truncated_messages[0].content
        assert isinstance(result, list)
        # base64 images stripped, URL image kept
        assert isinstance(result[0], TextBlockParam)  # was base64
        assert isinstance(result[1], ImageBlockParam)  # URL kept
        assert isinstance(result[2], TextBlockParam)  # was base64

    def test_tool_use_blocks_preserved(self) -> None:
        strategy = _make_strategy(n_images_to_keep=0)
        strategy.append_message(
            MessageParam(
                role="assistant",
                content=[
                    ToolUseBlockParam(
                        id="t1",
                        input={"x": 1},
                        name="my_tool",
                        type="tool_use",
                    ),
                ],
            )
        )
        result = strategy.truncated_messages[0].content
        assert isinstance(result, list)
        assert isinstance(result[0], ToolUseBlockParam)
