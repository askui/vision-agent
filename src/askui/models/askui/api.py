import os
import base64
import pathlib
from pydantic import RootModel
import requests
import json as json_lib
from PIL import Image
from typing import Any, Type, Union
from askui.models.models import ModelComposition
from askui.utils.image_utils import ImageSource
from askui.locators.serializers import AskUiLocatorSerializer
from askui.locators.locators import Locator
from askui.utils.image_utils import image_to_base64
from askui.logger import logger
from ..types.response_schemas import ResponseSchema, to_response_schema



class AskUiInferenceApi:
    def __init__(self, locator_serializer: AskUiLocatorSerializer):
        self._locator_serializer = locator_serializer
        self.inference_endpoint = os.getenv("ASKUI_INFERENCE_ENDPOINT", "https://inference.askui.com")
        self.workspace_id = os.getenv("ASKUI_WORKSPACE_ID")
        self.token = os.getenv("ASKUI_TOKEN")
        self.authenticated = True
        if self.workspace_id is None or self.token is None:
            logger.warning("ASKUI_WORKSPACE_ID or ASKUI_TOKEN missing.")
            self.authenticated = False

    def _build_askui_token_auth_header(self, bearer_token: str | None = None) -> dict[str, str]:
        if bearer_token is not None:
            return {"Authorization": f"Bearer {bearer_token}"}

        if self.token is None:
            raise Exception("ASKUI_TOKEN is not set.")
        token_base64 = base64.b64encode(self.token.encode("utf-8")).decode("utf-8")
        return {"Authorization": f"Basic {token_base64}"}

    def _build_base_url(self, endpoint: str) -> str:
        return f"{self.inference_endpoint}/api/v3/workspaces/{self.workspace_id}/{endpoint}"

    def _request(self, endpoint: str, json: dict[str, Any] | None = None) -> Any:
        response = requests.post(
            self._build_base_url(endpoint),
            json=json,
            headers={"Content-Type": "application/json", **self._build_askui_token_auth_header()},
            timeout=30,
        )
        if response.status_code != 200:
            raise Exception(f"{response.status_code}: Unknown Status Code\n", response.text)

        return response.json()

    def predict(self, image: Union[pathlib.Path, Image.Image], locator: Locator, model: ModelComposition | None = None) -> tuple[int | None, int | None]:
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
            logger.debug(f"modelComposition:\n{json_lib.dumps(json['modelComposition'])}")
        content = self._request(endpoint="inference", json=json)
        assert content["type"] == "COMMANDS", f"Received unknown content type {content['type']}"
        actions = [el for el in content["data"]["actions"] if el["inputEvent"] == "MOUSE_MOVE"]
        if len(actions) == 0:
            return None, None

        position = actions[0]["position"]
        return int(position["x"]), int(position["y"])

    def get_inference(
        self, 
        image: ImageSource, 
        query: str, 
        response_schema: Type[ResponseSchema] | None = None
    ) -> ResponseSchema | str:
        json: dict[str, Any] = {
            "image": image.to_data_url(),
            "prompt": query,
        }
        _response_schema = to_response_schema(response_schema)
        json["config"] = {
            "json_schema": _response_schema.model_json_schema()
        }
        logger.debug(f"json_schema:\n{json_lib.dumps(json['config']['json_schema'])}")
        content = self._request(endpoint="vqa/inference", json=json)
        response = content["data"]["response"]
        validated_response = _response_schema.model_validate(response)
        if isinstance(validated_response, RootModel):
            return validated_response.root
        return validated_response
