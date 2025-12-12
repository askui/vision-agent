"""Unit tests for caching tools."""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from askui.models.shared.agent import Agent
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.settings import CachedExecutionToolSettings
from askui.models.shared.tools import ToolCollection
from askui.tools.caching_tools import (
    ExecuteCachedTrajectory,
    RetrieveCachedTestExecutions,
)


# ============================================================================
# RetrieveCachedTestExecutions Tests (unchanged from before)
# ============================================================================


def test_retrieve_cached_test_executions_lists_json_files() -> None:
    """Test that RetrieveCachedTestExecutions lists all JSON files in cache dir."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)

        # Create valid cache files with v0.1 format
        cache_data = {
            "metadata": {
                "version": "0.1",
                "created_at": datetime.now(tz=timezone.utc).isoformat(),
                "execution_attempts": 0,
                "last_executed_at": None,
                "failures": [],
                "is_valid": True,
                "invalidation_reason": None,
            },
            "trajectory": [],
            "placeholders": {},
        }
        (cache_dir / "cache1.json").write_text(json.dumps(cache_data), encoding="utf-8")
        (cache_dir / "cache2.json").write_text(json.dumps(cache_data), encoding="utf-8")
        (cache_dir / "not_cache.txt").write_text("text", encoding="utf-8")

        tool = RetrieveCachedTestExecutions(cache_dir=str(cache_dir))
        result = tool()

        assert len(result) == 2
        assert any("cache1.json" in path for path in result)
        assert any("cache2.json" in path for path in result)
        assert not any("not_cache.txt" in path for path in result)


def test_retrieve_cached_test_executions_returns_empty_list_when_no_files() -> None:
    """Test that RetrieveCachedTestExecutions returns empty list when no files exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)

        tool = RetrieveCachedTestExecutions(cache_dir=str(cache_dir))
        result = tool()

        assert result == []


def test_retrieve_cached_test_executions_raises_error_when_dir_not_found() -> None:
    """Test that RetrieveCachedTestExecutions raises error if directory doesn't exist"""
    tool = RetrieveCachedTestExecutions(cache_dir="/non/existent/directory")

    with pytest.raises(FileNotFoundError, match="Trajectories directory not found"):
        tool()


def test_retrieve_cached_test_executions_respects_custom_format() -> None:
    """Test that RetrieveCachedTestExecutions respects custom file format."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)

        # Create valid cache files with different extensions
        cache_data = {
            "metadata": {
                "version": "0.1",
                "created_at": datetime.now(tz=timezone.utc).isoformat(),
                "execution_attempts": 0,
                "last_executed_at": None,
                "failures": [],
                "is_valid": True,
                "invalidation_reason": None,
            },
            "trajectory": [],
            "placeholders": {},
        }
        (cache_dir / "cache1.json").write_text(json.dumps(cache_data), encoding="utf-8")
        (cache_dir / "cache2.traj").write_text(json.dumps(cache_data), encoding="utf-8")

        # Default format (.json)
        tool_json = RetrieveCachedTestExecutions(
            cache_dir=str(cache_dir), trajectories_format=".json"
        )
        result_json = tool_json()
        assert len(result_json) == 1
        assert "cache1.json" in result_json[0]

        # Custom format (.traj)
        tool_traj = RetrieveCachedTestExecutions(
            cache_dir=str(cache_dir), trajectories_format=".traj"
        )
        result_traj = tool_traj()
        assert len(result_traj) == 1
        assert "cache2.traj" in result_traj[0]


def test_retrieve_caches_filters_invalid_by_default(tmp_path):
    """Test that RetrieveCachedTestExecutions filters out invalid caches by default."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # Create a valid cache
    valid_cache = cache_dir / "valid.json"
    valid_data = {
        "metadata": {
            "version": "0.1",
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "execution_attempts": 0,
            "failures": [],
            "is_valid": True,
            "invalidation_reason": None,
        },
        "trajectory": [],
        "placeholders": {},
    }
    with valid_cache.open("w") as f:
        json.dump(valid_data, f)

    # Create an invalid cache
    invalid_cache = cache_dir / "invalid.json"
    invalid_data = {
        "metadata": {
            "version": "0.1",
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "execution_attempts": 10,
            "failures": [],
            "is_valid": False,
            "invalidation_reason": "Too many failures",
        },
        "trajectory": [],
        "placeholders": {},
    }
    with invalid_cache.open("w") as f:
        json.dump(invalid_data, f)

    tool = RetrieveCachedTestExecutions(cache_dir=str(cache_dir))

    # Should only return valid cache
    results = tool()
    assert len(results) == 1
    assert str(valid_cache) in results
    assert str(invalid_cache) not in results


