import logging

from typing_extensions import override

from askui.locators.locators import Locator, Text
from askui.models.askui.models import AskUiBaseLocateModel
from askui.models.models import LocateSettings
from askui.models.types.geometry import PointList
from askui.utils.image_utils import ImageSource

logger = logging.getLogger(__name__)


class TextLocateModel(AskUiBaseLocateModel):
    """Default AskUI locate model - uses Text locators."""

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> PointList:
        logger.debug("Using AskUI default locate model")
        locator = Text(locator) if isinstance(locator, str) else locator
        return self._locate(locator, image)
