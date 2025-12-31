"""Test that token counting excludes visual validation fields."""

from askui.models.shared.agent_message_param import MessageParam, ToolUseBlockParam
from askui.models.shared.token_counter import SimpleTokenCounter


def test_token_counting_excludes_visual_validation_fields():
    """Verify that visual validation fields don't inflate token counts."""
    # Create two identical tool blocks, one with and one without visual validation
    tool_block_without = ToolUseBlockParam(
        id="test_id",
        name="computer",
        input={"action": "left_click", "coordinate": [100, 200]},
        type="tool_use",
    )

    tool_block_with = ToolUseBlockParam(
        id="test_id",
        name="computer",
        input={"action": "left_click", "coordinate": [100, 200]},
        type="tool_use",
        visual_representation="a" * 1000,  # 1000 character hash
    )

    # Create messages
    msg_without = MessageParam(role="assistant", content=[tool_block_without])
    msg_with = MessageParam(role="assistant", content=[tool_block_with])

    # Count tokens
    counter = SimpleTokenCounter()
    counts_without = counter.count_tokens(messages=[msg_without])
    counts_with = counter.count_tokens(messages=[msg_with])

    # Token counts should be identical (visual fields excluded from counting)
    assert counts_without.total == counts_with.total, (
        f"Token counts differ: {counts_without.total} vs {counts_with.total}. "
        "Visual validation fields should be excluded from token counting."
    )


def test_token_counter_uses_api_context():
    """Verify that token counter uses for_api context when stringifying objects."""
    tool_block = ToolUseBlockParam(
        id="test_id",
        name="computer",
        input={"action": "left_click", "coordinate": [100, 200]},
        type="tool_use",
        visual_representation="hash123",
    )

    counter = SimpleTokenCounter()

    # Stringify the object (as token counter does internally)
    stringified = counter._stringify_object(tool_block)

    # Should not contain visual validation fields
    assert "visual_representation" not in stringified
    assert "hash123" not in stringified

    # Should contain regular fields
    assert "test_id" in stringified
    assert "computer" in stringified


def test_token_counting_with_multiple_tool_blocks():
    """Test token counting with multiple tool blocks in one message."""
    blocks = [
        ToolUseBlockParam(
            id=f"id_{i}",
            name="computer",
            input={"action": "left_click", "coordinate": [i * 100, i * 100]},
            type="tool_use",
            visual_representation="x" * 500,  # Large hash
        )
        for i in range(5)
    ]

    blocks_without_validation = [
        ToolUseBlockParam(
            id=f"id_{i}",
            name="computer",
            input={"action": "left_click", "coordinate": [i * 100, i * 100]},
            type="tool_use",
        )
        for i in range(5)
    ]

    msg_with = MessageParam(role="assistant", content=blocks)
    msg_without = MessageParam(role="assistant", content=blocks_without_validation)

    counter = SimpleTokenCounter()
    counts_with = counter.count_tokens(messages=[msg_with])
    counts_without = counter.count_tokens(messages=[msg_without])

    # Should have same token count
    assert counts_with.total == counts_without.total