def test_retrieve_caches_includes_invalid_when_requested(tmp_path):
    """Test that RetrieveCachedTestExecutions includes invalid caches when requested."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # Create a valid cache
    valid_cache = cache_dir / "valid.json"
    valid_data = {
        "metadata": {
            "version": "0.1",
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "execution_attempts": 0,
            "failures": [],
            "is_valid": True,
            "invalidation_reason": None,
        },
        "trajectory": [],
        "placeholders": {},
    }
    with valid_cache.open("w") as f:
        json.dump(valid_data, f)

    # Create an invalid cache
    invalid_cache = cache_dir / "invalid.json"
    invalid_data = {
        "metadata": {
            "version": "0.1",
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "execution_attempts": 10,
            "failures": [],
            "is_valid": False,
            "invalidation_reason": "Too many failures",
        },
        "trajectory": [],
        "placeholders": {},
    }
    with invalid_cache.open("w") as f:
        json.dump(invalid_data, f)

    tool = RetrieveCachedTestExecutions(cache_dir=str(cache_dir))

    # Should return both caches when include_invalid=True
    results = tool(include_invalid=True)
    assert len(results) == 2


# ============================================================================
# ExecuteCachedTrajectory Tests (refactored for new behavior)
# ============================================================================


def test_execute_cached_execution_initializes_without_toolbox() -> None:
    """Test that ExecuteCachedTrajectory can be initialized without toolbox."""
    tool = ExecuteCachedTrajectory()
    assert tool.name == "execute_cached_executions_tool"
    assert tool._toolbox is None  # noqa: SLF001
    assert tool._agent is None  # noqa: SLF001


def test_execute_cached_execution_raises_error_without_toolbox_or_agent() -> None:
    """Test that ExecuteCachedTrajectory raises error when neither toolbox nor agent set."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test.json"
        cache_data = {
            "metadata": {
                "version": "0.1",
                "created_at": datetime.now(tz=timezone.utc).isoformat(),
                "execution_attempts": 0,
                "last_executed_at": None,
                "failures": [],
                "is_valid": True,
                "invalidation_reason": None,
            },
            "trajectory": [],
            "placeholders": {},
        }
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        tool = ExecuteCachedTrajectory()

        with pytest.raises(RuntimeError, match="Agent not set"):
            tool(trajectory_file=str(cache_file))


def test_execute_cached_execution_returns_error_when_file_not_found() -> None:
    """Test that ExecuteCachedTrajectory returns error message if file doesn't exist."""
    tool = ExecuteCachedTrajectory()
    mock_agent = MagicMock(spec=Agent)
    mock_agent._tool_collection = MagicMock(spec=ToolCollection)
    tool.set_agent(mock_agent)

    result = tool(trajectory_file="/non/existent/file.json")

    # New behavior: returns error message string instead of raising
    assert isinstance(result, str)
    assert "Trajectory file not found" in result


