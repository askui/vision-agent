import pytest

from askui.models.askui.askui_computer_agent import AskUiComputerAgent


@pytest.mark.skip(
    "Skip for now as the conversation between the agent and the user needs to be separated first"  # noqa: E501
)
def test_act(
    claude_computer_agent: AskUiComputerAgent,
) -> None:
    claude_computer_agent.act("Go to github.com/login")
