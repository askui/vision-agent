"""Unit tests for caching tools."""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

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
            "cache_parameters": {},
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
            "cache_parameters": {},
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


def test_retrieve_caches_filters_invalid_by_default(tmp_path: Path) -> None:
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
        "cache_parameters": {},
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
        "cache_parameters": {},
    }
    with invalid_cache.open("w") as f:
        json.dump(invalid_data, f)

    tool = RetrieveCachedTestExecutions(cache_dir=str(cache_dir))

    # Should only return valid cache
    results = tool()
    assert len(results) == 1
    assert str(valid_cache) in results[0]
    assert str(invalid_cache) not in "".join(results)


def test_retrieve_caches_includes_invalid_when_requested(tmp_path: Path) -> None:
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
        "cache_parameters": {},
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
        "cache_parameters": {},
    }
    with invalid_cache.open("w") as f:
        json.dump(invalid_data, f)

    tool = RetrieveCachedTestExecutions(cache_dir=str(cache_dir))

    # Should return both caches when include_invalid=True
    results = tool(include_invalid=True)
    assert len(results) == 2


# ============================================================================
# ExecuteCachedTrajectory Tests (simplified for new architecture)
# ============================================================================
# The tool now only checks if file exists and returns success/error message.
# All validation is done by CacheExecutor speaker, not the tool.


def test_execute_cached_execution_initializes_with_toolbox() -> None:
    """Test that ExecuteCachedTrajectory can be initialized with toolbox."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    tool = ExecuteCachedTrajectory(toolbox=mock_toolbox)
    assert tool.name == "execute_cached_executions_tool"
    assert tool._toolbox is mock_toolbox  # noqa: SLF001


def test_execute_cached_execution_returns_error_when_file_not_found() -> None:
    """Test that ExecuteCachedTrajectory returns error message if file doesn't exist."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    tool = ExecuteCachedTrajectory(toolbox=mock_toolbox)

    result = tool(trajectory_file="/non/existent/file.json")

    # Should return error message string
    assert isinstance(result, str)
    assert "Trajectory file not found" in result


def test_execute_cached_execution_returns_success_when_file_exists() -> None:
    """Test that ExecuteCachedTrajectory returns success message when file exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        # Create a simple cache file (content doesn't matter for this test)
        cache_data = {
            "metadata": {
                "version": "0.1",
                "created_at": datetime.now(tz=timezone.utc).isoformat(),
                "execution_attempts": 0,
                "failures": [],
                "is_valid": True,
            },
            "trajectory": [],
            "cache_parameters": {},
        }

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        mock_toolbox = MagicMock(spec=ToolCollection)
        tool = ExecuteCachedTrajectory(toolbox=mock_toolbox)

        result = tool(trajectory_file=str(cache_file))

        # Should return success message
        assert isinstance(result, str)
        assert "✓ Requesting cache execution" in result
        assert "test_trajectory.json" in result


def test_execute_cached_execution_initializes_with_default_settings() -> None:
    """Test that ExecuteCachedTrajectory uses default settings when none provided."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    tool = ExecuteCachedTrajectory(toolbox=mock_toolbox)

    # Should have default settings initialized
    assert hasattr(tool, "_settings")
    assert tool._settings.delay_time_between_action == 0.5  # noqa: SLF001


def test_execute_cached_execution_initializes_with_custom_settings() -> None:
    """Test that ExecuteCachedTrajectory accepts custom settings."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    custom_settings = CachedExecutionToolSettings(delay_time_between_action=1.0)
    tool = ExecuteCachedTrajectory(toolbox=mock_toolbox, settings=custom_settings)

    # Should have custom settings initialized
    assert hasattr(tool, "_settings")
    assert tool._settings.delay_time_between_action == 1.0  # noqa: SLF001


def test_execute_cached_execution_accepts_parameters() -> None:
    """Test that ExecuteCachedTrajectory accepts parameter values."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        # Create a cache file with parameters
        cache_data = {
            "metadata": {
                "version": "0.1",
                "created_at": "2025-12-11T10:00:00Z",
                "execution_attempts": 0,
                "failures": [],
                "is_valid": True,
            },
            "trajectory": [
                {
                    "id": "tool1",
                    "name": "type_tool",
                    "input": {"text": "Today is {{current_date}}"},
                    "type": "tool_use",
                },
            ],
            "cache_parameters": {
                "current_date": "Current date",
            },
        }

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        mock_toolbox = MagicMock(spec=ToolCollection)
        tool = ExecuteCachedTrajectory(toolbox=mock_toolbox)

        # Tool should accept parameter_values (validation happens in CacheExecutor)
        result = tool(
            trajectory_file=str(cache_file),
            parameter_values={"current_date": "2025-12-11"},
        )

        # Should return success
        assert isinstance(result, str)
        assert "✓ Requesting cache execution" in result


def test_execute_cached_execution_accepts_start_from_step_index() -> None:
    """Test that ExecuteCachedTrajectory accepts start_from_step_index parameter."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        # Create a trajectory with multiple steps
        cache_data = {
            "metadata": {
                "version": "0.1",
                "created_at": datetime.now(tz=timezone.utc).isoformat(),
                "execution_attempts": 0,
                "failures": [],
                "is_valid": True,
            },
            "trajectory": [
                {"id": "1", "name": "tool1", "input": {}, "type": "tool_use"},
                {"id": "2", "name": "tool2", "input": {}, "type": "tool_use"},
                {"id": "3", "name": "tool3", "input": {}, "type": "tool_use"},
            ],
            "cache_parameters": {},
        }

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        mock_toolbox = MagicMock(spec=ToolCollection)
        tool = ExecuteCachedTrajectory(toolbox=mock_toolbox)

        # Tool should accept start_from_step_index (validation happens in CacheExecutor)
        result = tool(trajectory_file=str(cache_file), start_from_step_index=2)

        # Should return success
        assert isinstance(result, str)
        assert "✓ Requesting cache execution" in result


# ============================================================================
# InspectCacheMetadata Tests (unchanged from before)
# ============================================================================


def test_inspect_cache_metadata_shows_basic_info(tmp_path: Path) -> None:
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
        "cache_parameters": {"current_date": "{{current_date}}"},
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
    assert "Parameters: 1" in result
    assert "current_date" in result


def test_inspect_cache_metadata_shows_failures(tmp_path: Path) -> None:
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
        "cache_parameters": {},
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


def test_inspect_cache_metadata_file_not_found() -> None:
    """Test that InspectCacheMetadata handles missing files."""
    from askui.tools.caching_tools import InspectCacheMetadata

    tool = InspectCacheMetadata()
    result = tool(trajectory_file="/nonexistent/file.json")

    assert "Trajectory file not found" in result
