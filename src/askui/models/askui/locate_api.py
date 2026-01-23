"""LocateApi interface and AskUI implementation for element location."""

import json as json_lib
import logging
from typing import Any

from askui.locators.locators import Locator
from askui.locators.serializers import AskUiLocatorSerializer, AskUiSerializedLocator
from askui.models.askui.inference_api import AskUiInferenceApi
from askui.models.exceptions import ElementNotFoundError
from askui.models.models import DetectedElement, LocateSettings
from askui.models.shared.locate_api import LocateApi
from askui.models.types.geometry import PointList
from askui.utils.image_utils import ImageSource

logger = logging.getLogger(__name__)


class AskUiInferenceLocateApi(LocateApi):
    """AskUI Inference API implementation for locating elements."""

    def __init__(
        self,
        locator_serializer: AskUiLocatorSerializer,
        inference_api: AskUiInferenceApi,
    ) -> None:
        """Initialize the AskUI Inference Locate API.

        Args:
            locator_serializer (AskUiLocatorSerializer): Serializer for locators.
            inference_api (AskUiInferenceApi): AskUI inference API client.
        """
        self._locator_serializer = locator_serializer
        self._inference_api = inference_api

    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        locate_settings: LocateSettings,  # noqa: ARG002
    ) -> PointList:
        """Locate elements using AskUI Inference API.

        Args:
            locator (str | Locator): Element locator (text or structured).
            image (ImageSource): Image to search in.
            locate_settings (LocateSettings): Settings (currently unused).

        Returns:
            PointList: List of (x, y) coordinates for located elements.

        Raises:
            ElementNotFoundError: If no elements are found.
        """
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

    def locate_all_elements(
        self,
        image: ImageSource,
        locate_settings: LocateSettings,  # noqa: ARG002
    ) -> list[DetectedElement]:
        """Locate all elements using AskUI Inference API.

        Args:
            image (ImageSource): Image to analyze.
            locate_settings (LocateSettings): Settings (currently unused).

        Returns:
            list[DetectedElement]: All detected elements.
        """
        request_body: dict[str, Any] = {
            "image": image.to_data_url(),
            "instruction": "get all elements",
        }

        response = self._inference_api.post(path="/inference", json=request_body)
        content = response.json()
        assert content["type"] == "DETECTED_ELEMENTS", (
            f"Received unknown content type {content['type']}"
        )
        detected_elements = content["data"]["detected_elements"]
        return [DetectedElement.from_json(element) for element in detected_elements]
