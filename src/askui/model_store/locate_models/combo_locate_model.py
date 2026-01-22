import logging

from typing_extensions import override

from askui.locators.locators import Locator, Prompt, Text
from askui.models.askui.models import AskUiBaseLocateModel
from askui.models.exceptions import (
    AutomationError,
    ElementNotFoundError,
)
from askui.models.models import LocateSettings
from askui.models.types.geometry import PointList
from askui.utils.image_utils import ImageSource

logger = logging.getLogger(__name__)


class AskUiComboLocateModel(AskUiBaseLocateModel):
    """AskUI Combo locate model - tries PTA first, falls back to OCR."""

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> PointList:
        logger.debug("Using AskUI Combo locate model (PTA + OCR fallback)")
        if not isinstance(locator, str):
            error_msg = (
                f"Locators of type `{type(locator)}` are not supported for "
                "Combo model. Please provide a `str`."
            )
            raise AutomationError(error_msg)

        # Try PTA first
        try:
            prompt_locator = Prompt(locator)
            return self._locate(prompt_locator, image)
        except ElementNotFoundError:
            # Fall back to OCR
            logger.debug("PTA failed, falling back to OCR")
            text_locator = Text(locator)
            return self._locate(text_locator, image)
