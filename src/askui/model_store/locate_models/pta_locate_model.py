import logging

from typing_extensions import override

from askui.locators.locators import Locator, Prompt
from askui.models.askui.locate_api import AskUiInferenceLocateApi, LocateApi
from askui.models.exceptions import AutomationError, IncompatibleApiError
from askui.models.models import DetectedElement, LocateModel, LocateSettings
from askui.models.types.geometry import PointList
from askui.utils.image_utils import ImageSource

logger = logging.getLogger(__name__)


class AskUiPtaLocateModel(LocateModel):
    """AskUI PTA (Prompt-to-Action) locate model - uses Prompt locators.

    Args:
        locate_api (LocateApi): The locate API for making locate requests.
            Must be an instance of AskUiInferenceLocateApi.
    """

    def __init__(self, locate_api: LocateApi) -> None:
        if not isinstance(locate_api, AskUiInferenceLocateApi):
            raise IncompatibleApiError(
                model_name="AskUiPtaLocateModel",
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
        logger.debug("Using AskUI PTA locate model")
        if not isinstance(locator, str):
            error_msg = (
                f"Locators of type `{type(locator)}` are not supported for PTA model. "
                "Please provide a `str`."
            )
            raise AutomationError(error_msg)
        return self._locate_api.locate(Prompt(locator), image, locate_settings)

    @override
    def locate_all_elements(
        self,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> list[DetectedElement]:
        return self._locate_api.locate_all_elements(image, locate_settings)
