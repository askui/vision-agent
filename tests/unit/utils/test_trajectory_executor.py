"""Unit tests for TrajectoryExecutor."""

from unittest.mock import MagicMock

import pytest

from askui.models.shared.agent_message_param import (
    MessageParam,
    TextBlockParam,
    ToolResultBlockParam,
    ToolUseBlockParam,
)
from askui.models.shared.tools import ToolCollection
from askui.utils.trajectory_executor import TrajectoryExecutor


def test_trajectory_executor_initialization() -> None:
    """Test TrajectoryExecutor initialization."""
    trajectory = [ToolUseBlockParam(id="1", name="tool1", input={}, type="tool_use")]
    toolbox = ToolCollection()

    executor = TrajectoryExecutor(
        trajectory=trajectory,
        toolbox=toolbox,
        placeholder_values={"var": "value"},
        delay_time=0.1,
    )

    assert executor.trajectory == trajectory
    assert executor.toolbox == toolbox
    assert executor.placeholder_values == {"var": "value"}
    assert executor.delay_time == 0.1
    assert executor.current_step_index == 0


def test_trajectory_executor_execute_simple_step() -> None:
    """Test executing a simple step."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Tool result")],
        )
    ]
    mock_toolbox._tool_map = {}

    trajectory = [
        ToolUseBlockParam(
            id="1", name="test_tool", input={"param": "value"}, type="tool_use"
        )
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    result = executor.execute_next_step()

    assert result.status == "SUCCESS"
    assert result.step_index == 0
    assert result.error_message is None
    assert executor.current_step_index == 1
    assert mock_toolbox.run.call_count == 1


def test_trajectory_executor_execute_all_steps() -> None:
    """Test executing all steps in a trajectory."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Result")],
        )
    ]
    mock_toolbox._tool_map = {}

    trajectory = [
        ToolUseBlockParam(id="1", name="tool1", input={}, type="tool_use"),
        ToolUseBlockParam(id="2", name="tool2", input={}, type="tool_use"),
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    results = executor.execute_all()

    # Should have 3 results: 2 successful steps + 1 completed
    assert len(results) == 3
    assert results[0].status == "SUCCESS"
    assert results[0].step_index == 0
    assert results[1].status == "SUCCESS"
    assert results[1].step_index == 1
    assert results[2].status == "COMPLETED"
    assert executor.current_step_index == 2
    assert mock_toolbox.run.call_count == 2


def test_trajectory_executor_executes_screenshot_tools() -> None:
    """Test that screenshot tools are executed (not skipped)."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Screenshot result")],
        )
    ]
    mock_toolbox._tool_map = {}

    trajectory = [
        ToolUseBlockParam(id="1", name="screenshot", input={}, type="tool_use"),
        ToolUseBlockParam(id="2", name="tool1", input={}, type="tool_use"),
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    result = executor.execute_next_step()

    # Should execute screenshot tool
    assert result.status == "SUCCESS"
    assert result.step_index == 0  # First step executed
    assert mock_toolbox.run.call_count == 1
    # Verify screenshot tool was called
    assert mock_toolbox.run.call_args[0][0][0].name == "screenshot"


def test_trajectory_executor_executes_retrieve_trajectories_tool() -> None:
    """Test that retrieve_available_trajectories_tool is executed (not skipped)."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Trajectory list")],
        )
    ]
    mock_toolbox._tool_map = {}

    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="retrieve_available_trajectories_tool",
            input={},
            type="tool_use",
        ),
        ToolUseBlockParam(id="2", name="tool1", input={}, type="tool_use"),
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    result = executor.execute_next_step()

    # Should execute retrieve tool
    assert result.status == "SUCCESS"
    assert result.step_index == 0  # First step executed
    assert mock_toolbox.run.call_count == 1
    # Verify retrieve tool was called
    assert (
        mock_toolbox.run.call_args[0][0][0].name
        == "retrieve_available_trajectories_tool"
    )


