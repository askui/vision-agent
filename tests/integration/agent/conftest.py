from typing import Any, Generator, Optional, Union

import pytest
from PIL import Image as PILImage
from typing_extensions import override

from askui.models.askui.messages_api import AskUiMessagesApi
from askui.models.askui.settings import AskUiComputerAgentSettings, AskUiSettings
from askui.models.shared.agent import Agent
from askui.models.shared.prompts import SYSTEM_PROMPT
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
) -> Generator[Agent, None, None]:
    """Fixture providing a AskUiClaudeComputerAgent instance."""
    settings = AskUiComputerAgentSettings(askui=AskUiSettings())
    agent = Agent(
        tool_collection=ToolCollection(tools=[Computer20241022Tool(agent_os_mock)]),
        reporter=ReporterMock(),
        settings=settings,
        messages_api=AskUiMessagesApi(
            settings=settings,
            tool_collection=ToolCollection(tools=[Computer20241022Tool(agent_os_mock)]),
            system_prompt=SYSTEM_PROMPT,
        ),
        system_prompt=SYSTEM_PROMPT,
    )
    yield agent
