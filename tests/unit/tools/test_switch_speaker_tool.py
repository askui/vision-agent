"""Unit tests for SwitchSpeakerTool."""

from askui.tools.switch_speaker_tool import SwitchSpeakerTool


def test_switch_speaker_tool_name() -> None:
    """Test that the tool name starts with switch_speaker."""
    tool = SwitchSpeakerTool(speaker_names=["CacheExecutor"])
    assert tool.name.startswith("switch_speaker")


def test_switch_speaker_tool_enum_constraint() -> None:
    """Test that speaker names are set as enum in input schema."""
    tool = SwitchSpeakerTool(speaker_names=["CacheExecutor", "ValidationAgent"])
    enum_values = tool.input_schema["properties"]["speaker_name"]["enum"]
    assert enum_values == ["CacheExecutor", "ValidationAgent"]


def test_switch_speaker_tool_is_not_cacheable() -> None:
    """Test that the tool is marked as not cacheable."""
    tool = SwitchSpeakerTool(speaker_names=["CacheExecutor"])
    assert tool.is_cacheable is False


def test_switch_speaker_tool_call_returns_acknowledgment() -> None:
    """Test that calling the tool returns an acknowledgment message."""
    tool = SwitchSpeakerTool(speaker_names=["CacheExecutor"])
    result = tool(speaker_name="CacheExecutor")
    assert "Switching to speaker 'CacheExecutor'" == result


def test_switch_speaker_tool_call_with_context() -> None:
    """Test that calling the tool with context works."""
    tool = SwitchSpeakerTool(speaker_names=["CacheExecutor"])
    result = tool(
        speaker_name="CacheExecutor",
        speaker_context={"trajectory_file": "test.json"},
    )
    assert "CacheExecutor" in result
