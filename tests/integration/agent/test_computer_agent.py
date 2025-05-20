import pytest

from askui.models.askui.claude_computer_agent import AskUiClaudeComputerAgent


@pytest.mark.skip(
    "Skip for now as the conversation between the agent and the user needs to be separated first"
)
def test_act(
    claude_computer_agent: AskUiClaudeComputerAgent,
) -> None:
    response = claude_computer_agent.act("Go to github.com/login")
    assert response is not None
