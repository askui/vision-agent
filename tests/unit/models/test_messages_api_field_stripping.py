"""Tests for Pydantic-based context-aware serialization of internal fields."""

from askui.models.shared.agent_message_param import MessageParam, ToolUseBlockParam


def test_tool_use_block_includes_fields_by_default() -> None:
    """Test that visual validation fields are included in normal serialization."""
    tool_block = ToolUseBlockParam(
        id="test_id",
        name="computer",
        input={"action": "left_click", "coordinate": [100, 200]},
        type="tool_use",
        visual_representation="abc123",
    )

    # Default serialization includes all fields
    serialized = tool_block.model_dump()

    assert serialized["visual_representation"] == "abc123"
    assert serialized["id"] == "test_id"
    assert serialized["name"] == "computer"


def test_tool_use_block_excludes_fields_for_api() -> None:
    """Test that visual validation fields are excluded when for_api context is set."""
    tool_block = ToolUseBlockParam(
        id="test_id",
        name="computer",
        input={"action": "left_click", "coordinate": [100, 200]},
        type="tool_use",
        visual_representation="abc123",
    )

    # Serialization with for_api context excludes internal fields
    serialized = tool_block.model_dump(context={"for_api": True})

    # Internal fields should be excluded
    assert "visual_representation" not in serialized

    # Other fields should remain
    assert serialized["id"] == "test_id"
    assert serialized["name"] == "computer"
    assert serialized["input"] == {"action": "left_click", "coordinate": [100, 200]}


def test_tool_use_block_without_visual_validation() -> None:
    """Test serialization of tool block without visual validation fields."""
    tool_block = ToolUseBlockParam(
        id="test_id",
        name="computer",
        input={"action": "screenshot"},
        type="tool_use",
    )

    # Both modes should work fine
    normal = tool_block.model_dump()
    for_api = tool_block.model_dump(context={"for_api": True})

    # Should not have visual representation field in either case (or it should be None)
    assert (
        "visual_representation" not in normal or normal["visual_representation"] is None
    )
    assert "visual_representation" not in for_api


def test_message_with_tool_use_context_propagation() -> None:
    """Test that context propagates through nested MessageParam serialization."""
    tool_block = ToolUseBlockParam(
        id="test_id",
        name="computer",
        input={"action": "left_click", "coordinate": [100, 200]},
        type="tool_use",
        visual_representation="abc123",
    )

    message = MessageParam(role="assistant", content=[tool_block])

    # Normal dump includes fields
    normal = message.model_dump()
    assert normal["content"][0]["visual_representation"] == "abc123"

    # API dump excludes fields
    for_api = message.model_dump(context={"for_api": True})
    assert "visual_representation" not in for_api["content"][0]


def test_cache_storage_includes_all_fields() -> None:
    """Test that cache storage (mode='json') includes all fields."""
    tool_block = ToolUseBlockParam(
        id="test_id",
        name="computer",
        input={"action": "left_click", "coordinate": [100, 200]},
        type="tool_use",
        visual_representation="abc123",
    )

    # Cache storage uses mode='json' without for_api context
    cache_dump = tool_block.model_dump(mode="json")

    # Should include all fields for cache storage
    assert cache_dump["visual_representation"] == "abc123"
