from abc import ABC, abstractmethod
from typing import Any, cast

from anthropic.types.beta import BetaToolUnionParam
from PIL import Image

from askui.models.shared.computer_agent_message_param import (
    Base64ImageSourceParam,
    ContentBlockParam,
    ImageBlockParam,
    TextBlockParam,
    ToolResultBlockParam,
    ToolUseBlockParam,
)
from askui.utils.image_utils import ImageSource

ToolCallResult = Image.Image | None


def _convert_to_content(
    result: ToolCallResult,
) -> list[TextBlockParam | ImageBlockParam]:
    if result is None:
        return []

    return [
        ImageBlockParam(
            source=Base64ImageSourceParam(
                media_type="image/png",
                data=ImageSource(result).to_base64(),
            )
        )
    ]


class Tool(ABC):
    """Abstract base class for tools."""

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> ToolCallResult:
        """Executes the tool with the given arguments."""
        raise NotImplementedError

    @abstractmethod
    def to_params(
        self,
    ) -> BetaToolUnionParam:
        raise NotImplementedError


class ToolCollection:
    """A collection of tools.

    Use for dispatching tool calls

    Vision:
    - Could be used for parallelizing tool calls configurable through init arg
    - Could be used for raising on an exception
      (instead of just returning `ContentBlockParam`)
      within tool call or doing tool call or if tool is not found
    """

    def __init__(self, tools: list[Tool]) -> None:
        self._tools = tools
        self._tool_map = {tool.to_params()["name"]: tool for tool in tools}

    def to_params(
        self,
    ) -> list[BetaToolUnionParam]:
        return [tool.to_params() for tool in self._tools]

    def run(
        self, tool_use_block_params: list[ToolUseBlockParam]
    ) -> list[ContentBlockParam]:
        return [
            self._run_tool(tool_use_block_param)
            for tool_use_block_param in tool_use_block_params
        ]

    def _run_tool(
        self, tool_use_block_param: ToolUseBlockParam
    ) -> ToolResultBlockParam:
        tool = self._tool_map.get(tool_use_block_param.name)
        if not tool:
            return ToolResultBlockParam(
                content=f"Tool not found: {tool_use_block_param.name}",
                is_error=True,
                tool_use_id=tool_use_block_param.id,
            )
        try:
            tool_result: ToolCallResult = cast(
                "ToolCallResult",
                tool(**tool_use_block_param.input),  # type: ignore
            )
            return ToolResultBlockParam(
                content=_convert_to_content(tool_result),
                tool_use_id=tool_use_block_param.id,
            )
        except Exception as e:  # noqa: BLE001
            return ToolResultBlockParam(
                content=f"Tool {tool_use_block_param.name} failed: {e}",
                is_error=True,
                tool_use_id=tool_use_block_param.id,
            )
