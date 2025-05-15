import base64
import json as json_lib
import pathlib
from functools import cached_property
from typing import Any, Type, Union

import requests
from PIL import Image
from pydantic import UUID4, Field, HttpUrl, RootModel, SecretStr
from pydantic_settings import BaseSettings

from askui.locators.locators import Locator
from askui.locators.serializers import AskUiLocatorSerializer
from askui.logger import logger
from askui.models.models import ModelComposition
from askui.utils.image_utils import ImageSource, image_to_base64

from ..types.response_schemas import ResponseSchema, to_response_schema
from .exceptions import AskUiApiRequestFailedError


class AskUiSettings(BaseSettings):
    """Settings for AskUI API."""

    inference_endpoint: HttpUrl = Field(
        default_factory=lambda: HttpUrl("https://inference.askui.com"),
        validation_alias="ASKUI_INFERENCE_ENDPOINT",
    )
    workspace_id: UUID4 = Field(
        validation_alias="ASKUI_WORKSPACE_ID",
    )
    token: SecretStr = Field(
        validation_alias="ASKUI_TOKEN",
    )

    @cached_property
    def authorization_header(self) -> str:
        token_str = self.token.get_secret_value()
        token_base64 = base64.b64encode(token_str.encode()).decode()
        return f"Basic {token_base64}"

    @cached_property
    def base_url(self) -> str:
        return f"{self.inference_endpoint}/api/v1/workspaces/{self.workspace_id}"


class AskUiInferenceApi:
    def __init__(
        self,
        locator_serializer: AskUiLocatorSerializer,
        settings: AskUiSettings,
    ) -> None:
        self._locator_serializer = locator_serializer
        self._settings = settings

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

    def predict(
        self,
        image: Union[pathlib.Path, Image.Image],
        locator: Locator,
        model: ModelComposition | None = None,
    ) -> tuple[int | None, int | None]:
        serialized_locator = self._locator_serializer.serialize(locator=locator)
        logger.debug(f"serialized_locator:\n{json_lib.dumps(serialized_locator)}")
        json: dict[str, Any] = {
            "image": f",{image_to_base64(image)}",
            "instruction": f"Click on {serialized_locator['instruction']}",
        }
        if "customElements" in serialized_locator:
            json["customElements"] = serialized_locator["customElements"]
        if model is not None:
            json["modelComposition"] = model.model_dump(by_alias=True)
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
            return None, None

        position = actions[0]["position"]
        return int(position["x"]), int(position["y"])

    def get_inference(
        self,
        image: ImageSource,
        query: str,
        response_schema: Type[ResponseSchema] | None = None,
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