def test_trajectory_executor_pauses_at_non_cacheable_tool() -> None:
    """Test that execution pauses at non-cacheable tools."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Result")],
        )
    ]

    # Create mock tools in the toolbox
    cacheable_tool = MagicMock()
    cacheable_tool.is_cacheable = True
    non_cacheable_tool = MagicMock()
    non_cacheable_tool.is_cacheable = False

    mock_toolbox._tool_map = {
        "cacheable": cacheable_tool,
        "non_cacheable": non_cacheable_tool,
    }

    trajectory = [
        ToolUseBlockParam(id="1", name="cacheable", input={}, type="tool_use"),
        ToolUseBlockParam(id="2", name="non_cacheable", input={}, type="tool_use"),
        ToolUseBlockParam(id="3", name="cacheable", input={}, type="tool_use"),
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    results = executor.execute_all()

    # Should execute first step, then pause at non-cacheable
    assert len(results) == 2
    assert results[0].status == "SUCCESS"
    assert results[0].step_index == 0
    assert results[1].status == "NEEDS_AGENT"
    assert results[1].step_index == 1
    assert mock_toolbox.run.call_count == 1  # Only first step executed
    assert executor.current_step_index == 1  # Paused at step 1


def test_trajectory_executor_handles_tool_error() -> None:
    """Test that executor handles tool execution errors gracefully."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox._tool_map = {}
    mock_toolbox.run.side_effect = Exception("Tool execution failed")

    trajectory = [
        ToolUseBlockParam(id="1", name="failing_tool", input={}, type="tool_use")
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    result = executor.execute_next_step()

    assert result.status == "FAILED"
    assert result.step_index == 0
    assert "Tool execution failed" in (result.error_message or "")


def test_trajectory_executor_substitutes_placeholders() -> None:
    """Test that executor substitutes placeholders before execution."""
    captured_steps = []

    def capture_run(steps):  # type: ignore
        captured_steps.extend(steps)
        return [
            ToolResultBlockParam(
                tool_use_id="1",
                content=[TextBlockParam(type="text", text="Result")],
            )
        ]

    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run = capture_run
    mock_toolbox._tool_map = {}

    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="test_tool",
            input={"text": "Hello {{name}}"},
            type="tool_use",
        )
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory,
        toolbox=mock_toolbox,
        placeholder_values={"name": "Alice"},
        delay_time=0,
    )

    result = executor.execute_next_step()

    assert result.status == "SUCCESS"
    assert len(captured_steps) == 1
    assert captured_steps[0].input["text"] == "Hello Alice"


def test_trajectory_executor_get_current_step_index() -> None:
    """Test getting current step index."""
    toolbox = ToolCollection()
    trajectory = [ToolUseBlockParam(id="1", name="tool1", input={}, type="tool_use")]

    executor = TrajectoryExecutor(trajectory=trajectory, toolbox=toolbox, delay_time=0)

    assert executor.get_current_step_index() == 0

    executor.current_step_index = 5
    assert executor.get_current_step_index() == 5


def test_trajectory_executor_get_remaining_trajectory() -> None:
    """Test getting remaining trajectory steps."""
    toolbox = ToolCollection()
    trajectory = [
        ToolUseBlockParam(id="1", name="tool1", input={}, type="tool_use"),
        ToolUseBlockParam(id="2", name="tool2", input={}, type="tool_use"),
        ToolUseBlockParam(id="3", name="tool3", input={}, type="tool_use"),
    ]

    executor = TrajectoryExecutor(trajectory=trajectory, toolbox=toolbox, delay_time=0)

    # Initially, all steps remain
    remaining = executor.get_remaining_trajectory()
    assert len(remaining) == 3

    # After advancing to step 1
    executor.current_step_index = 1
    remaining = executor.get_remaining_trajectory()
    assert len(remaining) == 2
    assert remaining[0].id == "2"
    assert remaining[1].id == "3"

    # At the end
    executor.current_step_index = 3
    remaining = executor.get_remaining_trajectory()
    assert len(remaining) == 0


def test_trajectory_executor_skip_current_step() -> None:
    """Test skipping the current step."""
    toolbox = ToolCollection()
    trajectory = [
        ToolUseBlockParam(id="1", name="tool1", input={}, type="tool_use"),
        ToolUseBlockParam(id="2", name="tool2", input={}, type="tool_use"),
    ]

    executor = TrajectoryExecutor(trajectory=trajectory, toolbox=toolbox, delay_time=0)

    assert executor.current_step_index == 0
    executor.skip_current_step()
    assert executor.current_step_index == 1
    executor.skip_current_step()
    assert executor.current_step_index == 2


def test_trajectory_executor_skip_at_end_does_nothing() -> None:
    """Test that skipping at the end doesn't cause errors."""
    toolbox = ToolCollection()
    trajectory = [ToolUseBlockParam(id="1", name="tool1", input={}, type="tool_use")]

    executor = TrajectoryExecutor(trajectory=trajectory, toolbox=toolbox, delay_time=0)

    executor.current_step_index = 1  # Already at end
    executor.skip_current_step()
    assert executor.current_step_index == 1  # Stays at end