def test_execute_cached_execution_activates_cache_mode() -> None:
    """Test that ExecuteCachedTrajectory activates cache mode in the agent."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        # Create a trajectory file with v0.1 format
        cache_data = {
            "metadata": {
                "version": "0.1",
                "created_at": datetime.now(tz=timezone.utc).isoformat(),
                "execution_attempts": 0,
                "last_executed_at": None,
                "failures": [],
                "is_valid": True,
                "invalidation_reason": None,
            },
            "trajectory": [
                {
                    "id": "tool1",
                    "name": "click_tool",
                    "input": {"x": 100, "y": 200},
                    "type": "tool_use",
                },
                {
                    "id": "tool2",
                    "name": "type_tool",
                    "input": {"text": "hello"},
                    "type": "tool_use",
                },
            ],
            "placeholders": {},
        }

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        # Create mock agent with toolbox
        mock_messages_api = MagicMock(spec=MessagesApi)
        mock_agent = Agent(messages_api=mock_messages_api)
        mock_toolbox = MagicMock(spec=ToolCollection)
        mock_toolbox._tool_map = {}
        mock_agent._tool_collection = mock_toolbox  # noqa: SLF001

        # Create and configure tool
        tool = ExecuteCachedTrajectory()
        tool.set_agent(mock_agent)

        # Call the tool
        result = tool(trajectory_file=str(cache_file))

        # Verify return type is string
        assert isinstance(result, str)
        assert "✓ Cache execution mode activated" in result
        assert "2 cached steps" in result

        # Verify agent state was set
        assert mock_agent._executing_from_cache is True  # noqa: SLF001
        assert mock_agent._cache_executor is not None  # noqa: SLF001
        assert mock_agent._cache_file is not None  # noqa: SLF001
        assert mock_agent._cache_file_path == str(cache_file)  # noqa: SLF001


def test_execute_cached_execution_works_with_set_toolbox() -> None:
    """Test that ExecuteCachedTrajectory works with set_toolbox (legacy approach)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        cache_data = {
            "metadata": {
                "version": "0.1",
                "created_at": datetime.now(tz=timezone.utc).isoformat(),
                "execution_attempts": 0,
                "last_executed_at": None,
                "failures": [],
                "is_valid": True,
                "invalidation_reason": None,
            },
            "trajectory": [
                {
                    "id": "tool1",
                    "name": "test_tool",
                    "input": {},
                    "type": "tool_use",
                }
            ],
            "placeholders": {},
        }

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        # Create mock agent without toolbox
        mock_messages_api = MagicMock(spec=MessagesApi)
        mock_agent = Agent(messages_api=mock_messages_api)

        # Create tool and set toolbox directly
        tool = ExecuteCachedTrajectory()
        mock_toolbox = MagicMock(spec=ToolCollection)
        mock_toolbox._tool_map = {}
        tool.set_toolbox(mock_toolbox)
        tool.set_agent(mock_agent)

        result = tool(trajectory_file=str(cache_file))

        # Should succeed using the toolbox
        assert isinstance(result, str)
        assert "✓ Cache execution mode activated" in result


def test_execute_cached_execution_set_agent_and_toolbox() -> None:
    """Test that set_agent and set_toolbox properly set references."""
    tool = ExecuteCachedTrajectory()
    mock_agent = MagicMock(spec=Agent)
    mock_toolbox = MagicMock(spec=ToolCollection)

    tool.set_agent(mock_agent)
    tool.set_toolbox(mock_toolbox)

    assert tool._agent == mock_agent  # noqa: SLF001
    assert tool._toolbox == mock_toolbox  # noqa: SLF001


def test_execute_cached_execution_initializes_with_default_settings() -> None:
    """Test that ExecuteCachedTrajectory uses default settings when none provided."""
    tool = ExecuteCachedTrajectory()

    # Should have default settings initialized
    assert hasattr(tool, "_settings")
    assert tool._settings.delay_time_between_action == 0.5  # noqa: SLF001


def test_execute_cached_execution_initializes_with_custom_settings() -> None:
    """Test that ExecuteCachedTrajectory accepts custom settings."""
    custom_settings = CachedExecutionToolSettings(delay_time_between_action=1.0)
    tool = ExecuteCachedTrajectory(settings=custom_settings)

    # Should have custom settings initialized
    assert hasattr(tool, "_settings")
    assert tool._settings.delay_time_between_action == 1.0  # noqa: SLF001


