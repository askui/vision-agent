from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, fields, replace
from typing import Any, Optional

from anthropic.types.beta import BetaToolUnionParam


class BaseAnthropicTool(metaclass=ABCMeta):
    """Abstract base class for Anthropic-defined tools."""

    @abstractmethod
    def __call__(self, **kwargs: Any) -> Any:
        """Executes the tool with the given arguments."""
        ...

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
        base64_image (str | None, optional): The base64 image of the tool.
        system (str | None, optional): The system message of the tool.
    """

    output: str | None = None
    error: str | None = None
    base64_image: str | None = None
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
            base64_image=combine_fields(self.base64_image, other.base64_image, False),
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
