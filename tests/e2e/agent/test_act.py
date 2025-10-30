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
        f"askui/{ModelName.CLAUDE__SONNET__4__20250514}",
        ModelName.CLAUDE__SONNET__4__20250514,
        "askui/claude-sonnet-4-5-20250929",
    ],
)
def test_act(
    vision_agent: VisionAgent,
    model: str,
) -> None:
    vision_agent.act("Tell me a joke", model=model)
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
        vision_agent.act("Tell me a joke")
        assert True
