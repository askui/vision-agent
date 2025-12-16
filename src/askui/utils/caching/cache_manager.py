"""Cache management for tracking execution and invalidation."""

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
    """Manages cache metadata updates and validation using configurable validators."""

    def __init__(self, validators: Optional[list[CacheValidator]] = None):
        if validators is None:
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
        cache_file.metadata.execution_attempts += 1
        if success:
            cache_file.metadata.last_executed_at = datetime.now(tz=timezone.utc)
        elif failure_info:
            cache_file.metadata.failures.append(failure_info)

    def record_step_failure(
        self, cache_file: CacheFile, step_index: int, error_message: str
    ) -> None:
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
        return self.validators.should_invalidate(cache_file, step_index)

    def invalidate_cache(self, cache_file: CacheFile, reason: str) -> None:
        cache_file.metadata.is_valid = False
        cache_file.metadata.invalidation_reason = reason

    def mark_cache_valid(self, cache_file: CacheFile) -> None:
        cache_file.metadata.is_valid = True
        cache_file.metadata.invalidation_reason = None

    def get_failure_count_for_step(self, cache_file: CacheFile, step_index: int) -> int:
        return sum(
            1 for f in cache_file.metadata.failures if f.step_index == step_index
        )
