from typing import Annotated

from pydantic import ConfigDict, Field, validate_call

from askui.container import telemetry
from askui.models.defaults import default_act_model
from askui.models.models import ActModel
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCb
from askui.models.shared.settings import ActSettings
from askui.models.shared.tools import Tool, ToolCollection


class CustomAgent:
    """Custom agent for headless agentic tasks without OS integration."""

    def __init__(self, act_model: ActModel | None = None) -> None:
        self._act_model = act_model or default_act_model()
        self.act_settings = ActSettings()

    @telemetry.record_call(exclude={"messages", "on_message", "settings", "tools"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def act(
        self,
        messages: Annotated[list[MessageParam], Field(min_length=1)],
        on_message: OnMessageCb | None = None,
        tools: list[Tool] | ToolCollection | None = None,
        settings: ActSettings | None = None,
    ) -> None:
        _settings = settings or self.act_settings
        _tools = self._build_tools(tools)
        self._act_model.act(
            messages=messages,
            act_settings=_settings,
            on_message=on_message,
            tools=_tools,
        )

    def _build_tools(self, tools: list[Tool] | ToolCollection | None) -> ToolCollection:
        if isinstance(tools, list):
            return ToolCollection(tools=tools)
        if isinstance(tools, ToolCollection):
            return tools
        return ToolCollection()
