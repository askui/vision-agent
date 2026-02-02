"""Unit tests for caching tools."""

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from askui.models.shared.settings import CachedExecutionToolSettings
from askui.models.shared.tools import ToolCollection
from askui.tools.caching_tools import (
    ExecuteCachedTrajectory,
    RetrieveCachedTestExecutions,
)


def test_retrieve_cached_test_executions_lists_json_files() -> None:
    """Test that RetrieveCachedTestExecutions lists all JSON files in cache dir."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir)

        # Create some cache files
        (cache_dir / "cache1.json").write_text("{}", encoding="utf-8")
        (cache_dir / "cache2.json").write_text("{}", encoding="utf-8")
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

        # Create files with different extensions
        (cache_dir / "cache1.json").write_text("{}", encoding="utf-8")
        (cache_dir / "cache2.traj").write_text("{}", encoding="utf-8")

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


def test_execute_cached_execution_initializes_without_toolbox() -> None:
    """Test that ExecuteCachedExecution can be initialized without toolbox."""
    tool = ExecuteCachedTrajectory()
    assert tool.name.startswith("execute_cached_executions_tool")


def test_execute_cached_execution_raises_error_without_toolbox() -> None:
    """Test that ExecuteCachedExecution raises error when toolbox not set."""
    tool = ExecuteCachedTrajectory()

    with pytest.raises(RuntimeError, match="Toolbox not set"):
        tool(trajectory_file="some_file.json")


def test_execute_cached_execution_raises_error_when_file_not_found() -> None:
    """Test that ExecuteCachedExecution raises error if trajectory file doesn't exist"""
    tool = ExecuteCachedTrajectory()
    mock_toolbox = MagicMock(spec=ToolCollection)
    tool.set_toolbox(mock_toolbox)

    with pytest.raises(FileNotFoundError, match="Trajectory file not found"):
        tool(trajectory_file="/non/existent/file.json")


def test_execute_cached_execution_executes_trajectory() -> None:
    """Test that ExecuteCachedExecution executes tools from trajectory file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        # Create a trajectory file
        trajectory: list[dict[str, Any]] = [
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
        ]

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(trajectory, f)

        # Execute the trajectory
        tool = ExecuteCachedTrajectory()
        mock_toolbox = MagicMock(spec=ToolCollection)
        tool.set_toolbox(mock_toolbox)

        result = tool(trajectory_file=str(cache_file))

        # Verify success message
        assert "Successfully executed trajectory" in result
        # Verify toolbox.run was called for each tool (2 calls)
        assert mock_toolbox.run.call_count == 2


def test_execute_cached_execution_skips_screenshot_tools() -> None:
    """Test that ExecuteCachedExecution skips screenshot-related tools."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        # Create a trajectory with screenshot tools
        trajectory: list[dict[str, Any]] = [
            {
                "id": "tool1",
                "name": "screenshot",
                "input": {},
                "type": "tool_use",
            },
            {
                "id": "tool2",
                "name": "click_tool",
                "input": {"x": 100, "y": 200},
                "type": "tool_use",
            },
            {
                "id": "tool3",
                "name": "retrieve_available_trajectories_tool",
                "input": {},
                "type": "tool_use",
            },
        ]

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(trajectory, f)

        # Execute the trajectory
        tool = ExecuteCachedTrajectory()
        mock_toolbox = MagicMock(spec=ToolCollection)
        tool.set_toolbox(mock_toolbox)

        result = tool(trajectory_file=str(cache_file))

        # Verify only click_tool was executed (screenshot and retrieve tools skipped)
        assert mock_toolbox.run.call_count == 1
        assert "Successfully executed trajectory" in result


def test_execute_cached_execution_handles_errors_gracefully() -> None:
    """Test that ExecuteCachedExecution handles errors during execution."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        # Create a trajectory
        trajectory: list[dict[str, Any]] = [
            {
                "id": "tool1",
                "name": "failing_tool",
                "input": {},
                "type": "tool_use",
            },
        ]

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(trajectory, f)

        # Execute the trajectory with a failing tool
        tool = ExecuteCachedTrajectory()
        mock_toolbox = MagicMock(spec=ToolCollection)
        mock_toolbox.run.side_effect = Exception("Tool execution failed")
        tool.set_toolbox(mock_toolbox)

        result = tool(trajectory_file=str(cache_file))

        # Verify error message
        assert "error occured" in result.lower()
        assert "verify the UI state" in result


def test_execute_cached_execution_set_toolbox() -> None:
    """Test that set_toolbox properly sets the toolbox reference."""
    tool = ExecuteCachedTrajectory()
    mock_toolbox = MagicMock(spec=ToolCollection)

    tool.set_toolbox(mock_toolbox)

    # After setting toolbox, should be able to access it
    assert hasattr(tool, "_toolbox")
    assert tool._toolbox == mock_toolbox


def test_execute_cached_execution_initializes_with_default_settings() -> None:
    """Test that ExecuteCachedTrajectory uses default settings when none provided."""
    tool = ExecuteCachedTrajectory()

    # Should have default settings initialized
    assert hasattr(tool, "_settings")


def test_execute_cached_execution_initializes_with_custom_settings() -> None:
    """Test that ExecuteCachedTrajectory accepts custom settings."""
    custom_settings = CachedExecutionToolSettings(delay_time_between_action=1.0)
    tool = ExecuteCachedTrajectory(settings=custom_settings)

    # Should have custom settings initialized
    assert hasattr(tool, "_settings")


def test_execute_cached_execution_uses_delay_time_between_actions() -> None:
    """Test that ExecuteCachedTrajectory uses the configured delay time."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        # Create a trajectory with 3 actions
        trajectory: list[dict[str, Any]] = [
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
            {
                "id": "tool3",
                "name": "move_tool",
                "input": {"x": 300, "y": 400},
                "type": "tool_use",
            },
        ]

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(trajectory, f)

        # Execute with custom delay time
        custom_settings = CachedExecutionToolSettings(delay_time_between_action=0.1)
        tool = ExecuteCachedTrajectory(settings=custom_settings)
        mock_toolbox = MagicMock(spec=ToolCollection)
        tool.set_toolbox(mock_toolbox)

        # Mock time.sleep to verify it's called with correct delay
        with patch("time.sleep") as mock_sleep:
            result = tool(trajectory_file=str(cache_file))

            # Verify success
            assert "Successfully executed trajectory" in result
            # Verify sleep was called 3 times (once after each action)
            assert mock_sleep.call_count == 3
            # Verify it was called with the configured delay time
            for call in mock_sleep.call_args_list:
                assert call[0][0] == 0.1


def test_execute_cached_execution_default_delay_time() -> None:
    """Test that ExecuteCachedTrajectory uses default delay time of 0.5s."""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "test_trajectory.json"

        # Create a trajectory with 2 actions
        trajectory: list[dict[str, Any]] = [
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
        ]

        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(trajectory, f)

        # Execute with default settings
        tool = ExecuteCachedTrajectory()
        mock_toolbox = MagicMock(spec=ToolCollection)
        tool.set_toolbox(mock_toolbox)

        # Mock time.sleep to verify default delay is used
        with patch("time.sleep") as mock_sleep:
            result = tool(trajectory_file=str(cache_file))

            # Verify success
            assert "Successfully executed trajectory" in result
            # Verify sleep was called with default delay of 0.5s
            assert mock_sleep.call_count == 2
            for call in mock_sleep.call_args_list:
                assert call[0][0] == 0.5
