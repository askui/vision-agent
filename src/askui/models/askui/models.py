import json as json_lib
import logging
from typing import Any

from typing_extensions import override

from askui.locators.locators import AiElement, Locator, Prompt, Text
from askui.locators.serializers import AskUiLocatorSerializer, AskUiSerializedLocator
from askui.models.askui.gemini_get_model import AskUiGeminiGetModel
from askui.models.askui.inference_api import AskUiInferenceApi
from askui.models.exceptions import (
    AutomationError,
    ElementNotFoundError,
)
from askui.models.models import (
    DetectedElement,
    LocateModel,
    LocateSettings,
    ModelComposition,
)
from askui.models.types.geometry import PointList
from askui.utils.image_utils import ImageSource

logger = logging.getLogger(__name__)


class AskUiBaseLocateModel(LocateModel):
    """Base class for AskUI locate models with shared functionality."""

    def __init__(
        self,
        locator_serializer: AskUiLocatorSerializer,
        inference_api: AskUiInferenceApi,
    ) -> None:
        self._locator_serializer = locator_serializer
        self._inference_api = inference_api

    def _locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model_composition: ModelComposition | None = None,
    ) -> PointList:
        """Helper method for making locate API calls."""
        serialized_locator = (
            self._locator_serializer.serialize(locator=locator)
            if isinstance(locator, Locator)
            else AskUiSerializedLocator(customElements=[], instruction=locator)
        )
        logger.debug(
            "Locator serialized",
            extra={"serialized_locator": json_lib.dumps(serialized_locator)},
        )
        json: dict[str, Any] = {
            "image": image.to_data_url(),
            "instruction": f"get element {serialized_locator['instruction']}",
        }
        if "customElements" in serialized_locator:
            json["customElements"] = serialized_locator["customElements"]
        if model_composition is not None:
            json["modelComposition"] = model_composition.model_dump(by_alias=True)
            logger.debug(
                "Model composition",
                extra={"modelComposition": json_lib.dumps(json["modelComposition"])},
            )
        response = self._inference_api.post(path="/inference", json=json)
        content = response.json()
        assert content["type"] == "DETECTED_ELEMENTS", (
            f"Received unknown content type {content['type']}"
        )
        detected_elements = content["data"]["detected_elements"]
        if len(detected_elements) == 0:
            raise ElementNotFoundError(locator, serialized_locator)

        return [
            (
                int((element["bndbox"]["xmax"] + element["bndbox"]["xmin"]) / 2),
                int((element["bndbox"]["ymax"] + element["bndbox"]["ymin"]) / 2),
            )
            for element in detected_elements
        ]

    @override
    def locate_all_elements(
        self,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> list[DetectedElement]:
        request_body: dict[str, Any] = {
            "image": image.to_data_url(),
            "instruction": "get all elements",
        }

        # Note: Model composition would be handled by subclasses if needed
        # For now, this is a basic implementation

        response = self._inference_api.post(path="/inference", json=request_body)
        content = response.json()
        assert content["type"] == "DETECTED_ELEMENTS", (
            f"Received unknown content type {content['type']}"
        )
        detected_elements = content["data"]["detected_elements"]
        return [DetectedElement.from_json(element) for element in detected_elements]


class AskUiLocateModel(AskUiBaseLocateModel):
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


class AskUiPtaLocateModel(AskUiBaseLocateModel):
    """AskUI PTA (Prompt-to-Action) locate model - uses Prompt locators."""

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
        return self._locate(Prompt(locator), image)


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
                f"Locators of type `{type(locator)}` are not supported for Combo model. "
                "Please provide a `str`."
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
                f"Locators of type `{type(locator)}` are not supported for AI Element model. "
                "Please provide a `str`."
            )
            raise AutomationError(error_msg)
        ai_element_locator = AiElement(locator)
        return self._locate(ai_element_locator, image)


# AskUiGetModel is an alias for AskUiGeminiGetModel
# In the future, this might point to a different default model
AskUiGetModel = AskUiGeminiGetModel
