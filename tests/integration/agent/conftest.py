from typing import Any, Generator, Optional, Union

import pytest
from PIL import Image as PILImage
from typing_extensions import override

from askui.models.askui.computer_agent import AskUiComputerAgent
from askui.models.askui.settings import AskUiComputerAgentSettings, AskUiSettings
from askui.models.shared.tools import ToolCollection
from askui.reporting import Reporter
from askui.tools.agent_os import AgentOs
from askui.tools.computer import Computer20241022Tool


class ReporterMock(Reporter):
    @override
    def add_message(
        self,
        role: str,
        content: Union[str, dict[str, Any], list[Any]],
        image: Optional[PILImage.Image | list[PILImage.Image]] = None,
    ) -> None:
        pass

    @override
    def generate(self) -> None:
        pass


@pytest.fixture
def claude_computer_agent(
    agent_os_mock: AgentOs,
) -> Generator[AskUiComputerAgent, None, None]:
    """Fixture providing a AskUiClaudeComputerAgent instance."""
    agent = AskUiComputerAgent(
        tool_collection=ToolCollection(tools=[Computer20241022Tool(agent_os_mock)]),
        reporter=ReporterMock(),
        settings=AskUiComputerAgentSettings(askui=AskUiSettings()),
    )
    yield agent
