import json
from typing import Optional, Type

from openai import OpenAI
from typing_extensions import override

from askui.logger import logger
from askui.models.exceptions import QueryNoResponseError
from askui.models.models import GetModel
from askui.models.shared.prompts import SYSTEM_PROMPT_GET
from askui.models.types.response_schemas import ResponseSchema, to_response_schema
from askui.utils.image_utils import ImageSource

from .settings import OpenRouterSettings


class OpenRouterModel(GetModel):
    """
    This class implements the GetModel interface for the OpenRouter API.

    Args:
        settings (OpenRouterSettings): The settings for the OpenRouter model.

    Example:
        ```python
        from askui import VisionAgent
        from askui.models import (
            OpenRouterModel,
            OpenRouterSettings,
            ModelRegistry,
        )


        # Register OpenRouter model in the registry
        custom_models: ModelRegistry = {
            "my-custom-model": OpenRouterGetModel(
                OpenRouterSettings(
                    model="anthropic/claude-opus-4",
                )
            ),
        }

        with VisionAgent(models=custom_models, model={"get":"my-custom-model"}) as agent:
            result = agent.get("What is the main heading on the screen?")
            print(result)
        ```
    """  # noqa: E501

    def __init__(
        self,
        settings: OpenRouterSettings | None = None,
        client: Optional[OpenAI] = None,
    ):
        self._settings = settings or OpenRouterSettings()

        self._client = (
            client
            if client is not None
            else OpenAI(
                api_key=self._settings.open_router_api_key.get_secret_value(),
                base_url=str(self._settings.base_url),
            )
        )

    def _predict(
        self,
        image_url: str,
        instruction: str,
        prompt: str,
        response_schema: type[ResponseSchema] | None,
    ) -> str | None | ResponseSchema:
        extra_body: dict[str, object] = {}

        if len(self._settings.models) > 0:
            extra_body["models"] = self._settings.models

        response_format: dict[str, object] | None = None
        if response_schema is not None:
            extra_body["provider"] = {"require_parameters": True}

            _response_schema = to_response_schema(response_schema)
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "user_json_schema",
                    "schema": next(
                        iter(
                            _response_schema.model_json_schema()
                            .get("$defs", {})
                            .values()
                        )
                    ),
                    "strict": True,
                },
            }

        chat_completion = self._client.chat.completions.create(  # type: ignore
            model=self._settings.model,
            extra_body=extra_body,
            response_format=response_format,
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
                        {"type": "text", "text": prompt + instruction},
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

        model_response = chat_completion.choices[0].message.content

        if response_schema is None:
            return model_response  # type: ignore

        response_json: object
        try:
            response_json = json.loads(str(model_response))
        except json.JSONDecodeError:
            error_msg = f"Expected JSON, but model {self._settings.model} returned: {model_response}"  # noqa: E501
            logger.error(error_msg)
            raise ValueError(error_msg) from None

        _response_schema = to_response_schema(response_schema)
        validated_response = _response_schema.model_validate(response_json)
        return validated_response.root

    @override
    def get(
        self,
        query: str,
        image: ImageSource,
        response_schema: Type[ResponseSchema] | None,
        model_choice: str,
    ) -> ResponseSchema | str:
        response = self._predict(
            image_url=image.to_data_url(),
            instruction=query,
            prompt=SYSTEM_PROMPT_GET,
            response_schema=response_schema,
        )
        if response is None:
            error_msg = f'No response from model "{model_choice}" to query: "{query}"'
            raise QueryNoResponseError(error_msg, query)
        return response
