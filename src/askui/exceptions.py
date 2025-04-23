class AutomationError(Exception):
    """Exception raised when the automation step cannot complete."""
    pass


class ElementNotFoundError(AutomationError):
    """Exception raised when an element cannot be located."""
    pass
