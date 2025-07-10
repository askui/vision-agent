from abc import ABC, abstractmethod
from typing import Any, cast

from anthropic.types.beta import BetaToolParam, BetaToolUnionParam
from anthropic.types.beta.beta_tool_param import InputSchema
from PIL import Image
from pydantic import BaseModel, Field
from typing_extensions import Self

from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    ContentBlockParam,
    ImageBlockParam,
    TextBlockParam,
    ToolResultBlockParam,
    ToolUseBlockParam,
)
from askui.utils.image_utils import ImageSource

PrimitiveToolCallResult = Image.Image | None | str

ToolCallResult = (
    PrimitiveToolCallResult
    | list[PrimitiveToolCallResult]
    | tuple[PrimitiveToolCallResult, ...]
)


def _convert_to_content(
    result: ToolCallResult,
) -> list[TextBlockParam | ImageBlockParam]:
    if result is None:
        return []

    if isinstance(result, str):
        return [TextBlockParam(text=result)]

    if isinstance(result, list | tuple):
        return [
            item
            for sublist in [_convert_to_content(item) for item in result]
            for item in sublist
        ]

    return [
        ImageBlockParam(
            source=Base64ImageSourceParam(
                media_type="image/png",
                data=ImageSource(result).to_base64(),
            )
        )
    ]


def _default_input_schema() -> InputSchema:
    return {"type": "object", "properties": {}, "required": []}


class Tool(BaseModel, ABC):
    name: str = Field(description="Name of the tool")
    description: str = Field(description="Description of what the tool does")
    input_schema: InputSchema = Field(
        default_factory=_default_input_schema,
        description="JSON schema for tool parameters",
    )

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> ToolCallResult:
        """Executes the tool with the given arguments."""
        error_msg = "Tool subclasses must implement __call__ method"
        raise NotImplementedError(error_msg)

    def to_params(
        self,
    ) -> BetaToolUnionParam:
        return BetaToolParam(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
        )


class AgentException(Exception):
    """
    Exception raised by the agent.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ToolCollection:
    """A collection of tools.

    Use for dispatching tool calls

    **Important**: Tools must have unique names. A tool with the same name as a tool
    added before will override the tool added before.


    Vision:
    - Could be used for parallelizing tool calls configurable through init arg
    - Could be used for raising on an exception
      (instead of just returning `ContentBlockParam`)
      within tool call or doing tool call or if tool is not found
    """

    def __init__(self, tools: list[Tool] | None = None) -> None:
        _tools = tools or []
        self._tool_map = {tool.to_params()["name"]: tool for tool in _tools}

    def to_params(self) -> list[BetaToolUnionParam]:
        return [tool.to_params() for tool in self._tool_map.values()]

    def append_tool(self, *tools: Tool) -> "Self":
        """Append a tool to the collection."""
        for tool in tools:
            self._tool_map[tool.to_params()["name"]] = tool
        return self

    def reset_tools(self, tools: list[Tool] | None = None) -> "Self":
        """Reset the tools in the collection with new tools."""
        _tools = tools or []
        self._tool_map = {tool.to_params()["name"]: tool for tool in _tools}
        return self

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
        except AgentException:
            raise
        except Exception as e:  # noqa: BLE001
            return ToolResultBlockParam(
                content=f"Tool {tool_use_block_param.name} failed: {e}",
                is_error=True,
                tool_use_id=tool_use_block_param.id,
            )
