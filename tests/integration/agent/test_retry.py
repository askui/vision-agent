from typing import Optional, Tuple, Union

import pytest

from askui import ConfigurableRetry, LocateModel, VisionAgent
from askui.locators.locators import Locator
from askui.models import ModelComposition
from askui.models.exceptions import ElementNotFoundError
from askui.tools.toolbox import AgentToolbox
from askui.utils.image_utils import ImageSource


class FailingLocateModel(LocateModel):
    def __init__(
        self, fail_times: int, succeed_point: Optional[Tuple[int, int]] = None
    ) -> None:
        self.fail_times = fail_times
        self.calls = 0
        if succeed_point is None:
            self.succeed_point = (10, 10)
        else:
            self.succeed_point = succeed_point

    def locate(
        self,
        locator: Union[str, Locator],
        image: ImageSource,  # noqa: ARG002
        model_choice: Union[ModelComposition, str],  # noqa: ARG002
    ) -> Tuple[int, int]:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise ElementNotFoundError(locator, locator)
        return self.succeed_point


@pytest.fixture
def failing_model() -> FailingLocateModel:
    return FailingLocateModel(fail_times=2)


@pytest.fixture
def always_failing_model() -> FailingLocateModel:
    return FailingLocateModel(fail_times=10)


@pytest.fixture
def vision_agent_with_retry(
    failing_model: FailingLocateModel, agent_toolbox_mock: AgentToolbox
) -> VisionAgent:
    return VisionAgent(
        models={"failing-locate": failing_model}, tools=agent_toolbox_mock
    )


@pytest.fixture
def vision_agent_always_fail(
    always_failing_model: FailingLocateModel, agent_toolbox_mock: AgentToolbox
) -> VisionAgent:
    return VisionAgent(
        models={"always-fail": always_failing_model},
        tools=agent_toolbox_mock,
        retry=ConfigurableRetry(
            on_exception_types=(ElementNotFoundError,),
            strategy="Fixed",
            retry_count=3,
            base_delay=1,
        ),
    )


def test_locate_retries_and_succeeds(
    vision_agent_with_retry: VisionAgent, failing_model: FailingLocateModel
) -> None:
    result = vision_agent_with_retry.locate(
        "something", screenshot=None, model="failing-locate"
    )
    assert result == (10, 10)
    assert failing_model.calls == 3  # 2 fails + 1 success


def test_locate_retries_and_fails(
    vision_agent_always_fail: VisionAgent, always_failing_model: FailingLocateModel
) -> None:
    with pytest.raises(ElementNotFoundError):
        vision_agent_always_fail.locate(
            "something", screenshot=None, model="always-fail"
        )
    assert always_failing_model.calls == 3  # Only 3 attempts


def test_click_retries(
    vision_agent_with_retry: VisionAgent, failing_model: FailingLocateModel
) -> None:
    vision_agent_with_retry.click("something", model="failing-locate")
    assert failing_model.calls == 3


def test_mouse_move_retries(
    vision_agent_with_retry: VisionAgent, failing_model: FailingLocateModel
) -> None:
    vision_agent_with_retry.mouse_move("something", model="failing-locate")
    assert failing_model.calls == 3
