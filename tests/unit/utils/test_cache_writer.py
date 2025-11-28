"""Unit tests for CacheWriter utility."""

import json
import tempfile
from pathlib import Path
from typing import Any

from askui.models.shared.agent_message_param import MessageParam, ToolUseBlockParam
from askui.models.shared.agent_on_message_cb import OnMessageCbParam
from askui.utils.cache_writer import CacheWriter


def test_cache_writer_initialization() -> None:
    """Test CacheWriter initialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_writer = CacheWriter(cache_dir=temp_dir, file_name="test.json")
        assert cache_writer.cache_dir == Path(temp_dir)
        assert cache_writer.file_name == "test.json"
        assert cache_writer.messages == []
        assert cache_writer.was_cached_execution is False


def test_cache_writer_creates_cache_directory() -> None:
    """Test that CacheWriter creates the cache directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        non_existent_dir = Path(temp_dir) / "new_cache_dir"
        assert not non_existent_dir.exists()

        CacheWriter(cache_dir=str(non_existent_dir))
        assert non_existent_dir.exists()
        assert non_existent_dir.is_dir()


def test_cache_writer_adds_json_extension() -> None:
    """Test that CacheWriter adds .json extension if not present."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_writer = CacheWriter(cache_dir=temp_dir, file_name="test")
        assert cache_writer.file_name == "test.json"

        cache_writer2 = CacheWriter(cache_dir=temp_dir, file_name="test.json")
        assert cache_writer2.file_name == "test.json"


def test_cache_writer_add_message_cb_stores_tool_use_blocks() -> None:
    """Test that add_message_cb stores ToolUseBlockParam from assistant messages."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_writer = CacheWriter(cache_dir=temp_dir, file_name="test.json")

        tool_use_block = ToolUseBlockParam(
            id="test_id",
            name="test_tool",
            input={"param": "value"},
            type="tool_use",
        )

        message = MessageParam(
            role="assistant",
            content=[tool_use_block],
            stop_reason=None,
        )

        param = OnMessageCbParam(
            message=message,
            messages=[message],
        )

        result = cache_writer.add_message_cb(param)
        assert result == param.message
        assert len(cache_writer.messages) == 1
        assert cache_writer.messages[0] == tool_use_block


def test_cache_writer_add_message_cb_ignores_non_tool_use_content() -> None:
    """Test that add_message_cb ignores non-ToolUseBlockParam content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_writer = CacheWriter(cache_dir=temp_dir, file_name="test.json")

        message = MessageParam(
            role="assistant",
            content="Just a text message",
            stop_reason=None,
        )

        param = OnMessageCbParam(
            message=message,
            messages=[message],
        )

        cache_writer.add_message_cb(param)
        assert len(cache_writer.messages) == 0


def test_cache_writer_add_message_cb_ignores_user_messages() -> None:
    """Test that add_message_cb ignores user messages."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_writer = CacheWriter(cache_dir=temp_dir, file_name="test.json")

        message = MessageParam(
            role="user",
            content="User message",
            stop_reason=None,
        )

        param = OnMessageCbParam(
            message=message,
            messages=[message],
        )

        cache_writer.add_message_cb(param)
        assert len(cache_writer.messages) == 0


def test_cache_writer_detects_cached_execution() -> None:
    """Test that CacheWriter detects when execute_cached_executions_tool is used."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_writer = CacheWriter(cache_dir=temp_dir, file_name="test.json")

        tool_use_block = ToolUseBlockParam(
            id="cached_exec_id",
            name="execute_cached_executions_tool",
            input={"trajectory_file": "test.json"},
            type="tool_use",
        )

        message = MessageParam(
            role="assistant",
            content=[tool_use_block],
            stop_reason=None,
        )

        param = OnMessageCbParam(
            message=message,
            messages=[message],
        )

        cache_writer.add_message_cb(param)
        assert cache_writer.was_cached_execution is True


def test_cache_writer_generate_writes_file() -> None:
    """Test that generate() writes messages to a JSON file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)
        cache_writer = CacheWriter(cache_dir=str(cache_dir), file_name="output.json")

        # Add some tool use blocks
        tool_use1 = ToolUseBlockParam(
            id="id1",
            name="tool1",
            input={"param": "value1"},
            type="tool_use",
        )
        tool_use2 = ToolUseBlockParam(
            id="id2",
            name="tool2",
            input={"param": "value2"},
            type="tool_use",
        )

        cache_writer.messages = [tool_use1, tool_use2]
        cache_writer.generate()

        # Verify file was created
        cache_file = cache_dir / "output.json"
        assert cache_file.exists()

        # Verify file content
        with cache_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]["id"] == "id1"
        assert data[0]["name"] == "tool1"
        assert data[1]["id"] == "id2"
        assert data[1]["name"] == "tool2"