def test_execute_cached_execution_with_placeholders() -> None:
    """Test that ExecuteCachedTrajectory validates placeholders."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        # Create a v0.1 cache file with placeholders
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
                    "id": "tool1",
                    "name": "type_tool",
                    "input": {"text": "Today is {{current_date}}"},
                    "type": "tool_use",
                },
            ],
            "placeholders": {
                "current_date": "Current date",
            },
        }

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        # Create mock agent
        mock_messages_api = MagicMock(spec=MessagesApi)
        mock_agent = Agent(messages_api=mock_messages_api)
        mock_toolbox = MagicMock(spec=ToolCollection)
        mock_toolbox._tool_map = {}
        mock_agent._tool_collection = mock_toolbox  # noqa: SLF001

        tool = ExecuteCachedTrajectory()
        tool.set_agent(mock_agent)

        result = tool(
            trajectory_file=str(cache_file),
            placeholder_values={"current_date": "2025-12-11"},
        )

        # Verify success
        assert isinstance(result, str)
        assert "✓ Cache execution mode activated" in result
        assert "1 placeholder value" in result


def test_execute_cached_execution_missing_placeholders() -> None:
    """Test that ExecuteCachedTrajectory returns error for missing placeholders."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        # Create a v0.1 cache file with placeholders
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
                    "id": "tool1",
                    "name": "type_tool",
                    "input": {"text": "Date: {{current_date}}, User: {{user_name}}"},
                    "type": "tool_use",
                }
            ],
            "placeholders": {
                "current_date": "Current date",
                "user_name": "User name",
            },
        }

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        # Create mock agent
        mock_messages_api = MagicMock(spec=MessagesApi)
        mock_agent = Agent(messages_api=mock_messages_api)
        mock_toolbox = MagicMock(spec=ToolCollection)
        mock_agent._tool_collection = mock_toolbox  # noqa: SLF001

        tool = ExecuteCachedTrajectory()
        tool.set_agent(mock_agent)

        result = tool(trajectory_file=str(cache_file))

        # Verify error message
        assert isinstance(result, str)
        assert "Missing required placeholder values" in result
        assert "current_date" in result
        assert "user_name" in result


def test_execute_cached_execution_no_placeholders_backward_compat() -> None:
    """Test backward compatibility: trajectories without placeholders work fine."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        # Create a v0.0 cache file (old format, no placeholders)
        trajectory: list[dict[str, Any]] = [
            {
                "id": "tool1",
                "name": "click_tool",
                "input": {"x": 100, "y": 200},
                "type": "tool_use",
            }
        ]

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(trajectory, f)

        # Create mock agent
        mock_messages_api = MagicMock(spec=MessagesApi)
        mock_agent = Agent(messages_api=mock_messages_api)
        mock_toolbox = MagicMock(spec=ToolCollection)
        mock_toolbox._tool_map = {}
        mock_agent._tool_collection = mock_toolbox  # noqa: SLF001

        tool = ExecuteCachedTrajectory()
        tool.set_agent(mock_agent)

        result = tool(trajectory_file=str(cache_file))

        # Verify success
        assert isinstance(result, str)
        assert "✓ Cache execution mode activated" in result


def test_continue_cached_trajectory_from_middle() -> None:
    """Test continuing execution from middle of trajectory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        # Create a trajectory with 5 steps
        cache_data = {
            "metadata": {
                "version": "0.1",
                "created_at": datetime.now(tz=timezone.utc).isoformat(),
                "execution_attempts": 0,
                "last_executed_at": None,
                "failures": [],
                "is_valid": True,
                "invalidation_reason": None,
            },
            "trajectory": [
                {"id": "1", "name": "tool1", "input": {}, "type": "tool_use"},
                {"id": "2", "name": "tool2", "input": {}, "type": "tool_use"},
                {"id": "3", "name": "tool3", "input": {}, "type": "tool_use"},
                {"id": "4", "name": "tool4", "input": {}, "type": "tool_use"},
                {"id": "5", "name": "tool5", "input": {}, "type": "tool_use"},
            ],
            "placeholders": {},
        }

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        # Create mock agent
        mock_messages_api = MagicMock(spec=MessagesApi)
        mock_agent = Agent(messages_api=mock_messages_api)
        mock_toolbox = MagicMock(spec=ToolCollection)
        mock_toolbox._tool_map = {}
        mock_agent._tool_collection = mock_toolbox  # noqa: SLF001

        tool = ExecuteCachedTrajectory()
        tool.set_agent(mock_agent)

        result = tool(trajectory_file=str(cache_file), start_from_step_index=2)

        # Verify success message
        assert isinstance(result, str)
        assert "✓ Cache execution mode activated" in result
        assert "resuming from step 2" in result
        assert "3 remaining cached steps" in result