def test_trajectory_executor_completed_status_when_done() -> None:
    """Test that executor returns COMPLETED when all steps are done."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Result")],
        )
    ]
    mock_toolbox._tool_map = {}

    trajectory = [ToolUseBlockParam(id="1", name="tool1", input={}, type="tool_use")]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    # Execute the step
    result1 = executor.execute_next_step()
    assert result1.status == "SUCCESS"

    # Try to execute again (no more steps)
    result2 = executor.execute_next_step()
    assert result2.status == "COMPLETED"


def test_trajectory_executor_execute_all_stops_on_failure() -> None:
    """Test that execute_all stops when a step fails."""
    # Mock to fail on second call
    call_count = [0]

    def mock_run(steps):  # type: ignore
        call_count[0] += 1
        if call_count[0] == 2:
            raise Exception("Second call fails")
        return [
            ToolResultBlockParam(
                tool_use_id="1",
                content=[TextBlockParam(type="text", text="Result")],
            )
        ]

    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run = mock_run
    mock_toolbox._tool_map = {}

    trajectory = [
        ToolUseBlockParam(id="1", name="tool1", input={}, type="tool_use"),
        ToolUseBlockParam(id="2", name="tool1", input={}, type="tool_use"),
        ToolUseBlockParam(id="3", name="tool1", input={}, type="tool_use"),
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    results = executor.execute_all()

    # Should have 2 results: 1 success + 1 failure (stopped)
    assert len(results) == 2
    assert results[0].status == "SUCCESS"
    assert results[1].status == "FAILED"
    assert executor.current_step_index == 1  # Stopped at failed step


def test_trajectory_executor_builds_message_history() -> None:
    """Test that executor builds message history during execution."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Result1")],
        )
    ]
    mock_toolbox._tool_map = {}

    trajectory = [
        ToolUseBlockParam(
            id="tool1", name="test_tool", input={"x": 100}, type="tool_use"
        )
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    result = executor.execute_next_step()

    # Verify message history is built
    assert result.status == "SUCCESS"
    assert len(result.message_history) == 2  # Assistant + User message

    # Verify assistant message (tool use)
    assert isinstance(result.message_history[0], MessageParam)
    assert result.message_history[0].role == "assistant"
    assert isinstance(result.message_history[0].content, list)
    assert len(result.message_history[0].content) == 1
    assert isinstance(result.message_history[0].content[0], ToolUseBlockParam)

    # Verify user message (tool result)
    assert isinstance(result.message_history[1], MessageParam)
    assert result.message_history[1].role == "user"
    assert isinstance(result.message_history[1].content, list)
    assert len(result.message_history[1].content) == 1
    assert isinstance(result.message_history[1].content[0], ToolResultBlockParam)


def test_trajectory_executor_message_history_accumulates() -> None:
    """Test that message history accumulates across multiple steps."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Result")],
        )
    ]
    mock_toolbox._tool_map = {}

    trajectory = [
        ToolUseBlockParam(id="1", name="tool1", input={}, type="tool_use"),
        ToolUseBlockParam(id="2", name="tool2", input={}, type="tool_use"),
        ToolUseBlockParam(id="3", name="tool3", input={}, type="tool_use"),
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    results = executor.execute_all()

    # Should have 4 results: 3 successful steps + 1 completed
    assert len(results) == 4

    # Check message history grows
    assert len(results[0].message_history) == 2  # Step 1: assistant + user
    assert len(results[1].message_history) == 4  # Step 2: + assistant + user
    assert len(results[2].message_history) == 6  # Step 3: + assistant + user
    assert len(results[3].message_history) == 6  # Completed: same as last step


def test_trajectory_executor_message_history_contains_tool_use_id() -> None:
    """Test that tool result has correct tool_use_id matching tool use."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Success")],
        )
    ]
    mock_toolbox._tool_map = {}

    trajectory = [ToolUseBlockParam(id="1", name="tool", input={}, type="tool_use")]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    result = executor.execute_next_step()

    # Get tool use and tool result
    tool_use = result.message_history[0].content[0]
    tool_result = result.message_history[1].content[0]

    # Verify tool_use_id matches
    assert isinstance(tool_use, ToolUseBlockParam)
    assert isinstance(tool_result, ToolResultBlockParam)
    assert tool_result.tool_use_id == tool_use.id
    assert tool_result.tool_use_id == "1"


