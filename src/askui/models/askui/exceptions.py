class AskUiApiError(Exception):
    """Base exception for AskUI API errors.

    This exception is raised when there is an error communicating with the AskUI API.
    It serves as a base class for more specific API-related exceptions.

    Args:
        message (str): The error message.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class AskUiApiRequestFailedError(AskUiApiError):
    """Exception raised when an API response is not as expected.

    This exception is raised when the API returns a response that cannot be processed
    or indicates an error condition. It includes the HTTP status code and error message
    from the API response.

    Args:
        status_code (int): The HTTP status code from the API response.
        message (str): The error message from the API response.
    """

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"API response error: {status_code} - {message}")


__all__ = [
    "AskUiApiError",
    "AskUiApiRequestFailedError",
]
