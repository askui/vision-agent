from unittest.mock import MagicMock

import pytest

from askui.callbacks import MaxStepsCallback
from askui.models.exceptions import MaxStepsReachedError


class TestMaxStepsCallback:
    def test_raises_when_step_index_equals_max_steps(self) -> None:
        callback = MaxStepsCallback(max_steps=3)
        conversation = MagicMock()
        with pytest.raises(MaxStepsReachedError, match="3 steps"):
            callback.on_step_start(conversation, step_index=3)

    def test_raises_when_step_index_exceeds_max_steps(self) -> None:
        callback = MaxStepsCallback(max_steps=3)
        conversation = MagicMock()
        with pytest.raises(MaxStepsReachedError):
            callback.on_step_start(conversation, step_index=5)

    def test_does_not_raise_when_under_limit(self) -> None:
        callback = MaxStepsCallback(max_steps=3)
        conversation = MagicMock()
        for i in range(3):
            callback.on_step_start(conversation, step_index=i)

    def test_max_steps_of_one(self) -> None:
        callback = MaxStepsCallback(max_steps=1)
        conversation = MagicMock()
        callback.on_step_start(conversation, step_index=0)
        with pytest.raises(MaxStepsReachedError):
            callback.on_step_start(conversation, step_index=1)
