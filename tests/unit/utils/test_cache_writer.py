"""Unit tests for CacheWriter utility."""

import json
import tempfile
from pathlib import Path
from typing import Any

from askui.models.shared.agent_message_param import MessageParam, ToolUseBlockParam
from askui.models.shared.agent_on_message_cb import OnMessageCbParam
from askui.models.shared.settings import CacheFile, CacheWriterSettings
from askui.utils.caching.cache_writer import CacheWriter


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
    """Test that generate() writes messages to a JSON file in v0.1 format."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)
        cache_writer = CacheWriter(
            cache_dir=str(cache_dir),
            file_name="output.json",
            cache_writer_settings=CacheWriterSettings(
                placeholder_identification_strategy="preset"
            ),
        )

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

        # Verify file content (v0.1 format)
        with cache_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Check v0.1 structure
        assert "metadata" in data
        assert "trajectory" in data
        assert "placeholders" in data

        # Check metadata
        assert data["metadata"]["version"] == "0.1"
        assert "created_at" in data["metadata"]
        assert data["metadata"]["execution_attempts"] == 0
        assert data["metadata"]["is_valid"] is True

        # Check trajectory
        assert len(data["trajectory"]) == 2
        assert data["trajectory"][0]["id"] == "id1"
        assert data["trajectory"][0]["name"] == "tool1"
        assert data["trajectory"][1]["id"] == "id2"
        assert data["trajectory"][1]["name"] == "tool2"


def test_cache_writer_generate_auto_names_file() -> None:
    """Test that generate() auto-generates filename if not provided."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)
        cache_writer = CacheWriter(
            cache_dir=str(cache_dir),
            file_name="",
            cache_writer_settings=CacheWriterSettings(
                placeholder_identification_strategy="preset"
            ),
        )

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


def test_cache_writer_read_cache_file_v1() -> None:
    """Test backward compatibility: read_cache_file() loads v0.0 format."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file_path = Path(temp_dir) / "test_cache.json"

        # Create a v0.0 cache file (just a list)
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

        with cache_file_path.open("w", encoding="utf-8") as f:
            json.dump(trajectory, f)

        # Read cache file
        result = CacheWriter.read_cache_file(cache_file_path)

        # Should return CacheFile with migrated v0.0 data (now v0.1)
        assert isinstance(result, CacheFile)
        assert result.metadata.version == "0.1"  # Migrated from v0.0 to v0.1
        assert len(result.trajectory) == 2
        assert isinstance(result.trajectory[0], ToolUseBlockParam)
        assert result.trajectory[0].id == "id1"
        assert result.trajectory[0].name == "tool1"
        assert isinstance(result.trajectory[1], ToolUseBlockParam)
        assert result.trajectory[1].id == "id2"
        assert result.trajectory[1].name == "tool2"


def test_cache_writer_read_cache_file_v2() -> None:
    """Test that read_cache_file() loads v0.1 format correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file_path = Path(temp_dir) / "test_cache_v2.json"

        # Create a v0.1 cache file
        cache_data = {
            "metadata": {
                "version": "0.1",
                "created_at": "2025-12-11T10:00:00Z",
                "last_executed_at": None,
                "execution_attempts": 0,
                "failures": [],
                "is_valid": True,
                "invalidation_reason": None,
            },
            "trajectory": [
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
            ],
            "placeholders": {"current_date": "Current date in YYYY-MM-DD format"},
        }

        with cache_file_path.open("w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        # Read cache file
        result = CacheWriter.read_cache_file(cache_file_path)

        # Should return CacheFile
        assert isinstance(result, CacheFile)
        assert result.metadata.version == "0.1"
        assert result.metadata.is_valid is True
        assert len(result.trajectory) == 2
        assert result.trajectory[0].id == "id1"
        assert result.trajectory[1].id == "id2"
        assert "current_date" in result.placeholders


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
        cache_writer = CacheWriter(
            cache_dir=str(cache_dir),
            file_name="test.json",
            cache_writer_settings=CacheWriterSettings(
                placeholder_identification_strategy="preset"
            ),
        )

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


def test_cache_writer_detects_and_stores_placeholders() -> None:
    """Test that CacheWriter detects placeholders and stores them in metadata."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)
        cache_writer = CacheWriter(
            cache_dir=str(cache_dir),
            file_name="test.json",
            cache_writer_settings=CacheWriterSettings(
                placeholder_identification_strategy="preset"
            ),
        )

        # Add tool use blocks with placeholders
        cache_writer.messages = [
            ToolUseBlockParam(
                id="id1",
                name="computer",
                input={"action": "type", "text": "Today is {{current_date}}"},
                type="tool_use",
            ),
            ToolUseBlockParam(
                id="id2",
                name="computer",
                input={"action": "type", "text": "User: {{user_name}}"},
                type="tool_use",
            ),
        ]

        cache_writer.generate()

        # Read back the cache file
        cache_file = cache_dir / "test.json"
        with cache_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Verify placeholders were detected and stored
        assert "placeholders" in data
        assert "current_date" in data["placeholders"]
        assert "user_name" in data["placeholders"]
        assert len(data["placeholders"]) == 2


def test_cache_writer_empty_placeholders_when_none_found() -> None:
    """Test that placeholders dict is empty when no placeholders exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)
        cache_writer = CacheWriter(
            cache_dir=str(cache_dir),
            file_name="test.json",
            cache_writer_settings=CacheWriterSettings(
                placeholder_identification_strategy="preset"
            ),
        )

        # Add tool use blocks without placeholders
        cache_writer.messages = [
            ToolUseBlockParam(
                id="id1",
                name="computer",
                input={"action": "click", "coordinate": [100, 200]},
                type="tool_use",
            )
        ]

        cache_writer.generate()

        # Read back the cache file
        cache_file = cache_dir / "test.json"
        with cache_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Verify placeholders dict is empty
        assert "placeholders" in data
        assert data["placeholders"] == {}
