"""Collection classes for managing multiple tools."""

from typing import Any, cast

from anthropic.types.beta import BetaToolUnionParam

from .base import AgentException, BaseAnthropicTool, ToolError, ToolFailure, ToolResult


class ToolCollection:
    """A collection of anthropic-defined tools."""

    def __init__(self, tools: list[BaseAnthropicTool]):
        self.tools = tools
        self.tool_map = {tool.to_params()["name"]: tool for tool in tools}

    def to_params(
        self,
    ) -> list[BetaToolUnionParam]:
        return [tool.to_params() for tool in self.tools]

    def add_tool(self, tool: BaseAnthropicTool) -> None:
        """Add a tool to the collection."""
        self.tools.append(tool)
        self.tool_map[tool.to_params()["name"]] = tool

    def run(self, *, name: str, tool_input: dict[str, Any]) -> ToolResult:
        tool = self.tool_map.get(name)
        if not tool:
            return ToolFailure(error=f"Tool {name} is invalid")
        try:
            return cast("ToolResult", tool(**tool_input))
        except AgentException as e:
            raise e  # noqa: TRY201
        except ToolError as e:
            return ToolFailure(error=e.message)
        except Exception as e:  # noqa: BLE001
            error_message = f"Unexpected error occurred with tool {name}: {e}"
            return ToolFailure(error=error_message)
