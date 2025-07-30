import json as json_lib
from typing import Type

import google.genai as genai
from google.genai import types as genai_types
from pydantic import ValidationError
from typing_extensions import override

from askui.logger import logger
from askui.models.askui.inference_api import AskUiInferenceApiSettings
from askui.models.exceptions import QueryNoResponseError, QueryUnexpectedResponseError
from askui.models.models import GetModel, ModelName
from askui.models.shared.prompts import SYSTEM_PROMPT_GET
from askui.models.types.response_schemas import ResponseSchema, to_response_schema
from askui.utils.image_utils import ImageSource

ASKUI_MODEL_CHOICE_PREFIX = "askui/"
ASKUI_MODEL_CHOICE_PREFIX_LEN = len(ASKUI_MODEL_CHOICE_PREFIX)


def _extract_model_id(model_choice: str) -> str:
    if model_choice == ModelName.ASKUI:
        return ModelName.GEMINI__2_5__FLASH
    if model_choice.startswith(ASKUI_MODEL_CHOICE_PREFIX):
        return model_choice[ASKUI_MODEL_CHOICE_PREFIX_LEN:]
    return model_choice


class AskUiGoogleGenAiApi(GetModel):
    def __init__(self, settings: AskUiInferenceApiSettings | None = None) -> None:
        self._settings = settings or AskUiInferenceApiSettings()
        self._client = genai.Client(
            vertexai=True,
            api_key="DummyValueRequiredByGenaiClient",
            http_options=genai_types.HttpOptions(
                base_url=f"{self._settings.base_url}/proxy/vertexai",
                headers={
                    "Authorization": self._settings.authorization_header,
                },
            ),
        )

    @override
    def get(
        self,
        query: str,
        image: ImageSource,
        response_schema: Type[ResponseSchema] | None,
        model_choice: str,
    ) -> ResponseSchema | str:
        try:
            _response_schema = to_response_schema(response_schema)
            json_schema = _response_schema.model_json_schema()
            logger.debug(f"json_schema:\n{json_lib.dumps(json_schema)}")
            content = genai_types.Content(
                parts=[
                    genai_types.Part.from_bytes(
                        data=image.to_bytes(),
                        mime_type="image/png",
                    ),
                    genai_types.Part.from_text(text=query),
                ],
                role="user",
            )
            generate_content_response = self._client.models.generate_content(
                model=f"models/{_extract_model_id(model_choice)}",
                contents=content,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": _response_schema,
                    "system_instruction": SYSTEM_PROMPT_GET,
                },
            )
            json_str = generate_content_response.text
            if json_str is None:
                raise QueryNoResponseError(
                    message="No response from the model", query=query
                )
            try:
                return _response_schema.model_validate_json(json_str).root
            except ValidationError as e:
                error_message = str(e.errors())
                raise QueryUnexpectedResponseError(
                    message=f"Unexpected response from the model: {error_message}",
                    query=query,
                    response=json_str,
                ) from e
        except RecursionError as e:
            error_message = (
                "Recursive response schemas are not supported by AskUiGoogleGenAiApi"
            )
            raise NotImplementedError(error_message) from e
