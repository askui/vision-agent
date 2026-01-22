from .anthropic_get_model import AnthropicGetModel
from .gemini_get_model import AskUiGeminiGetModel

# AskUiGetModel is an alias for AskUiGeminiGetModel
# In the future, this might point to a different default model
AskUiGetModel = AskUiGeminiGetModel

__all__ = [
    "AskUiGetModel",
    "AskUiGeminiGetModel",
    "AnthropicGetModel",
]
