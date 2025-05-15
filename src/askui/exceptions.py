from typing import Any, Literal

from askui.models.models import ModelComposition

from .models.askui.ai_element_utils import AiElementNotFound
from .models.askui.exceptions import (
    AskUiApiError,
    AskUiApiRequestFailedError,
)


class AutomationError(Exception):
    """Exception raised when the automation step cannot complete.

    Args:
        message (str): The error message.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ElementNotFoundError(AutomationError):
    """Exception raised when an element cannot be located.

    Args:
        message (str): The error message.
    """

    def __init__(self, message: str):
        super().__init__(message)


class ModelNotFoundError(AutomationError):
    """Exception raised when an invalid model is used.

    Args:
        model (str | ModelComposition): The model that was used.
    """

    def __init__(
        self,
        model: str | ModelComposition,
        model_type: Literal["Act", "Grounding (locate)", "Query (get/extract)"],
    ):
        self.model = model
        model_str = model if isinstance(model, str) else model.model_dump_json()
        super().__init__(f"{model_type} model not found: {model_str}")


class QueryNoResponseError(AutomationError):
    """Exception raised when a query does not return a response.

    Args:
        message (str): The error message.
        query (str): The query that was made.
    """

    def __init__(self, message: str, query: str):
        self.message = message
        self.query = query
        super().__init__(self.message)


class QueryUnexpectedResponseError(AutomationError):
    """Exception raised when a query returns an unexpected response.

    Args:
        message (str): The error message.
        query (str): The query that was made.
        response (Any): The response that was received.
    """

    def __init__(self, message: str, query: str, response: Any):
        self.message = message
        self.query = query
        self.response = response
        super().__init__(self.message)


__all__ = [
    "AiElementNotFound",
    "AskUiApiError",
    "AskUiApiRequestFailedError",
    "AutomationError",
    "ElementNotFoundError",
    "ModelNotFoundError",
    "QueryNoResponseError",
    "QueryUnexpectedResponseError",
]
