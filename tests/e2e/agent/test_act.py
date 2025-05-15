import pytest

from askui.agent import VisionAgent
from askui.models.models import ModelComposition, ModelDefinition, ModelName


@pytest.mark.parametrize(
    "model", [None, ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022]
)
def test_act(
    vision_agent: VisionAgent,
    model: str,
) -> None:
    vision_agent.act("Click anywhere on the screen (may be blank)", model=model)
    assert True


def test_act_with_model_composition_should_use_default_model(
    vision_agent: VisionAgent,
) -> None:
    vision_agent.model = ModelComposition(
        [
            ModelDefinition(
                task="e2e_ocr",
                architecture="easy_ocr",
                version="1",
                interface="online_learning",
                use_case="fb3b9a7b_3aea_41f7_ba02_e55fd66d1c1e",
                tags=["trained"],
            ),
        ],
    )
    vision_agent.act("Click anywhere on the screen (may be blank)")
    assert True
