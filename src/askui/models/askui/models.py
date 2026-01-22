import json as json_lib
import logging
from typing import Any

from typing_extensions import override

from askui.locators.locators import Locator
from askui.locators.serializers import AskUiLocatorSerializer, AskUiSerializedLocator
from askui.models.askui.inference_api import AskUiInferenceApi
from askui.models.exceptions import (
    ElementNotFoundError,
)
from askui.models.models import (
    DetectedElement,
    LocateModel,
    LocateSettings,
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

        response = self._inference_api.post(path="/inference", json=request_body)
        content = response.json()
        assert content["type"] == "DETECTED_ELEMENTS", (
            f"Received unknown content type {content['type']}"
        )
        detected_elements = content["data"]["detected_elements"]
        return [DetectedElement.from_json(element) for element in detected_elements]
