"""Tests for cache validation strategies."""

from datetime import datetime, timedelta, timezone

import pytest

from askui.models.shared.agent_message_param import ToolUseBlockParam
from askui.models.shared.settings import CacheFailure, CacheFile, CacheMetadata
from askui.utils.cache_validator import (
    CacheValidator,
    CompositeCacheValidator,
    StaleCacheValidator,
    StepFailureCountValidator,
    TotalFailureRateValidator,
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


# StepFailureCountValidator Tests


def test_step_failure_count_validator_below_threshold(sample_cache_file):
    """Test validator does not invalidate when failures are below threshold."""
    validator = StepFailureCountValidator(max_failures_per_step=3)

    # Add 2 failures at step 1
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message="Error 1",
            failure_count_at_step=1,
        ),
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message="Error 2",
            failure_count_at_step=2,
        ),
    ]

    should_inv, reason = validator.should_invalidate(sample_cache_file, step_index=1)
    assert should_inv is False
    assert reason is None


def test_step_failure_count_validator_at_threshold(sample_cache_file):
    """Test validator invalidates when failures reach threshold."""
    validator = StepFailureCountValidator(max_failures_per_step=3)

    # Add 3 failures at step 1
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message=f"Error {i}",
            failure_count_at_step=i + 1,
        )
        for i in range(3)
    ]

    should_inv, reason = validator.should_invalidate(sample_cache_file, step_index=1)
    assert should_inv is True
    assert "Step 1 failed 3 times" in reason


def test_step_failure_count_validator_different_steps(sample_cache_file):
    """Test validator only counts failures for specific step."""
    validator = StepFailureCountValidator(max_failures_per_step=3)

    # Add failures at different steps
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message="Error at step 1",
            failure_count_at_step=1,
        ),
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=2,
            error_message="Error at step 2",
            failure_count_at_step=1,
        ),
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message="Error at step 1 again",
            failure_count_at_step=2,
        ),
    ]

    # Step 1 has 2 failures (below threshold)
    should_inv, reason = validator.should_invalidate(sample_cache_file, step_index=1)
    assert should_inv is False

    # Step 2 has 1 failure (below threshold)
    should_inv, reason = validator.should_invalidate(sample_cache_file, step_index=2)
    assert should_inv is False


def test_step_failure_count_validator_no_step_index(sample_cache_file):
    """Test validator returns False when no step_index provided."""
    validator = StepFailureCountValidator(max_failures_per_step=3)

    should_inv, reason = validator.should_invalidate(sample_cache_file, step_index=None)
    assert should_inv is False
    assert reason is None


def test_step_failure_count_validator_name():
    """Test validator returns correct name."""
    validator = StepFailureCountValidator()
    assert validator.get_name() == "StepFailureCount"


# TotalFailureRateValidator Tests


def test_total_failure_rate_validator_below_min_attempts(sample_cache_file):
    """Test validator does not check rate below minimum attempts."""
    validator = TotalFailureRateValidator(min_attempts=10, max_failure_rate=0.5)

    sample_cache_file.metadata.execution_attempts = 5
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message="Error",
            failure_count_at_step=1,
        )
        for _ in range(4)
    ]  # 4/5 = 80% failure rate

    should_inv, reason = validator.should_invalidate(sample_cache_file)
    assert should_inv is False  # Too few attempts to judge


def test_total_failure_rate_validator_above_threshold(sample_cache_file):
    """Test validator invalidates when failure rate exceeds threshold."""
    validator = TotalFailureRateValidator(min_attempts=10, max_failure_rate=0.5)

    sample_cache_file.metadata.execution_attempts = 10
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=i % 2,
            error_message=f"Error {i}",
            failure_count_at_step=1,
        )
        for i in range(6)
    ]  # 6/10 = 60% failure rate

    should_inv, reason = validator.should_invalidate(sample_cache_file)
    assert should_inv is True
    assert "60.0%" in reason
    assert "50.0%" in reason


