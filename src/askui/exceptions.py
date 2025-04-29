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


__all__ = [
    "AiElementNotFound",
    "AutomationError",
    "ElementNotFoundError",
]
