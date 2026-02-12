import logging

from typing_extensions import override

from askui.locators.locators import Locator, Text
from askui.models.askui.locate_api import AskUiInferenceLocateApi, LocateApi
from askui.models.exceptions import AutomationError, IncompatibleApiError
from askui.models.models import DetectedElement, LocateModel, LocateSettings
from askui.models.types.geometry import PointList
from askui.utils.image_utils import ImageSource

logger = logging.getLogger(__name__)


class AskUiOcrLocateModel(LocateModel):
    """AskUI OCR locate model - uses Text/OCR locators.

    Args:
        locate_api (LocateApi): The locate API for making locate requests.
            Must be an instance of AskUiInferenceLocateApi.
    """

    def __init__(self, locate_api: LocateApi) -> None:
        if not isinstance(locate_api, AskUiInferenceLocateApi):
            raise IncompatibleApiError(
                model_name="AskUiOcrLocateModel",
                expected_api="AskUiInferenceLocateApi",
                actual_api=type(locate_api).__name__,
            )
        self._locate_api = locate_api

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
        return self._locate_api.locate(text_locator, image, locate_settings)

    @override
    def locate_all_elements(
        self,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> list[DetectedElement]:
        return self._locate_api.locate_all_elements(image, locate_settings)