def test_total_failure_rate_validator_below_threshold(sample_cache_file):
    """Test validator does not invalidate when rate is acceptable."""
    validator = TotalFailureRateValidator(min_attempts=10, max_failure_rate=0.5)

    sample_cache_file.metadata.execution_attempts = 10
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message=f"Error {i}",
            failure_count_at_step=1,
        )
        for i in range(4)
    ]  # 4/10 = 40% failure rate

    should_inv, reason = validator.should_invalidate(sample_cache_file)
    assert should_inv is False


def test_total_failure_rate_validator_zero_attempts(sample_cache_file):
    """Test validator handles zero attempts correctly."""
    validator = TotalFailureRateValidator(min_attempts=10, max_failure_rate=0.5)

    sample_cache_file.metadata.execution_attempts = 0
    sample_cache_file.metadata.failures = []

    should_inv, reason = validator.should_invalidate(sample_cache_file)
    assert should_inv is False


def test_total_failure_rate_validator_name():
    """Test validator returns correct name."""
    validator = TotalFailureRateValidator()
    assert validator.get_name() == "TotalFailureRate"


# StaleCacheValidator Tests


def test_stale_cache_validator_not_stale(sample_cache_file):
    """Test validator does not invalidate recent cache."""
    validator = StaleCacheValidator(max_age_days=30)

    sample_cache_file.metadata.last_executed_at = datetime.now(tz=timezone.utc) - timedelta(days=10)
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message="Error",
            failure_count_at_step=1,
        )
    ]

    should_inv, reason = validator.should_invalidate(sample_cache_file)
    assert should_inv is False


def test_stale_cache_validator_is_stale(sample_cache_file):
    """Test validator invalidates old cache with failures."""
    validator = StaleCacheValidator(max_age_days=30)

    sample_cache_file.metadata.last_executed_at = datetime.now(tz=timezone.utc) - timedelta(days=35)
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message="Error",
            failure_count_at_step=1,
        )
    ]

    should_inv, reason = validator.should_invalidate(sample_cache_file)
    assert should_inv is True
    assert "35 days" in reason


def test_stale_cache_validator_old_but_no_failures(sample_cache_file):
    """Test validator does not invalidate old cache without failures."""
    validator = StaleCacheValidator(max_age_days=30)

    sample_cache_file.metadata.last_executed_at = datetime.now(tz=timezone.utc) - timedelta(days=100)
    sample_cache_file.metadata.failures = []

    should_inv, reason = validator.should_invalidate(sample_cache_file)
    assert should_inv is False  # Old but no failures = still valid


def test_stale_cache_validator_never_executed(sample_cache_file):
    """Test validator handles cache that was never executed."""
    validator = StaleCacheValidator(max_age_days=30)

    sample_cache_file.metadata.last_executed_at = None
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message="Error",
            failure_count_at_step=1,
        )
    ]

    should_inv, reason = validator.should_invalidate(sample_cache_file)
    assert should_inv is False  # Never executed = can't be stale


def test_stale_cache_validator_name():
    """Test validator returns correct name."""
    validator = StaleCacheValidator()
    assert validator.get_name() == "StaleCache"


# CompositeCacheValidator Tests


def test_composite_validator_empty():
    """Test composite validator with no validators."""
    validator = CompositeCacheValidator([])
    cache_file = CacheFile(
        metadata=CacheMetadata(
            version="0.1",
            created_at=datetime.now(tz=timezone.utc),
            execution_attempts=0,
            is_valid=True,
        ),
        trajectory=[],
        placeholders={},
    )

    should_inv, reason = validator.should_invalidate(cache_file)
    assert should_inv is False
    assert reason is None


def test_composite_validator_single_validator_triggers(sample_cache_file):
    """Test composite validator with one validator that triggers."""
    step_validator = StepFailureCountValidator(max_failures_per_step=2)
    composite = CompositeCacheValidator([step_validator])

    # Add 2 failures
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message=f"Error {i}",
            failure_count_at_step=i + 1,
        )
        for i in range(2)
    ]

    should_inv, reason = composite.should_invalidate(sample_cache_file, step_index=1)
    assert should_inv is True
    assert "StepFailureCount" in reason


