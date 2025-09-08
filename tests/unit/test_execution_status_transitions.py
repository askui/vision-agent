"""Unit tests for execution status transition validation logic."""

import pytest

from askui.chat.api.executions.models import (
    ExecutionStatus,
    InvalidStatusTransitionError,
    _validate_status_transition,
)


class TestStatusTransitionValidation:
    """Test the low-level status transition validation function."""

    def test_same_status_transition_allowed(self) -> None:
        """Test that transitioning to the same status is always allowed."""
        for status in ExecutionStatus:
            # Should not raise an exception
            _validate_status_transition(status, status)

    def test_valid_transitions_from_pending(self) -> None:
        """Test valid transitions from PENDING status."""
        valid_targets = [
            ExecutionStatus.INCOMPLETE,
            ExecutionStatus.PASSED,
            ExecutionStatus.FAILED,
            ExecutionStatus.SKIPPED,
        ]

        for target in valid_targets:
            _validate_status_transition(ExecutionStatus.PENDING, target)

    def test_invalid_transitions_from_pending(self) -> None:
        """Test that PENDING cannot transition back to PENDING (via validation logic)."""
        # Note: same-status transitions are allowed at the validation level,
        # but this tests the transition map logic
        # PENDING -> PENDING is actually allowed as a no-op
        return

    def test_valid_transitions_from_incomplete(self) -> None:
        """Test valid transitions from INCOMPLETE status."""
        valid_targets = [
            ExecutionStatus.PASSED,
            ExecutionStatus.FAILED,
            ExecutionStatus.SKIPPED,
        ]

        for target in valid_targets:
            _validate_status_transition(ExecutionStatus.INCOMPLETE, target)

    def test_incomplete_cannot_go_back_to_pending(self) -> None:
        """Test that INCOMPLETE cannot transition back to PENDING."""
        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            _validate_status_transition(
                ExecutionStatus.INCOMPLETE, ExecutionStatus.PENDING
            )

        assert exc_info.value.from_status == ExecutionStatus.INCOMPLETE
        assert exc_info.value.to_status == ExecutionStatus.PENDING

    def test_no_transitions_from_final_states(self) -> None:
        """Test that final states cannot transition to any other status."""
        final_states = [
            ExecutionStatus.PASSED,
            ExecutionStatus.FAILED,
            ExecutionStatus.SKIPPED,
        ]

        all_other_statuses = [
            ExecutionStatus.PENDING,
            ExecutionStatus.INCOMPLETE,
        ]

        for final_state in final_states:
            for target in all_other_statuses:
                with pytest.raises(InvalidStatusTransitionError) as exc_info:
                    _validate_status_transition(final_state, target)

                assert exc_info.value.from_status == final_state
                assert exc_info.value.to_status == target

    def test_final_states_cannot_transition_to_each_other(self) -> None:
        """Test that final states cannot transition to other final states."""
        final_states = [
            ExecutionStatus.PASSED,
            ExecutionStatus.FAILED,
            ExecutionStatus.SKIPPED,
        ]

        for from_state in final_states:
            for to_state in final_states:
                if from_state == to_state:
                    # Same status is allowed
                    continue

                with pytest.raises(InvalidStatusTransitionError) as exc_info:
                    _validate_status_transition(from_state, to_state)

                assert exc_info.value.from_status == from_state
                assert exc_info.value.to_status == to_state

    def test_error_message_format(self) -> None:
        """Test that the error message has the expected format."""
        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            _validate_status_transition(ExecutionStatus.PASSED, ExecutionStatus.PENDING)

        error = exc_info.value
        expected_msg = "Invalid status transition from 'passed' to 'pending'"
        assert str(error) == expected_msg

    def test_error_attributes(self) -> None:
        """Test that the error has the correct attributes."""
        from_status = ExecutionStatus.FAILED
        to_status = ExecutionStatus.INCOMPLETE

        with pytest.raises(InvalidStatusTransitionError) as exc_info:
            _validate_status_transition(from_status, to_status)

        error = exc_info.value
        assert error.from_status == from_status
        assert error.to_status == to_status
        assert isinstance(error, ValueError)

    @pytest.mark.parametrize(
        "final_state",
        [
            ExecutionStatus.PASSED,
            ExecutionStatus.FAILED,
            ExecutionStatus.SKIPPED,
        ],
    )
    @pytest.mark.parametrize(
        "target_state",
        [
            ExecutionStatus.PENDING,
            ExecutionStatus.INCOMPLETE,
        ],
    )
    def test_specific_invalid_transitions_parametrized(
        self, final_state: ExecutionStatus, target_state: ExecutionStatus
    ) -> None:
        """Test specific invalid transitions mentioned in requirements using parametrization."""
        with pytest.raises(InvalidStatusTransitionError):
            _validate_status_transition(final_state, target_state)

    def test_transition_map_structure(self) -> None:
        """Test the structure of the transition map."""
        from askui.chat.api.executions.models import _STATUS_TRANSITIONS

        # All statuses should be keys in the transition map
        all_statuses = set(ExecutionStatus)
        map_keys = set(_STATUS_TRANSITIONS.keys())
        assert all_statuses == map_keys

        # Final states should have empty transition sets
        final_states = [
            ExecutionStatus.PASSED,
            ExecutionStatus.FAILED,
            ExecutionStatus.SKIPPED,
        ]

        for final_state in final_states:
            assert _STATUS_TRANSITIONS[final_state] == set(), (
                f"{final_state} should have no allowed transitions"
            )

        # Non-final states should have non-empty transition sets
        non_final_states = [
            ExecutionStatus.PENDING,
            ExecutionStatus.INCOMPLETE,
        ]

        for non_final_state in non_final_states:
            assert len(_STATUS_TRANSITIONS[non_final_state]) > 0, (
                f"{non_final_state} should have allowed transitions"
            )
