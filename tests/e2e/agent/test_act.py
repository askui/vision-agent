from askui.agent import ComputerAgent


def test_act(
    vision_agent: ComputerAgent,
) -> None:
    vision_agent.act("Tell me a joke")
    assert True
