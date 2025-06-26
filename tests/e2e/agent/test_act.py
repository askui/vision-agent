import pytest

from askui.agent import VisionAgent
from askui.models.models import ModelComposition, ModelDefinition, ModelName
from askui.models.shared.facade import ModelFacade
from askui.reporting import Reporter
from askui.tools.toolbox import AgentToolbox


@pytest.mark.parametrize(
    "model",
    [
        None,
        ModelName.ASKUI,
        ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022,
        ModelName.CLAUDE__SONNET__4__20250514,
    ],
)
def test_act(
    vision_agent: VisionAgent,
    model: str,
) -> None:
    vision_agent.act("Click anywhere on the screen (may be blank)", model=model)
    assert True


def test_act_with_model_composition_should_use_default_model(
    agent_toolbox_mock: AgentToolbox,
    simple_html_reporter: Reporter,
    askui_facade: ModelFacade,
) -> None:
    with VisionAgent(
        reporters=[simple_html_reporter],
        models={
            ModelName.ASKUI: askui_facade,
        },
        model=ModelComposition(
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
        ),
        tools=agent_toolbox_mock,
    ) as vision_agent:
        vision_agent.act("Click anywhere on the screen (may be blank)")
        assert True
