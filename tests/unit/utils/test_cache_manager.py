"""Tests for cache manager."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from askui.models.shared.agent_message_param import ToolUseBlockParam
from askui.models.shared.settings import CacheFailure, CacheFile, CacheMetadata
from askui.utils.cache_manager import CacheManager
from askui.utils.cache_validator import (
    CacheValidator,
    CompositeCacheValidator,
    StepFailureCountValidator,
)


@pytest.fixture
def sample_cache_file():
    """Create a sample cache file for testing."""
    return CacheFile(
        metadata=CacheMetadata(
            version="0.1",
            created_at=datetime.now(tz=timezone.utc),
            execution_attempts=0,
            is_valid=True,
        ),
        trajectory=[
            ToolUseBlockParam(
                id="1", name="click", input={"x": 100}, type="tool_use"
            ),
            ToolUseBlockParam(id="2", name="type", input={"text": "test"}, type="tool_use"),
        ],
        placeholders={},
    )


# Initialization Tests


def test_cache_manager_default_initialization():
    """Test cache manager initializes with default validator."""
    manager = CacheManager()
    assert manager.validator is not None
    assert isinstance(manager.validator, CompositeCacheValidator)
    assert len(manager.validator.validators) == 3  # 3 built-in validators


def test_cache_manager_custom_validator():
    """Test cache manager with custom validator."""
    custom_validator = StepFailureCountValidator(max_failures_per_step=5)
    manager = CacheManager(validator=custom_validator)
    assert manager.validator is custom_validator


# Record Execution Attempt Tests


def test_record_execution_attempt_success(sample_cache_file):
    """Test recording successful execution attempt."""
    manager = CacheManager()
    initial_attempts = sample_cache_file.metadata.execution_attempts
    initial_last_executed = sample_cache_file.metadata.last_executed_at

    manager.record_execution_attempt(sample_cache_file, success=True)

    assert sample_cache_file.metadata.execution_attempts == initial_attempts + 1
    assert sample_cache_file.metadata.last_executed_at is not None
    assert sample_cache_file.metadata.last_executed_at != initial_last_executed


def test_record_execution_attempt_failure_with_info(sample_cache_file):
    """Test recording failed execution attempt with failure info."""
    manager = CacheManager()
    initial_attempts = sample_cache_file.metadata.execution_attempts
    initial_failures = len(sample_cache_file.metadata.failures)

    failure_info = CacheFailure(
        timestamp=datetime.now(tz=timezone.utc),
        step_index=1,
        error_message="Test error",
        failure_count_at_step=1,
    )

    manager.record_execution_attempt(
        sample_cache_file, success=False, failure_info=failure_info
    )

    assert sample_cache_file.metadata.execution_attempts == initial_attempts + 1
    assert len(sample_cache_file.metadata.failures) == initial_failures + 1
    assert sample_cache_file.metadata.failures[-1] == failure_info


def test_record_execution_attempt_failure_without_info(sample_cache_file):
    """Test recording failed execution attempt without failure info."""
    manager = CacheManager()
    initial_attempts = sample_cache_file.metadata.execution_attempts
    initial_failures = len(sample_cache_file.metadata.failures)

    manager.record_execution_attempt(sample_cache_file, success=False, failure_info=None)

    assert sample_cache_file.metadata.execution_attempts == initial_attempts + 1
    assert len(sample_cache_file.metadata.failures) == initial_failures  # No new failure added


# Record Step Failure Tests


def test_record_step_failure_first_failure(sample_cache_file):
    """Test recording the first failure at a step."""
    manager = CacheManager()

    manager.record_step_failure(sample_cache_file, step_index=1, error_message="First error")

    assert len(sample_cache_file.metadata.failures) == 1
    failure = sample_cache_file.metadata.failures[0]
    assert failure.step_index == 1
    assert failure.error_message == "First error"
    assert failure.failure_count_at_step == 1


def test_record_step_failure_multiple_at_same_step(sample_cache_file):
    """Test recording multiple failures at the same step."""
    manager = CacheManager()

    manager.record_step_failure(sample_cache_file, step_index=1, error_message="Error 1")
    manager.record_step_failure(sample_cache_file, step_index=1, error_message="Error 2")
    manager.record_step_failure(sample_cache_file, step_index=1, error_message="Error 3")

    assert len(sample_cache_file.metadata.failures) == 3
    assert sample_cache_file.metadata.failures[0].failure_count_at_step == 1
    assert sample_cache_file.metadata.failures[1].failure_count_at_step == 2
    assert sample_cache_file.metadata.failures[2].failure_count_at_step == 3


def test_record_step_failure_different_steps(sample_cache_file):
    """Test recording failures at different steps."""
    manager = CacheManager()

    manager.record_step_failure(sample_cache_file, step_index=1, error_message="Error at step 1")
    manager.record_step_failure(sample_cache_file, step_index=2, error_message="Error at step 2")
    manager.record_step_failure(sample_cache_file, step_index=1, error_message="Another at step 1")

    assert len(sample_cache_file.metadata.failures) == 3

    step_1_failures = [f for f in sample_cache_file.metadata.failures if f.step_index == 1]
    step_2_failures = [f for f in sample_cache_file.metadata.failures if f.step_index == 2]

    assert len(step_1_failures) == 2
    assert len(step_2_failures) == 1
    assert step_1_failures[1].failure_count_at_step == 2  # Second failure at step 1


# Should Invalidate Tests


def test_should_invalidate_delegates_to_validator(sample_cache_file):
    """Test that should_invalidate delegates to the validator."""
    mock_validator = MagicMock(spec=CacheValidator)
    mock_validator.should_invalidate.return_value = (True, "Test reason")

    manager = CacheManager(validator=mock_validator)
    should_inv, reason = manager.should_invalidate(sample_cache_file, step_index=1)

    assert should_inv is True
    assert reason == "Test reason"
    mock_validator.should_invalidate.assert_called_once_with(sample_cache_file, 1)


def test_should_invalidate_with_default_validator(sample_cache_file):
    """Test should_invalidate with default built-in validators."""
    manager = CacheManager()

    # Add failures that exceed default thresholds
    sample_cache_file.metadata.execution_attempts = 10
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message=f"Error {i}",
            failure_count_at_step=i + 1,
        )
        for i in range(6)
    ]  # 6/10 = 60% failure rate (exceeds default 50%)

    should_inv, reason = manager.should_invalidate(sample_cache_file)
    assert should_inv is True
    assert "Failure rate" in reason


# Invalidate Cache Tests


def test_invalidate_cache(sample_cache_file):
    """Test marking cache as invalid."""
    manager = CacheManager()
    assert sample_cache_file.metadata.is_valid is True
    assert sample_cache_file.metadata.invalidation_reason is None

    manager.invalidate_cache(sample_cache_file, reason="Test invalidation")

    assert sample_cache_file.metadata.is_valid is False
    assert sample_cache_file.metadata.invalidation_reason == "Test invalidation"


def test_invalidate_cache_multiple_times(sample_cache_file):
    """Test invalidating cache multiple times updates reason."""
    manager = CacheManager()

    manager.invalidate_cache(sample_cache_file, reason="First reason")
    assert sample_cache_file.metadata.invalidation_reason == "First reason"

    manager.invalidate_cache(sample_cache_file, reason="Second reason")
    assert sample_cache_file.metadata.invalidation_reason == "Second reason"


# Mark Cache Valid Tests


def test_mark_cache_valid(sample_cache_file):
    """Test marking cache as valid."""
    manager = CacheManager()

    # First invalidate
    sample_cache_file.metadata.is_valid = False
    sample_cache_file.metadata.invalidation_reason = "Was invalid"

    # Then mark valid
    manager.mark_cache_valid(sample_cache_file)

    assert sample_cache_file.metadata.is_valid is True
    assert sample_cache_file.metadata.invalidation_reason is None


def test_mark_cache_valid_already_valid(sample_cache_file):
    """Test marking already valid cache as valid."""
    manager = CacheManager()
    assert sample_cache_file.metadata.is_valid is True

    manager.mark_cache_valid(sample_cache_file)

    assert sample_cache_file.metadata.is_valid is True
    assert sample_cache_file.metadata.invalidation_reason is None


# Get Failure Count for Step Tests


def test_get_failure_count_for_step_no_failures(sample_cache_file):
    """Test getting failure count when no failures exist."""
    manager = CacheManager()

    count = manager.get_failure_count_for_step(sample_cache_file, step_index=1)
    assert count == 0


def test_get_failure_count_for_step_with_failures(sample_cache_file):
    """Test getting failure count for specific step."""
    manager = CacheManager()

    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message="Error 1",
            failure_count_at_step=1,
        ),
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=2,
            error_message="Error 2",
            failure_count_at_step=1,
        ),
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message="Error 3",
            failure_count_at_step=2,
        ),
    ]

    count_step_1 = manager.get_failure_count_for_step(sample_cache_file, step_index=1)
    count_step_2 = manager.get_failure_count_for_step(sample_cache_file, step_index=2)

    assert count_step_1 == 2
    assert count_step_2 == 1


def test_get_failure_count_for_step_nonexistent_step(sample_cache_file):
    """Test getting failure count for step that hasn't failed."""
    manager = CacheManager()

    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message="Error",
            failure_count_at_step=1,
        )
    ]

    count = manager.get_failure_count_for_step(sample_cache_file, step_index=99)
    assert count == 0


