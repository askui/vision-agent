from typing import Annotated

from pydantic import ConfigDict, Field, validate_call

from askui.container import telemetry
from askui.models.models import ModelName
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCb
from askui.models.shared.messages_api_provider import MessagesApiProvider
from askui.models.shared.settings import ActSettings
from askui.models.shared.tools import Tool, ToolCollection
from askui.speaker import AskUIAgent, CacheExecutor, Conversation, Speakers

from .models.model_router import ModelRouter, initialize_default_model_registry
from .reporting import NullReporter


class CustomAgent:
    def __init__(self) -> None:
        reporter = NullReporter()
        self._reporter = reporter

        # Create model router for get/locate operations (no act)
        self._model_router = self._init_model_router(reporter)

        # Create MessagesApiProvider for handling different model providers
        messages_api_provider = MessagesApiProvider()

        # Create speakers for the conversation
        askui_agent_speaker = AskUIAgent(messages_api_provider)
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

    def _init_model_router(
        self,
        reporter: NullReporter,
    ) -> ModelRouter:
        models = initialize_default_model_registry(
            reporter=reporter,
        )
        return ModelRouter(
            reporter=reporter,
            models=models,
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
