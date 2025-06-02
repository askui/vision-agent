import json as json_lib
from typing import Any, Type

import requests
from pydantic import RootModel
from typing_extensions import override

from askui.exceptions import ElementNotFoundError
from askui.locators.locators import Locator
from askui.locators.serializers import AskUiLocatorSerializer, AskUiSerializedLocator
from askui.logger import logger
from askui.models.askui.settings import AskUiSettings
from askui.models.models import GetModel, LocateModel, ModelComposition, Point
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.image_utils import ImageSource

from ..types.response_schemas import to_response_schema
from .exceptions import AskUiApiRequestFailedError


class AskUiInferenceApi(GetModel, LocateModel):
    def __init__(
        self,
        settings: AskUiSettings,
        locator_serializer: AskUiLocatorSerializer,
    ) -> None:
        self._settings = settings
        self._locator_serializer = locator_serializer

    def _request(self, endpoint: str, json: dict[str, Any] | None = None) -> Any:
        response = requests.post(
            f"{self._settings.base_url}/{endpoint}",
            json=json,
            headers={
                "Content-Type": "application/json",
                "Authorization": self._settings.authorization_header,
            },
            timeout=30,
        )
        if response.status_code != 200:
            raise AskUiApiRequestFailedError(response.status_code, response.text)

        return response.json()

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model_choice: ModelComposition | str,
    ) -> Point:
        serialized_locator = (
            self._locator_serializer.serialize(locator=locator)
            if isinstance(locator, Locator)
            else AskUiSerializedLocator(customElements=[], instruction=locator)
        )
        logger.debug(f"serialized_locator:\n{json_lib.dumps(serialized_locator)}")
        json: dict[str, Any] = {
            "image": image.to_data_url(),
            "instruction": f"Click on {serialized_locator['instruction']}",
        }
        if "customElements" in serialized_locator:
            json["customElements"] = serialized_locator["customElements"]
        if isinstance(model_choice, ModelComposition):
            json["modelComposition"] = model_choice.model_dump(by_alias=True)
            logger.debug(
                f"modelComposition:\n{json_lib.dumps(json['modelComposition'])}"
            )
        content = self._request(endpoint="inference", json=json)
        assert content["type"] == "COMMANDS", (
            f"Received unknown content type {content['type']}"
        )
        actions = [
            el for el in content["data"]["actions"] if el["inputEvent"] == "MOUSE_MOVE"
        ]
        if len(actions) == 0:
            raise ElementNotFoundError(locator, serialized_locator)

        position = actions[0]["position"]
        return int(position["x"]), int(position["y"])

    @override
    def get(
        self,
        query: str,
        image: ImageSource,
        response_schema: Type[ResponseSchema] | None,
        model_choice: str,
    ) -> ResponseSchema | str:
        json: dict[str, Any] = {
            "image": image.to_data_url(),
            "prompt": query,
        }
        _response_schema = to_response_schema(response_schema)
        json["config"] = {"json_schema": _response_schema.model_json_schema()}
        logger.debug(f"json_schema:\n{json_lib.dumps(json['config']['json_schema'])}")
        content = self._request(endpoint="vqa/inference", json=json)
        response = content["data"]["response"]
        validated_response = _response_schema.model_validate(response)
        if isinstance(validated_response, RootModel):
            return validated_response.root
        return validated_response