def test_trajectory_executor_message_history_includes_text_result() -> None:
    """Test that tool results include text content."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Tool executed successfully")],
        )
    ]
    mock_toolbox._tool_map = {}

    trajectory = [ToolUseBlockParam(id="1", name="tool", input={}, type="tool_use")]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    result = executor.execute_next_step()

    # Get tool result
    tool_result_block = result.message_history[1].content[0]
    assert isinstance(tool_result_block, ToolResultBlockParam)

    # Verify text content is included
    assert isinstance(tool_result_block.content, list)
    assert len(tool_result_block.content) == 1
    assert isinstance(tool_result_block.content[0], TextBlockParam)
    assert tool_result_block.content[0].text == "Tool executed successfully"


def test_trajectory_executor_message_history_on_failure() -> None:
    """Test that message history is included even when execution fails."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox._tool_map = {}
    mock_toolbox.run.side_effect = Exception("Tool failed")

    trajectory = [
        ToolUseBlockParam(id="1", name="failing_tool", input={}, type="tool_use")
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    result = executor.execute_next_step()

    assert result.status == "FAILED"
    # Message history should include the assistant message (tool use)
    # but not the user message (since execution failed)
    assert len(result.message_history) == 1
    assert result.message_history[0].role == "assistant"


def test_trajectory_executor_message_history_on_pause() -> None:
    """Test that message history is included when execution pauses."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Result")],
        )
    ]

    cacheable_tool = MagicMock()
    cacheable_tool.is_cacheable = True
    non_cacheable_tool = MagicMock()
    non_cacheable_tool.is_cacheable = False

    mock_toolbox._tool_map = {
        "cacheable": cacheable_tool,
        "non_cacheable": non_cacheable_tool,
    }

    trajectory = [
        ToolUseBlockParam(id="1", name="cacheable", input={}, type="tool_use"),
        ToolUseBlockParam(id="2", name="non_cacheable", input={}, type="tool_use"),
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    results = executor.execute_all()

    # Should pause at non-cacheable step
    assert len(results) == 2
    assert results[0].status == "SUCCESS"
    assert results[1].status == "NEEDS_AGENT"

    # Message history should include only the successfully executed cacheable step:
    # 1. First step: assistant message (tool use)
    # 2. First step: user message (tool result)
    # The non-cacheable tool is NOT in message history - instead it's in tool_result
    assert len(results[1].message_history) == 2
    assert results[1].message_history[0].role == "assistant"  # First cacheable tool use
    assert results[1].message_history[1].role == "user"  # First tool result

    # The non-cacheable tool should be in tool_result for reference
    assert results[1].tool_result is not None
    assert results[1].tool_result.name == "non_cacheable"


def test_trajectory_executor_message_history_order() -> None:
    """Test that message history maintains correct order."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Result")],
        )
    ]
    mock_toolbox._tool_map = {}

    trajectory = [
        ToolUseBlockParam(id="1", name="tool1", input={"step": 1}, type="tool_use"),
        ToolUseBlockParam(id="2", name="tool2", input={"step": 2}, type="tool_use"),
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    results = executor.execute_all()

    # Get final message history
    final_history = results[-1].message_history

    # Should have 4 messages: assistant, user, assistant, user
    assert len(final_history) == 4
    assert final_history[0].role == "assistant"  # Step 1 tool use
    assert final_history[1].role == "user"  # Step 1 result
    assert final_history[2].role == "assistant"  # Step 2 tool use
    assert final_history[3].role == "user"  # Step 2 result

    # Verify step order in tool use
    tool_use_1 = final_history[0].content[0]
    tool_use_2 = final_history[2].content[0]
    assert isinstance(tool_use_1, ToolUseBlockParam)
    assert isinstance(tool_use_2, ToolUseBlockParam)
    assert tool_use_1.input == {"step": 1}
    assert tool_use_2.input == {"step": 2}


# Visual Validation Extension Point Tests


def test_visual_validation_disabled_by_default() -> None:
    """Test that visual validation is disabled by default."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Result")],
        )
    ]
    mock_toolbox._tool_map = {}

    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="click",
            input={"x": 100},
            type="tool_use",
            visual_hash="abc123",
            visual_validation_required=True,
        ),
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    # visual_validation_enabled should be False by default
    assert executor.visual_validation_enabled is False

    # Should execute successfully without validation
    results = executor.execute_all()
    assert results[0].status == "SUCCESS"


def test_visual_validation_enabled_flag() -> None:
    """Test that visual validation flag can be enabled."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Result")],
        )
    ]
    mock_toolbox._tool_map = {}

    trajectory = [
        ToolUseBlockParam(id="1", name="click", input={"x": 100}, type="tool_use"),
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory,
        toolbox=mock_toolbox,
        delay_time=0,
        visual_validation_enabled=True,
    )

    # visual_validation_enabled should be True
    assert executor.visual_validation_enabled is True


