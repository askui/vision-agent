from .askui_workspaces.exceptions import (
    ApiAttributeError,
    ApiException,
    ApiKeyError,
    ApiTypeError,
    ApiValueError,
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    OpenApiException,
    ServiceException,
    UnauthorizedException,
)


class AskUIControllerError(Exception):
    """Base exception for AskUI controller errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ControllerOperationError(AskUIControllerError):
    """Exception raised when a controller operation fails."""

    def __init__(self, operation: str, error: Exception):
        super().__init__(f"Failed to {operation}: {error}")
        self.operation = operation
        self.original_error = error


class ActionTimeoutError(AskUIControllerError):
    """Exception raised when an action times out."""

    def __init__(self, message: str = "Action not yet done"):
        super().__init__(message)


__all__ = [
    "ActionTimeoutError",
    "ApiAttributeError",
    "ApiException",
    "ApiKeyError",
    "ApiTypeError",
    "ApiValueError",
    "AskUIControllerError",
    "BadRequestException",
    "ControllerOperationError",
    "ForbiddenException",
    "NotFoundException",
    "OpenApiException",
    "ServiceException",
    "UnauthorizedException",
]