def test_continue_cached_trajectory_invalid_step_index_negative() -> None:
    """Test that negative step index returns error."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        cache_data = {
            "metadata": {
                "version": "0.1",
                "created_at": datetime.now(tz=timezone.utc).isoformat(),
                "execution_attempts": 0,
                "last_executed_at": None,
                "failures": [],
                "is_valid": True,
                "invalidation_reason": None,
            },
            "trajectory": [
                {"id": "1", "name": "tool1", "input": {}, "type": "tool_use"},
            ],
            "placeholders": {},
        }

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        mock_messages_api = MagicMock(spec=MessagesApi)
        mock_agent = Agent(messages_api=mock_messages_api)
        mock_toolbox = MagicMock(spec=ToolCollection)
        mock_toolbox._tool_map = {}
        mock_agent._tool_collection = mock_toolbox  # noqa: SLF001

        tool = ExecuteCachedTrajectory()
        tool.set_agent(mock_agent)

        result = tool(trajectory_file=str(cache_file), start_from_step_index=-1)

        # Verify error message
        assert isinstance(result, str)
        assert "Invalid start_from_step_index" in result


def test_continue_cached_trajectory_invalid_step_index_too_large() -> None:
    """Test that step index beyond trajectory length returns error."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        cache_data = {
            "metadata": {
                "version": "0.1",
                "created_at": datetime.now(tz=timezone.utc).isoformat(),
                "execution_attempts": 0,
                "last_executed_at": None,
                "failures": [],
                "is_valid": True,
                "invalidation_reason": None,
            },
            "trajectory": [
                {"id": "1", "name": "tool1", "input": {}, "type": "tool_use"},
                {"id": "2", "name": "tool2", "input": {}, "type": "tool_use"},
            ],
            "placeholders": {},
        }

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        mock_messages_api = MagicMock(spec=MessagesApi)
        mock_agent = Agent(messages_api=mock_messages_api)
        mock_toolbox = MagicMock(spec=ToolCollection)
        mock_toolbox._tool_map = {}
        mock_agent._tool_collection = mock_toolbox  # noqa: SLF001

        tool = ExecuteCachedTrajectory()
        tool.set_agent(mock_agent)

        result = tool(trajectory_file=str(cache_file), start_from_step_index=5)

        # Verify error message
        assert isinstance(result, str)
        assert "Invalid start_from_step_index" in result
        assert "valid indices: 0-1" in result