def test_validate_step_visually_hook_exists() -> None:
    """Test that validate_step_visually hook exists and returns correct signature."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox._tool_map = {}

    trajectory = [
        ToolUseBlockParam(id="1", name="click", input={"x": 100}, type="tool_use"),
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory, toolbox=mock_toolbox, delay_time=0
    )

    # Hook should exist
    assert hasattr(executor, "validate_step_visually")
    assert callable(executor.validate_step_visually)

    # Hook should return correct signature
    step = trajectory[0]
    is_valid, error_msg = executor.validate_step_visually(step)

    assert isinstance(is_valid, bool)
    assert is_valid is True  # Currently always returns True
    assert error_msg is None


def test_validate_step_visually_always_passes_when_disabled() -> None:
    """Test that validation always passes when disabled (default behavior)."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Result")],
        )
    ]
    mock_toolbox._tool_map = {}

    # Create step with visual validation fields
    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="click",
            input={"x": 100},
            type="tool_use",
            visual_hash="abc123",
            visual_validation_required=True,
        ),
    ]

    # Validation disabled (default)
    executor = TrajectoryExecutor(
        trajectory=trajectory,
        toolbox=mock_toolbox,
        delay_time=0,
        visual_validation_enabled=False,
    )

    # Should execute without calling validate_step_visually
    results = executor.execute_all()
    assert results[0].status == "SUCCESS"


def test_validate_step_visually_hook_called_when_enabled() -> None:
    """Test that validate_step_visually is called when enabled."""
    mock_toolbox = MagicMock(spec=ToolCollection)
    mock_toolbox.run.return_value = [
        ToolResultBlockParam(
            tool_use_id="1",
            content=[TextBlockParam(type="text", text="Result")],
        )
    ]
    mock_toolbox._tool_map = {}

    trajectory = [
        ToolUseBlockParam(
            id="1",
            name="click",
            input={"x": 100},
            type="tool_use",
            visual_hash="abc123",
            visual_validation_required=True,
        ),
    ]

    executor = TrajectoryExecutor(
        trajectory=trajectory,
        toolbox=mock_toolbox,
        delay_time=0,
        visual_validation_enabled=True,
    )

    # Mock the validation hook to track calls
    original_validate = executor.validate_step_visually
    validation_called = []

    def mock_validate(step, screenshot=None) -> tuple[bool, str | None]:  # type: ignore[no-untyped-def]
        validation_called.append(step)
        return original_validate(step, screenshot)

    executor.validate_step_visually = mock_validate  # type: ignore[assignment]

    # Execute trajectory
    results = executor.execute_all()

    # Validation should have been called
    assert len(validation_called) == 1
    assert results[0].status == "SUCCESS"


@pytest.mark.skip(
    reason="Visual validation fields not yet implemented - future feature"
)
def test_visual_validation_fields_on_tool_use_block() -> None:
    """Test that ToolUseBlockParam supports visual validation fields.

    Note: This test is for future functionality. Visual validation fields
    (visual_hash, visual_validation_required) are planned but not yet
    implemented in the ToolUseBlockParam model.
    """
    # Create step with visual validation fields
    step = ToolUseBlockParam(
        id="1",
        name="click",
        input={"x": 100, "y": 200},
        type="tool_use",
        visual_hash="a8f3c9e14b7d2056",
        visual_validation_required=True,
    )

    # Fields should be accessible
    assert step.visual_hash == "a8f3c9e14b7d2056"  # type: ignore[attr-defined]
    assert step.visual_validation_required is True  # type: ignore[attr-defined]

    # Default values should work
    step_default = ToolUseBlockParam(
        id="2", name="type", input={"text": "hello"}, type="tool_use"
    )

    assert step_default.visual_hash is None  # type: ignore[attr-defined]
    assert step_default.visual_validation_required is False  # type: ignore[attr-defined]
