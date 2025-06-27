import pytest

from askui.models.models import ModelName
from askui.models.shared.agent import Agent
from askui.models.shared.agent_message_param import MessageParam


@pytest.mark.skip(
    "Skip for now as the conversation between the agent and the user needs to be separated first"  # noqa: E501
)
def test_act(
    claude_computer_agent: Agent,
) -> None:
    claude_computer_agent.act(
        [MessageParam(role="user", content="Go to github.com/login")],
        model_choice=ModelName.ASKUI,
    )
