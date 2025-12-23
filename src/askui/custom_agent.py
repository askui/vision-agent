from typing import Annotated

from pydantic import ConfigDict, Field, validate_call

from askui.container import telemetry
from askui.models.models import ModelName
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCb
from askui.models.shared.settings import ActSettings
from askui.models.shared.tools import Tool, ToolCollection
from askui.speaker import AskUIAgent, CacheExecutor, Conversation, Speakers

from .reporting import NullReporter


class CustomAgent:
    def __init__(self) -> None:
        reporter = NullReporter()
        self._reporter = reporter

        # Create speakers for the conversation
        # AskUIAgent will use default AskUI MessagesApi if none provided
        askui_agent_speaker = AskUIAgent()
        cache_executor_speaker = CacheExecutor()

        # Create conversation with speakers
        self._conversation = Conversation(
            speakers=Speakers(
                {
                    "AskUIAgent": askui_agent_speaker,
                    "CacheExecutor": cache_executor_speaker,
                }
            ),
            reporter=reporter,
        )

    @telemetry.record_call(exclude={"messages", "on_message", "settings", "tools"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def act(
        self,
        messages: Annotated[list[MessageParam], Field(min_length=1)],
        model: str | None = None,
        on_message: OnMessageCb | None = None,
        tools: list[Tool] | ToolCollection | None = None,
        settings: ActSettings | None = None,
    ) -> None:
        _settings = settings or ActSettings()
        _tools = self._build_tools(tools)
        # Use conversation instead of model_router
        self._conversation.start(
            messages=messages,
            model=model or ModelName.CLAUDE__SONNET__4__20250514,
            on_message=on_message,
            settings=_settings,
            tools=_tools,
        )

    def _build_tools(self, tools: list[Tool] | ToolCollection | None) -> ToolCollection:
        if isinstance(tools, list):
            return ToolCollection(tools=tools)
        if isinstance(tools, ToolCollection):
            return tools
        return ToolCollection()
