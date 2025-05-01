from typing import Any
from .models.askui.ai_element_utils import AiElementNotFound

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


class NoResponseToQueryError(AutomationError):
    """Exception raised when a query does not return a response.
    
    Args:
        message (str): The error message.
        query (str): The query that was made.
    """
    def __init__(self, message: str, query: str):
        self.message = message
        self.query = query
        super().__init__(self.message)


class UnexpectedResponseToQueryError(AutomationError):
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
    "AutomationError",
    "ElementNotFoundError",
    "NoResponseToQueryError",
    "UnexpectedResponseToQueryError",
]
