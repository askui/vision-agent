"""AskUI locate model implementations."""

from .ai_element_locate_model import AskUiAiElementLocateModel
from .anthropic_locate_model import AnthropicLocateModel
from .combo_locate_model import AskUiComboLocateModel
from .ocr_locate_model import AskUiOcrLocateModel
from .pta_locate_model import AskUiPtaLocateModel
from .text_locate_model import TextLocateModel

# AskUiLocateModel is an alias for TextLocateModel
# In the future, this might point to a different default model
AskUiLocateModel = TextLocateModel

__all__ = [
    "AskUiLocateModel",
    "AskUiAiElementLocateModel",
    "AnthropicLocateModel",
    "TextLocateModel",
    "AskUiComboLocateModel",
    "AskUiOcrLocateModel",
    "AskUiPtaLocateModel",
]
