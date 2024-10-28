class AutomationError(Exception):
    """Exception raised when the automation step cannot complete."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
