from typing import Generator, Optional, Union

from askui.models.askui.claude_computer_agent import AskUiClaudeComputerAgent
from askui.tools.agent_os import AgentOs
import pytest
from PIL import Image as PILImage
from typing_extensions import override

from askui.reporting import Reporter


class ReporterMock(Reporter):
    @override
    def add_message(
        self,
        role: str,
        content: Union[str, dict, list],
        image: Optional[PILImage.Image | list[PILImage.Image]] = None,
    ) -> None:
        pass

    @override
    def generate(self) -> None:
        pass

@pytest.fixture
def claude_computer_agent(
    agent_os_mock: AgentOs,
) -> Generator[AskUiClaudeComputerAgent, None, None]:
    """Fixture providing a AskUiClaudeComputerAgent instance."""
    agent = AskUiClaudeComputerAgent(
        agent_os=agent_os_mock,
        reporter=ReporterMock(),
    )
    yield agent
