"""Cache management utilities for tracking execution and invalidation.

This module provides the CacheManager class that handles cache metadata updates,
failure tracking, and cache invalidation using configurable validation strategies.
"""

from datetime import datetime, timezone
from typing import Optional

from askui.models.shared.settings import CacheFailure, CacheFile
from askui.utils.caching.cache_validator import (
    CacheValidator,
    CompositeCacheValidator,
    StaleCacheValidator,
    StepFailureCountValidator,
    TotalFailureRateValidator,
)


class CacheManager:
    """Manages cache metadata updates and validation.

    Uses a CompositeCacheValidator for extensible invalidation logic.
    Users can provide custom validators via the validator parameter.

    Example:
        # Using default validators
        manager = CacheManager()

        # Using custom validator
        custom_validator = CompositeCacheValidator([
            StepFailureCountValidator(max_failures_per_step=5),
            MyCustomValidator()
        ])
        manager = CacheManager(validator=custom_validator)
    """

    def __init__(self, validators: Optional[list[CacheValidator]] = None):
        """Initialize cache manager.

        Args:
            validator: Custom validator or None to use default composite validator
        """
        if validators is None:
            # Default validator with built-in strategies
            self.validators = CompositeCacheValidator(
                [
                    StepFailureCountValidator(max_failures_per_step=3),
                    TotalFailureRateValidator(min_attempts=10, max_failure_rate=0.5),
                    StaleCacheValidator(max_age_days=30),
                ]
            )
        else:
            self.validators = CompositeCacheValidator(validators)

    def record_execution_attempt(
        self,
        cache_file: CacheFile,
        success: bool,
        failure_info: Optional[CacheFailure] = None,
    ) -> None:
        """Record an execution attempt and update metadata.

        Args:
            cache_file: The cache file to update
            success: Whether the execution was successful
            failure_info: Optional failure information if execution failed
        """
        cache_file.metadata.execution_attempts += 1

        if success:
            cache_file.metadata.last_executed_at = datetime.now(tz=timezone.utc)
            # Successful execution - metadata updated
        elif failure_info:
            cache_file.metadata.failures.append(failure_info)

    def record_step_failure(
        self, cache_file: CacheFile, step_index: int, error_message: str
    ) -> None:
        """Record a failure at specific step.

        Args:
            cache_file: The cache file to update
            step_index: Index of the step that failed
            error_message: Description of the error
        """
        failure = CacheFailure(
            timestamp=datetime.now(tz=timezone.utc),
            step_index=step_index,
            error_message=error_message,
            failure_count_at_step=self.get_failure_count_for_step(
                cache_file, step_index
            )
            + 1,
        )
        cache_file.metadata.failures.append(failure)

    def should_invalidate(
        self, cache_file: CacheFile, step_index: Optional[int] = None
    ) -> tuple[bool, Optional[str]]:
        """Check if cache should be invalidated using the validator.

        Args:
            cache_file: The cache file to check
            step_index: Optional step index where failure occurred

        Returns:
            Tuple of (should_invalidate: bool, reason: Optional[str])
        """
        return self.validators.should_invalidate(cache_file, step_index)

    def invalidate_cache(self, cache_file: CacheFile, reason: str) -> None:
        """Mark cache as invalid.

        Args:
            cache_file: The cache file to invalidate
            reason: Reason for invalidation
        """
        cache_file.metadata.is_valid = False
        cache_file.metadata.invalidation_reason = reason

    def mark_cache_valid(self, cache_file: CacheFile) -> None:
        """Mark cache as valid.

        Args:
            cache_file: The cache file to mark as valid
        """
        cache_file.metadata.is_valid = True
        cache_file.metadata.invalidation_reason = None

    def get_failure_count_for_step(self, cache_file: CacheFile, step_index: int) -> int:
        """Get number of failures for a specific step.

        Args:
            cache_file: The cache file to check
            step_index: Index of the step to count failures for

        Returns:
            Number of failures at this step
        """
        return sum(
            1 for f in cache_file.metadata.failures if f.step_index == step_index
        )
