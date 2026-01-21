from askui.agent import VisionAgent


def test_act(
    vision_agent: VisionAgent,
) -> None:
    vision_agent.act("Tell me a joke")
    assert True
