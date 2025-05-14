from askui.exceptions import AutomationError
from askui.models.models import ModelComposition


class InvalidModelError(AutomationError):
    """Exception raised when an invalid model is used.

    Args:
        model (str | ModelComposition): The model that was used.
    """

    def __init__(self, model: str | ModelComposition):
        self.model = model
        model_str = model if isinstance(model, str) else model.model_dump_json()
        super().__init__(f"Invalid model: {model_str}")
