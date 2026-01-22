import logging

from typing_extensions import override

from askui.locators.locators import AiElement, Locator
from askui.models.askui.models import AskUiBaseLocateModel
from askui.models.exceptions import AutomationError
from askui.models.models import LocateSettings
from askui.models.types.geometry import PointList
from askui.utils.image_utils import ImageSource

logger = logging.getLogger(__name__)


class AskUiAiElementLocateModel(AskUiBaseLocateModel):
    """AskUI AI Element locate model - uses AiElement locators."""

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> PointList:
        logger.debug("Using AskUI AI Element locate model")
        if not isinstance(locator, str):
            error_msg = (
                f"Locators of type `{type(locator)}` are not supported for "
                "AI Element model. Please provide a `str`."
            )
            raise AutomationError(error_msg)
        ai_element_locator = AiElement(locator)
        return self._locate(ai_element_locator, image)
