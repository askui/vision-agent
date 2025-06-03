import pytest

from askui.agent import VisionAgent
from askui.reporting import CompositeReporter
from askui.tools.agent_os import AgentOs
from askui.tools.pynput.pynput_agent_os import PynputAgentOs
from askui.tools.toolbox import AgentToolbox


@pytest.fixture
def pynput_agent_os() -> AgentOs:
    return PynputAgentOs(reporter=CompositeReporter())


def test_mouse_move(pynput_agent_os: AgentOs) -> None:
    with VisionAgent(tools=AgentToolbox(agent_os=pynput_agent_os)) as agent:
        agent.act("Clicking the 'Access Tokens' option in the left sidebar")
    assert True