# Integration Tests


def test_full_workflow_with_failure_detection(sample_cache_file):
    """Test complete workflow: record failures, detect threshold, invalidate."""
    manager = CacheManager()

    # Record 3 failures at step 1 (default threshold is 3)
    for i in range(3):
        manager.record_step_failure(
            sample_cache_file, step_index=1, error_message=f"Error {i+1}"
        )

    # Check if should invalidate
    should_inv, reason = manager.should_invalidate(sample_cache_file, step_index=1)
    assert should_inv is True
    assert "Step 1 failed 3 times" in reason

    # Invalidate
    manager.invalidate_cache(sample_cache_file, reason=reason)
    assert sample_cache_file.metadata.is_valid is False


def test_full_workflow_below_threshold(sample_cache_file):
    """Test workflow where failures don't reach threshold."""
    manager = CacheManager()

    # Record 2 failures at step 1 (below default threshold of 3)
    for i in range(2):
        manager.record_step_failure(
            sample_cache_file, step_index=1, error_message=f"Error {i+1}"
        )

    # Check if should invalidate
    should_inv, reason = manager.should_invalidate(sample_cache_file, step_index=1)
    assert should_inv is False

    # Cache should still be valid
    assert sample_cache_file.metadata.is_valid is True


def test_workflow_with_custom_validator(sample_cache_file):
    """Test workflow with custom validator with lower threshold."""
    # Custom validator with lower threshold
    custom_validator = CompositeCacheValidator(
        [StepFailureCountValidator(max_failures_per_step=2)]
    )
    manager = CacheManager(validator=custom_validator)

    # Record 2 failures (enough to trigger custom validator)
    for i in range(2):
        manager.record_step_failure(
            sample_cache_file, step_index=1, error_message=f"Error {i+1}"
        )

    should_inv, reason = manager.should_invalidate(sample_cache_file, step_index=1)
    assert should_inv is True
    assert "Step 1 failed 2 times" in reason


def test_workflow_successful_execution_updates_timestamp(sample_cache_file):
    """Test that successful execution updates last_executed_at."""
    manager = CacheManager()

    # Record some failures first
    manager.record_step_failure(sample_cache_file, step_index=1, error_message="Error")
    assert sample_cache_file.metadata.last_executed_at is None

    # Record successful execution
    manager.record_execution_attempt(sample_cache_file, success=True)

    assert sample_cache_file.metadata.last_executed_at is not None
    assert sample_cache_file.metadata.execution_attempts == 1