def test_composite_validator_multiple_validators_all_pass(sample_cache_file):
    """Test composite validator when all validators pass."""
    composite = CompositeCacheValidator(
        [
            StepFailureCountValidator(max_failures_per_step=3),
            TotalFailureRateValidator(min_attempts=10, max_failure_rate=0.5),
        ]
    )

    sample_cache_file.metadata.execution_attempts = 10
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message="Error",
            failure_count_at_step=1,
        )
    ]  # 1/10 = 10% rate, and only 1 failure at step 1

    should_inv, reason = composite.should_invalidate(sample_cache_file, step_index=1)
    assert should_inv is False


def test_composite_validator_multiple_validators_one_triggers(sample_cache_file):
    """Test composite validator when one validator triggers."""
    composite = CompositeCacheValidator(
        [
            StepFailureCountValidator(max_failures_per_step=2),
            TotalFailureRateValidator(min_attempts=100, max_failure_rate=0.5),
        ]
    )

    sample_cache_file.metadata.execution_attempts = 10  # Below min_attempts
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message=f"Error {i}",
            failure_count_at_step=i + 1,
        )
        for i in range(3)
    ]  # 3 failures at step 1 (exceeds threshold of 2)

    should_inv, reason = composite.should_invalidate(sample_cache_file, step_index=1)
    assert should_inv is True
    assert "StepFailureCount" in reason
    assert "Step 1 failed 3 times" in reason


def test_composite_validator_multiple_validators_multiple_trigger(sample_cache_file):
    """Test composite validator when multiple validators trigger."""
    composite = CompositeCacheValidator(
        [
            StepFailureCountValidator(max_failures_per_step=2),
            TotalFailureRateValidator(min_attempts=5, max_failure_rate=0.5),
        ]
    )

    sample_cache_file.metadata.execution_attempts = 5
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message=f"Error {i}",
            failure_count_at_step=i + 1,
        )
        for i in range(4)
    ]  # 4/5 = 80% rate (exceeds 50%), and 4 failures at step 1 (exceeds 2)

    should_inv, reason = composite.should_invalidate(sample_cache_file, step_index=1)
    assert should_inv is True
    assert "StepFailureCount" in reason
    assert "TotalFailureRate" in reason
    assert ";" in reason  # Multiple reasons combined


def test_composite_validator_add_validator(sample_cache_file):
    """Test adding validator to composite after initialization."""
    composite = CompositeCacheValidator([])
    assert len(composite.validators) == 0

    composite.add_validator(StepFailureCountValidator(max_failures_per_step=1))
    assert len(composite.validators) == 1

    # Add failure
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message="Error",
            failure_count_at_step=1,
        )
    ]

    should_inv, reason = composite.should_invalidate(sample_cache_file, step_index=1)
    assert should_inv is True


def test_composite_validator_name():
    """Test composite validator returns correct name."""
    composite = CompositeCacheValidator([])
    assert composite.get_name() == "CompositeValidator"


# Custom Validator Tests


class CustomTestValidator(CacheValidator):
    """Custom test validator for testing extensibility."""

    def __init__(self, should_trigger: bool = False):
        self.should_trigger = should_trigger

    def should_invalidate(self, cache_file, step_index=None):
        if self.should_trigger:
            return True, "Custom validation failed"
        return False, None

    def get_name(self):
        return "CustomTest"


def test_custom_validator_integration(sample_cache_file):
    """Test that custom validators work with composite."""
    custom = CustomTestValidator(should_trigger=True)
    composite = CompositeCacheValidator([custom])

    should_inv, reason = composite.should_invalidate(sample_cache_file)
    assert should_inv is True
    assert "CustomTest" in reason
    assert "Custom validation failed" in reason


def test_custom_validator_with_built_in(sample_cache_file):
    """Test custom validator alongside built-in validators."""
    custom = CustomTestValidator(should_trigger=False)
    step_validator = StepFailureCountValidator(max_failures_per_step=1)

    composite = CompositeCacheValidator([custom, step_validator])

    # Add failure to trigger step validator
    sample_cache_file.metadata.failures = [
        CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=1,
            error_message="Error",
            failure_count_at_step=1,
        )
    ]

    should_inv, reason = composite.should_invalidate(sample_cache_file, step_index=1)
    assert should_inv is True
    assert "StepFailureCount" in reason
    assert "CustomTest" not in reason  # Custom didn't trigger
