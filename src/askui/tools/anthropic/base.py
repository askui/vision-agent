from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, fields, replace
from typing import Any, Optional

from anthropic.types.beta import BetaToolParam, BetaToolUnionParam
from pydantic import Field


class BaseAnthropicTool(metaclass=ABCMeta):
    """Abstract base class for Anthropic-defined tools."""

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Executes the tool with the given arguments."""
        raise NotImplementedError

    @abstractmethod
    def to_params(
        self,
    ) -> BetaToolUnionParam:
        raise NotImplementedError


@dataclass(kw_only=True, frozen=True)
class ToolResult:
    """Represents the result of a tool execution.

    Args:
        output (str | None, optional): The output of the tool.
        error (str | None, optional): The error message of the tool.
        base64_images (list[str], optional): The base64 images of the tool.
        system (str | None, optional): The system message of the tool.
    """

    output: str | None = None
    error: str | None = None
    base64_images: list[str] = Field(default_factory=list)
    system: str | None = None

    def __bool__(self) -> bool:
        return any(getattr(self, field.name) for field in fields(self))

    def __add__(self, other: "ToolResult") -> "ToolResult":
        def combine_fields(
            field: str | None, other_field: str | None, concatenate: bool = True
        ) -> str | None:
            if field and other_field:
                if concatenate:
                    return field + other_field
                error_msg = "Cannot combine tool results"
                raise ValueError(error_msg)
            return field or other_field

        return ToolResult(
            output=combine_fields(self.output, other.output),
            error=combine_fields(self.error, other.error),
            base64_images=self.base64_images + other.base64_images,
            system=combine_fields(self.system, other.system),
        )

    def replace(self, **kwargs: Any) -> "ToolResult":
        """Returns a new ToolResult with the given fields replaced."""
        return replace(self, **kwargs)


class CLIResult(ToolResult):
    """A ToolResult that can be rendered as a CLI output."""


class ToolFailure(ToolResult):
    """A ToolResult that represents a failure."""


class ToolError(Exception):
    """Raised when a tool encounters an error.

    Args:
        message (str): The error message.
        result (ToolResult, optional): The ToolResult that caused the error.
    """

    def __init__(self, message: str, result: Optional[ToolResult] = None):
        self.message = message
        self.result = result
        super().__init__(self.message)


class Tool(BaseAnthropicTool):
    """A tool that can be used in an agent."""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any] | None = None,
    ) -> None:
        if not name:
            error_msg = "Tool name is required"
            raise ValueError(error_msg)
        if not description:
            error_msg = "Tool description is required"
            raise ValueError(error_msg)
        if not input_schema:
            input_schema = {"type": "object", "properties": {}, "required": []}
        self.name = name
        self.description = description
        self.input_schema = input_schema

    def to_params(self) -> BetaToolParam:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def __call__(self, *_args: Any, **_kwargs: Any) -> ToolResult:
        error_msg = "Tool subclasses must implement __call__ method"
        raise NotImplementedError(error_msg)


class AgentException(Exception):
    """
    Exception raised by the agent.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
