import json
import logging
from typing import TYPE_CHECKING, Any, Optional, Type

import openai
from openai import OpenAI
from typing_extensions import override

from askui.models.exceptions import QueryNoResponseError
from askui.models.models import GetModel, GetSettings
from askui.models.openrouter.settings import OpenRouterSettings
from askui.models.shared.prompts import GetSystemPrompt
from askui.models.types.response_schemas import ResponseSchema, to_response_schema
from askui.prompts.get_prompts import SYSTEM_PROMPT_GET
from askui.utils.excel_utils import OfficeDocumentSource
from askui.utils.pdf_utils import PdfSource
from askui.utils.source_utils import Source

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from openai.types.chat.completion_create_params import ResponseFormat


def _clean_schema_refs(schema: dict[str, Any] | list[Any]) -> None:
    """Remove title fields that are at the same level as $ref fields as they are not supported by OpenAI."""  # noqa: E501
    if isinstance(schema, dict):
        if "$ref" in schema and "title" in schema:
            del schema["title"]
        for value in schema.values():
            if isinstance(value, (dict, list)):
                _clean_schema_refs(value)
    elif isinstance(schema, list):
        for item in schema:
            if isinstance(item, (dict, list)):
                _clean_schema_refs(item)


class OpenRouterModel(GetModel):
    """
    This class implements the GetModel interface for the OpenRouter API.

    Args:
        settings (OpenRouterSettings): The settings for the OpenRouter model.

    Example:
        ```python
        from askui.models.openrouter.get_model import OpenRouterModel
        from askui.models.openrouter import OpenRouterSettings

        # Create OpenRouter model instance
        openrouter_model = OpenRouterModel(
            model_id="anthropic/claude-opus-4",
            settings=OpenRouterSettings(),
        )
        ```
    """  # noqa: E501

    def __init__(
        self,
        model_id: str,
        settings: OpenRouterSettings | None = None,
        client: Optional[OpenAI] = None,
    ):
        self._model_id = model_id
        self._settings = settings or OpenRouterSettings()

        self._client = (
            client
            if client is not None
            else OpenAI(
                api_key=self._settings.api_key.get_secret_value(),
                base_url=str(self._settings.base_url),
            )
        )

    def _predict(
        self,
        image_url: str,
        instruction: str,
        prompt: GetSystemPrompt,
        response_schema: type[ResponseSchema] | None,
    ) -> str | None | ResponseSchema:
        extra_body: dict[str, object] = {}

        if len(self._settings.models) > 0:
            extra_body["models"] = self._settings.models

        _response_schema = (
            to_response_schema(response_schema) if response_schema else None
        )

        response_format: openai.NotGiven | ResponseFormat = openai.NOT_GIVEN
        if _response_schema is not None:
            extra_body["provider"] = {"require_parameters": True}
            schema = _response_schema.model_json_schema()
            _clean_schema_refs(schema)

            defs = schema.pop("$defs", None)
            schema_response_wrapper = {
                "type": "object",
                "properties": {"response": schema},
                "additionalProperties": False,
                "required": ["response"],
            }
            if defs:
                schema_response_wrapper["$defs"] = defs
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "user_json_schema",
                    "schema": schema_response_wrapper,
                    "strict": True,
                },
            }

        chat_completion = self._client.chat.completions.create(  # type: ignore[misc]
            model=self._model_id,
            extra_body=extra_body,
            response_format=response_format,  # type: ignore[arg-type]
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                            },
                        },
                        {"type": "text", "text": str(prompt) + instruction},
                    ],
                }
            ],
            stream=False,
            top_p=self._settings.chat_completions_create_settings.top_p,
            temperature=self._settings.chat_completions_create_settings.temperature,
            max_tokens=self._settings.chat_completions_create_settings.max_tokens,
            seed=self._settings.chat_completions_create_settings.seed,
            stop=self._settings.chat_completions_create_settings.stop,
            frequency_penalty=self._settings.chat_completions_create_settings.frequency_penalty,
            presence_penalty=self._settings.chat_completions_create_settings.presence_penalty,
        )

        model_response = chat_completion.choices[0].message.content  # type: ignore[union-attr]

        if _response_schema is not None and model_response is not None:
            try:
                response_json = json.loads(model_response)
            except json.JSONDecodeError:
                error_msg = f"Expected JSON, but model {self._model_id} returned: {model_response}"  # noqa: E501
                logger.exception(
                    "Expected JSON, but model returned",
                    extra={"model": self._model_id, "response": model_response},
                )
                raise ValueError(error_msg) from None

            validated_response = _response_schema.model_validate(
                response_json["response"]
            )
            return validated_response.root

        return model_response

    @override
    def get(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None,
        get_settings: GetSettings,
    ) -> ResponseSchema | str:
        if isinstance(source, (PdfSource, OfficeDocumentSource)):
            err_msg = (
                "PDF or Office Document processing is not supported for "
                "OpenRouter model"
            )
            raise NotImplementedError(err_msg)

        # Use system prompt from settings if provided, otherwise use default
        system_prompt = (
            get_settings.system_prompt
            if get_settings.system_prompt
            else SYSTEM_PROMPT_GET
        )

        response = self._predict(
            image_url=source.to_data_url(),
            instruction=query,
            prompt=system_prompt,
            response_schema=response_schema,
        )
        if response is None:
            error_msg = f'No response from model "{self._model_id}" to query: "{query}"'
            raise QueryNoResponseError(error_msg, query)
        return response
