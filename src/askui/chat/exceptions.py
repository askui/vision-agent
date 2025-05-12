"""Exceptions for the chat module."""


class ChatError(Exception):
    """Base exception for chat-related errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class InvalidFunctionError(ChatError):
    """Exception raised when an invalid function is called."""

    def __init__(self, function_name: str):
        super().__init__(f"Invalid function: {function_name}")


class FunctionExecutionError(ChatError):
    """Exception raised when a function execution fails."""

    def __init__(self, function_name: str, error: Exception):
        super().__init__(f"Error executing {function_name}: {str(error)}")
        self.original_error = error


class AnnotationError(ChatError):
    """Exception raised when annotation is not done or invalid."""

    def __init__(self, message: str = "No annotation Done!"):
        super().__init__(message)


class ActionTimeoutError(ChatError):
    """Exception raised when an action times out."""

    def __init__(self, message: str = "Action not yet done"):
        super().__init__(message)


__all__ = [
    "ChatError",
    "InvalidFunctionError",
    "FunctionExecutionError",
    "AnnotationError",
    "ActionTimeoutError",
]
