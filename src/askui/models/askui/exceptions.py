class AskUiApiError(Exception):
    """Base exception for AskUI API errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class TokenNotSetError(AskUiApiError):
    """Exception raised when a token is not set."""

    def __init__(self, message: str = "Token not set") -> None:
        super().__init__(message)


class ApiResponseError(AskUiApiError):
    """Exception raised when an API response is not as expected."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"API response error: {status_code} - {message}")


__all__ = [
    "AskUiApiError",
    "TokenNotSetError",
    "ApiResponseError",
]
