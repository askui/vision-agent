from abc import ABC, abstractmethod
from typing import Any, Literal, cast

from anthropic.types.beta import BetaToolParam, BetaToolUnionParam
from anthropic.types.beta.beta_tool_param import InputSchema
from asyncer import syncify
from fastmcp import Client
from fastmcp.client.client import CallToolResult
from fastmcp.client.transports import ClientTransportT
from mcp import Tool as McpTool
from PIL import Image
from pydantic import BaseModel, Field
from typing_extensions import Self

from askui.logger import logger
from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    ContentBlockParam,
    ImageBlockParam,
    TextBlockParam,
    ToolResultBlockParam,
    ToolUseBlockParam,
)
from askui.utils.image_utils import ImageSource

PrimitiveToolCallResult = Image.Image | None | str | BaseModel

ToolCallResult = (
    PrimitiveToolCallResult
    | list[PrimitiveToolCallResult]
    | tuple[PrimitiveToolCallResult, ...]
    | CallToolResult
)


IMAGE_MEDIA_TYPES_SUPPORTED: list[
    Literal["image/jpeg", "image/png", "image/gif", "image/webp"]
] = ["image/jpeg", "image/png", "image/gif", "image/webp"]


def _convert_to_content(
    result: ToolCallResult,
) -> list[TextBlockParam | ImageBlockParam]:
    if result is None:
        return []

    if isinstance(result, CallToolResult):
        _result: list[TextBlockParam | ImageBlockParam] = []
        for block in result.content:
            match block.type:
                case "text":
                    _result.append(TextBlockParam(text=block.text))  # type: ignore[union-attr]
                case "image":
                    media_type = block.mimeType  # type: ignore[union-attr]
                    if media_type not in IMAGE_MEDIA_TYPES_SUPPORTED:
                        logger.error(f"Unsupported image media type: {media_type}")
                        continue
                    _result.append(
                        ImageBlockParam(
                            source=Base64ImageSourceParam(
                                media_type=media_type,
                                data=result.data,
                            )
                        )
                    )
                case _:
                    logger.error(f"Unsupported block type: {block.type}")
        return _result

    if isinstance(result, str):
        return [TextBlockParam(text=result)]

    if isinstance(result, list | tuple):
        return [
            item
            for sublist in [_convert_to_content(item) for item in result]
            for item in sublist
        ]

    if isinstance(result, BaseModel):
        return [TextBlockParam(text=result.model_dump_json())]

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

    Args:
        tools (list[Tool] | None, optional): The tools to add to the collection.
            Defaults to `None`.
        mcp_client (Client[ClientTransportT] | None, optional): The client to use for
            the tools. Defaults to `None`.
    """

    def __init__(
        self,
        tools: list[Tool] | None = None,
        mcp_client: Client[ClientTransportT] | None = None,
    ) -> None:
        _tools = tools or []
        self._tool_map = {tool.to_params()["name"]: tool for tool in _tools}
        self._mcp_client = mcp_client
        self._mcp_tools_cache: dict[str, McpTool] | None = None

    def to_params(self) -> list[BetaToolUnionParam]:
        return self._get_mcp_tool_params() + [
            tool.to_params() for tool in self._tool_map.values()
        ]

    def _get_mcp_tool_params(self) -> list[BetaToolUnionParam]:
        if not self._mcp_client:
            return []
        mcp_tools = self._get_mcp_tools()
        return [
            cast(
                "BetaToolUnionParam",
                BetaToolParam(
                    name=tool_name,
                    description=tool.description or "",
                    input_schema=tool.inputSchema,
                ),
            )
            for tool_name, tool in mcp_tools.items()
        ]

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
        if tool:
            return self._run_regular_tool(tool_use_block_param, tool)
        mcp_tool = self._get_mcp_tools().get(tool_use_block_param.name)
        if mcp_tool:
            return self._run_mcp_tool(tool_use_block_param)
        return ToolResultBlockParam(
            content=f"Tool not found: {tool_use_block_param.name}",
            is_error=True,
            tool_use_id=tool_use_block_param.id,
        )

    def _get_mcp_tools(self) -> dict[str, McpTool]:
        """Get cached MCP tools or fetch them if not cached."""
        try:
            if not self._mcp_client:
                return {}
            tools_list = syncify(self._mcp_client.list_tools, raise_sync_error=False)()
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to list MCP tools: {e}", exc_info=True)
            return {}
        else:
            return {tool.name: tool for tool in tools_list}

    def _run_regular_tool(
        self,
        tool_use_block_param: ToolUseBlockParam,
        tool: Tool,
    ) -> ToolResultBlockParam:
        try:
            tool_result: ToolCallResult = tool(**tool_use_block_param.input)  # type: ignore
            return ToolResultBlockParam(
                content=_convert_to_content(tool_result),
                tool_use_id=tool_use_block_param.id,
            )
        except AgentException:
            raise
        except Exception as e:  # noqa: BLE001
            logger.error(f"Tool {tool_use_block_param.name} failed: {e}", exc_info=True)
            return ToolResultBlockParam(
                content=f"Tool {tool_use_block_param.name} failed: {e}",
                is_error=True,
                tool_use_id=tool_use_block_param.id,
            )

    def _run_mcp_tool(
        self,
        tool_use_block_param: ToolUseBlockParam,
    ) -> ToolResultBlockParam:
        """Run an MCP tool using the client."""
        if not self._mcp_client:
            return ToolResultBlockParam(
                content="MCP client not available",
                is_error=True,
                tool_use_id=tool_use_block_param.id,
            )
        try:
            result = syncify(self._mcp_client.call_tool, raise_sync_error=False)(
                tool_use_block_param.name,
                tool_use_block_param.input,  # type: ignore[arg-type]
            )
            return ToolResultBlockParam(
                content=_convert_to_content(result),
                tool_use_id=tool_use_block_param.id,
            )
        except Exception as e:  # noqa: BLE001
            logger.error(
                f"MCP tool {tool_use_block_param.name} failed: {e}", exc_info=True
            )
            return ToolResultBlockParam(
                content=f"MCP tool {tool_use_block_param.name} failed: {e}",
                is_error=True,
                tool_use_id=tool_use_block_param.id,
            )