def test_cache_writer_generate_auto_names_file() -> None:
    """Test that generate() auto-generates filename if not provided."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)
        cache_writer = CacheWriter(cache_dir=str(cache_dir), file_name="")

        tool_use = ToolUseBlockParam(
            id="id1",
            name="tool1",
            input={},
            type="tool_use",
        )
        cache_writer.messages = [tool_use]
        cache_writer.generate()

        # Verify a file was created with auto-generated name
        json_files = list(cache_dir.glob("*.json"))
        assert len(json_files) == 1
        assert json_files[0].name.startswith("cached_trajectory_")


def test_cache_writer_generate_skips_cached_execution() -> None:
    """Test that generate() doesn't write file for cached executions."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)
        cache_writer = CacheWriter(cache_dir=str(cache_dir), file_name="test.json")

        cache_writer.was_cached_execution = True
        cache_writer.messages = [
            ToolUseBlockParam(
                id="id1",
                name="tool1",
                input={},
                type="tool_use",
            )
        ]

        cache_writer.generate()

        # Verify no file was created
        json_files = list(cache_dir.glob("*.json"))
        assert len(json_files) == 0


def test_cache_writer_reset() -> None:
    """Test that reset() clears messages and filename."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_writer = CacheWriter(cache_dir=temp_dir, file_name="original.json")

        # Add some data
        cache_writer.messages = [
            ToolUseBlockParam(
                id="id1",
                name="tool1",
                input={},
                type="tool_use",
            )
        ]
        cache_writer.was_cached_execution = True

        # Reset
        cache_writer.reset(file_name="new.json")

        assert cache_writer.messages == []
        assert cache_writer.file_name == "new.json"
        assert cache_writer.was_cached_execution is False


def test_cache_writer_read_cache_file() -> None:
    """Test that read_cache_file() loads ToolUseBlockParam from JSON."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_cache.json"

        # Create a cache file
        trajectory: list[dict[str, Any]] = [
            {
                "id": "id1",
                "name": "tool1",
                "input": {"param": "value1"},
                "type": "tool_use",
            },
            {
                "id": "id2",
                "name": "tool2",
                "input": {"param": "value2"},
                "type": "tool_use",
            },
        ]

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(trajectory, f)

        # Read cache file
        result = CacheWriter.read_cache_file(cache_file)

        assert len(result) == 2
        assert isinstance(result[0], ToolUseBlockParam)
        assert result[0].id == "id1"
        assert result[0].name == "tool1"
        assert isinstance(result[1], ToolUseBlockParam)
        assert result[1].id == "id2"
        assert result[1].name == "tool2"


def test_cache_writer_set_file_name() -> None:
    """Test that set_file_name() updates the filename."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_writer = CacheWriter(cache_dir=temp_dir, file_name="original.json")

        cache_writer.set_file_name("new_name")
        assert cache_writer.file_name == "new_name.json"

        cache_writer.set_file_name("another.json")
        assert cache_writer.file_name == "another.json"


def test_cache_writer_generate_resets_after_writing() -> None:
    """Test that generate() calls reset() after writing the file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)
        cache_writer = CacheWriter(cache_dir=str(cache_dir), file_name="test.json")

        cache_writer.messages = [
            ToolUseBlockParam(
                id="id1",
                name="tool1",
                input={},
                type="tool_use",
            )
        ]

        cache_writer.generate()

        # After generate, messages should be empty
        assert cache_writer.messages == []
