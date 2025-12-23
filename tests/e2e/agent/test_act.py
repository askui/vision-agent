import pytest

from askui.agent import VisionAgent
from askui.models.models import ModelName


@pytest.mark.parametrize(
    "model_name",
    [
        None,
        f"askui/{ModelName.CLAUDE__SONNET__4__20250514}",
        ModelName.CLAUDE__SONNET__4__20250514,
        "askui/claude-sonnet-4-5-20250929",
    ],
)
def test_act(
    vision_agent: VisionAgent,
    model_name: str,
) -> None:
    vision_agent.act("Tell me a joke", model_name=model_name)
    assert True