def test_continue_cached_trajectory_with_placeholders() -> None:
    """Test continuing execution with placeholder substitution."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        # Create a v0.1 cache file with placeholders
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
                    "id": "1",
                    "name": "tool1",
                    "input": {"text": "Step 1"},
                    "type": "tool_use",
                },
                {
                    "id": "2",
                    "name": "tool2",
                    "input": {"text": "Date: {{current_date}}"},
                    "type": "tool_use",
                },
                {
                    "id": "3",
                    "name": "tool3",
                    "input": {"text": "User: {{user_name}}"},
                    "type": "tool_use",
                },
            ],
            "placeholders": {
                "current_date": "Current date",
                "user_name": "User name",
            },
        }

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        # Create mock agent
        mock_messages_api = MagicMock(spec=MessagesApi)
        mock_agent = Agent(messages_api=mock_messages_api)
        mock_toolbox = MagicMock(spec=ToolCollection)
        mock_toolbox._tool_map = {}
        mock_agent._tool_collection = mock_toolbox  # noqa: SLF001

        tool = ExecuteCachedTrajectory()
        tool.set_agent(mock_agent)

        result = tool(
            trajectory_file=str(cache_file),
            start_from_step_index=1,
            placeholder_values={"current_date": "2025-12-11", "user_name": "Alice"},
        )

        # Verify success
        assert isinstance(result, str)
        assert "✓ Cache execution mode activated" in result
        assert "resuming from step 1" in result


def test_execute_cached_trajectory_warns_if_invalid(tmp_path, caplog):
    """Test that ExecuteCachedTrajectory warns when activating with invalid cache."""
    import logging

    caplog.set_level(logging.WARNING)

    cache_file = tmp_path / "test.json"
    cache_data = {
        "metadata": {
            "version": "0.1",
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "execution_attempts": 10,
            "last_executed_at": None,
            "failures": [],
            "is_valid": False,
            "invalidation_reason": "Cache marked invalid for testing",
        },
        "trajectory": [
            {"id": "1", "name": "click", "input": {"x": 100}, "type": "tool_use"},
        ],
        "placeholders": {},
    }
    with cache_file.open("w") as f:
        json.dump(cache_data, f)

    # Create mock agent
    mock_messages_api = MagicMock(spec=MessagesApi)
    mock_agent = Agent(messages_api=mock_messages_api)
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox._tool_map = {}
    mock_agent._tool_collection = mock_toolbox  # noqa: SLF001

    tool = ExecuteCachedTrajectory()
    tool.set_agent(mock_agent)

    result = tool(trajectory_file=str(cache_file))

    # Should still activate but log warning
    assert isinstance(result, str)
    assert "✓ Cache execution mode activated" in result

    # Verify warning was logged
    assert any("WARNING" in record.levelname for record in caplog.records)
    assert any("invalid cache" in record.message.lower() for record in caplog.records)


# ============================================================================
# InspectCacheMetadata Tests (unchanged from before)
# ============================================================================


def test_inspect_cache_metadata_shows_basic_info(tmp_path):
    """Test that InspectCacheMetadata displays basic cache information."""
    from askui.tools.caching_tools import InspectCacheMetadata

    cache_file = tmp_path / "test.json"
    cache_data = {
        "metadata": {
            "version": "0.1",
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "execution_attempts": 5,
            "last_executed_at": datetime.now(tz=timezone.utc).isoformat(),
            "failures": [],
            "is_valid": True,
            "invalidation_reason": None,
        },
        "trajectory": [
            {"id": "1", "name": "click", "input": {"x": 100}, "type": "tool_use"},
            {"id": "2", "name": "type", "input": {"text": "test"}, "type": "tool_use"},
        ],
        "placeholders": {"current_date": "{{current_date}}"},
    }
    with cache_file.open("w") as f:
        json.dump(cache_data, f)

    tool = InspectCacheMetadata()
    result = tool(trajectory_file=str(cache_file))

    # Verify output contains key information
    assert "=== Cache Metadata ===" in result
    assert "Version: 0.1" in result
    assert "Total Execution Attempts: 5" in result
    assert "Is Valid: True" in result
    assert "Total Steps: 2" in result
    assert "Placeholders: 1" in result
    assert "current_date" in result


def test_inspect_cache_metadata_shows_failures(tmp_path):
    """Test that InspectCacheMetadata displays failure history."""
    from askui.tools.caching_tools import InspectCacheMetadata

    cache_file = tmp_path / "test.json"
    cache_data = {
        "metadata": {
            "version": "0.1",
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "execution_attempts": 3,
            "last_executed_at": None,
            "failures": [
                {
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                    "step_index": 1,
                    "error_message": "Click failed",
                    "failure_count_at_step": 1,
                },
                {
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                    "step_index": 1,
                    "error_message": "Click failed again",
                    "failure_count_at_step": 2,
                },
            ],
            "is_valid": False,
            "invalidation_reason": "Too many failures at step 1",
        },
        "trajectory": [
            {"id": "1", "name": "click", "input": {"x": 100}, "type": "tool_use"},
        ],
        "placeholders": {},
    }
    with cache_file.open("w") as f:
        json.dump(cache_data, f)

    tool = InspectCacheMetadata()
    result = tool(trajectory_file=str(cache_file))

    # Verify failure information
    assert "--- Failure History ---" in result
    assert "Failure 1:" in result
    assert "Failure 2:" in result
    assert "Step Index: 1" in result
    assert "Click failed" in result
    assert "Is Valid: False" in result
    assert "Invalidation Reason: Too many failures at step 1" in result


def test_inspect_cache_metadata_file_not_found():
    """Test that InspectCacheMetadata handles missing files."""
    from askui.tools.caching_tools import InspectCacheMetadata

    tool = InspectCacheMetadata()
    result = tool(trajectory_file="/nonexistent/file.json")

    assert "Trajectory file not found" in result


# ============================================================================
# RevalidateCache Tests (unchanged from before)
# ============================================================================


def test_revalidate_cache_marks_invalid_as_valid(tmp_path):
    """Test that RevalidateCache marks invalid cache as valid."""
    from askui.tools.caching_tools import RevalidateCache

    cache_file = tmp_path / "test.json"
    cache_data = {
        "metadata": {
            "version": "0.1",
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "execution_attempts": 3,
            "last_executed_at": None,
            "failures": [
                {
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                    "step_index": 1,
                    "error_message": "Error",
                    "failure_count_at_step": 1,
                }
            ],
            "is_valid": False,
            "invalidation_reason": "Manual invalidation",
        },
        "trajectory": [
            {"id": "1", "name": "click", "input": {"x": 100}, "type": "tool_use"},
        ],
        "placeholders": {},
    }
    with cache_file.open("w") as f:
        json.dump(cache_data, f)

    tool = RevalidateCache()
    result = tool(trajectory_file=str(cache_file))

    # Verify success message
    assert "Successfully revalidated" in result
    assert "Manual invalidation" in result

    # Read updated cache file
    with cache_file.open("r") as f:
        updated_data = json.load(f)

    # Verify cache is now valid
    assert updated_data["metadata"]["is_valid"] is True
    assert updated_data["metadata"]["invalidation_reason"] is None
    # Failure history should still be there
    assert len(updated_data["metadata"]["failures"]) == 1


def test_revalidate_cache_already_valid(tmp_path):
    """Test that RevalidateCache handles already valid cache."""
    from askui.tools.caching_tools import RevalidateCache

    cache_file = tmp_path / "test.json"
    cache_data = {
        "metadata": {
            "version": "0.1",
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "execution_attempts": 0,
            "last_executed_at": None,
            "failures": [],
            "is_valid": True,
            "invalidation_reason": None,
        },
        "trajectory": [
            {"id": "1", "name": "click", "input": {"x": 100}, "type": "tool_use"},
        ],
        "placeholders": {},
    }
    with cache_file.open("w") as f:
        json.dump(cache_data, f)

    tool = RevalidateCache()
    result = tool(trajectory_file=str(cache_file))

    # Verify message indicates already valid
    assert "already valid" in result
    assert "No changes made" in result


def test_revalidate_cache_file_not_found():
    """Test that RevalidateCache handles missing files."""
    from askui.tools.caching_tools import RevalidateCache

    tool = RevalidateCache()
    result = tool(trajectory_file="/nonexistent/file.json")

    assert "Trajectory file not found" in result


# ============================================================================
# InvalidateCache Tests (unchanged from before)
# ============================================================================


def test_invalidate_cache_marks_valid_as_invalid(tmp_path):
    """Test that InvalidateCache marks valid cache as invalid."""
    from askui.tools.caching_tools import InvalidateCache

    cache_file = tmp_path / "test.json"
    cache_data = {
        "metadata": {
            "version": "0.1",
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "execution_attempts": 2,
            "last_executed_at": datetime.now(tz=timezone.utc).isoformat(),
            "failures": [],
            "is_valid": True,
            "invalidation_reason": None,
        },
        "trajectory": [
            {"id": "1", "name": "click", "input": {"x": 100}, "type": "tool_use"},
        ],
        "placeholders": {},
    }
    with cache_file.open("w") as f:
        json.dump(cache_data, f)

    tool = InvalidateCache()
    result = tool(trajectory_file=str(cache_file), reason="UI changed - button moved")

    # Verify success message
    assert "Successfully invalidated" in result
    assert "UI changed - button moved" in result

    # Read updated cache file
    with cache_file.open("r") as f:
        updated_data = json.load(f)

    # Verify cache is now invalid
    assert updated_data["metadata"]["is_valid"] is False
    assert (
        updated_data["metadata"]["invalidation_reason"] == "UI changed - button moved"
    )
    # Other metadata should be preserved
    assert updated_data["metadata"]["execution_attempts"] == 2


def test_invalidate_cache_updates_reason_if_already_invalid(tmp_path):
    """Test that InvalidateCache updates reason if already invalid."""
    from askui.tools.caching_tools import InvalidateCache

    cache_file = tmp_path / "test.json"
    cache_data = {
        "metadata": {
            "version": "0.1",
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "execution_attempts": 0,
            "last_executed_at": None,
            "failures": [],
            "is_valid": False,
            "invalidation_reason": "Old reason",
        },
        "trajectory": [
            {"id": "1", "name": "click", "input": {"x": 100}, "type": "tool_use"},
        ],
        "placeholders": {},
    }
    with cache_file.open("w") as f:
        json.dump(cache_data, f)

    tool = InvalidateCache()
    result = tool(trajectory_file=str(cache_file), reason="New reason")

    # Verify message indicates update
    assert "already invalid" in result
    assert "Updated invalidation reason to: New reason" in result

    # Read updated cache file
    with cache_file.open("r") as f:
        updated_data = json.load(f)

    # Verify reason was updated
    assert updated_data["metadata"]["invalidation_reason"] == "New reason"


def test_invalidate_cache_file_not_found():
    """Test that InvalidateCache handles missing files."""
    from askui.tools.caching_tools import InvalidateCache

    tool = InvalidateCache()
    result = tool(trajectory_file="/nonexistent/file.json", reason="Test")

    assert "Trajectory file not found" in result
