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


class AskUiControllerError(Exception):
    """Base exception for AskUI controller errors.

    This exception is raised when there is an error in the AskUI controller (client),
    which handles the communication with the AskUI controller (server).

    Args:
        message (str): The error message.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AskUiControllerOperationFailedError(AskUiControllerError):
    """Exception raised when a controller operation fails.

    This exception is raised when a specific operation in the AskUI controller
    fails, such as starting/stopping the controller or executing an action.

    Args:
        operation (str): The operation that failed.
        error (Exception): The original error that caused the failure.
    """

    def __init__(self, operation: str, error: Exception):
        super().__init__(f"Failed to {operation}: {error}")
        self.operation = operation
        self.original_error = error


class AskUiControllerOperationTimeoutError(AskUiControllerError):
    """Exception raised when a controller action times out.

    This exception is raised when an action in the AskUI controller takes longer
    than the expected timeout period to complete.

    Args:
        message (str): The error message.
        timeout_seconds (float | None): Optional timeout duration in seconds.
    """

    def __init__(
        self, message: str = "Action not yet done", timeout_seconds: float | None = None
    ):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


__all__ = [
    "ApiAttributeError",
    "ApiException",
    "ApiKeyError",
    "ApiTypeError",
    "ApiValueError",
    "AskUiControllerError",
    "AskUiControllerOperationFailedError",
    "AskUiControllerOperationTimeoutError",
    "BadRequestException",
    "ForbiddenException",
    "NotFoundException",
    "OpenApiException",
    "ServiceException",
    "UnauthorizedException",
]
