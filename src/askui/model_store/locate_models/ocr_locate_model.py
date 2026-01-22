import logging

from typing_extensions import override

from askui.locators.locators import Locator, Text
from askui.models.askui.models import AskUiBaseLocateModel
from askui.models.exceptions import AutomationError
from askui.models.models import LocateSettings
from askui.models.types.geometry import PointList
from askui.utils.image_utils import ImageSource

logger = logging.getLogger(__name__)


class AskUiOcrLocateModel(AskUiBaseLocateModel):
    """AskUI OCR locate model - uses Text/OCR locators."""

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> PointList:
        logger.debug("Using AskUI OCR locate model")
        if not isinstance(locator, str):
            error_msg = (
                f"Locators of type `{type(locator)}` are not supported for OCR model. "
                "Please provide a `str`."
            )
            raise AutomationError(error_msg)
        text_locator = Text(locator)
        return self._locate(text_locator, image)
