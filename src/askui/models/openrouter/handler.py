import os
from typing import Type

from openai import OpenAI
from typing_extensions import override

from askui.models.exceptions import QueryNoResponseError
from askui.models.models import GetModel
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.image_utils import ImageSource

from .prompts import PROMPT_QA
from .settings import OpenRouterSettings


class OpenRouterGetModel(GetModel):
    def __init__(self, settings: OpenRouterSettings):
        self._settings = settings

        _open_router_key = os.getenv("OPEN_ROUTER_API_KEY")
        if _open_router_key is None:
            error_msg = "OPEN_ROUTER_API_KEY is not set"
            raise ValueError(error_msg)

        self._client = OpenAI(
            api_key=_open_router_key,
            base_url="https://openrouter.ai/api/v1",
        )

    def _predict(self, image_url: str, instruction: str, prompt: str) -> str | None:
        chat_completion = self._client.chat.completions.create(
            model=self._settings.model,
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
            top_p=None,
            temperature=None,
            max_tokens=150,
            stream=False,
            seed=None,
            stop=None,
            frequency_penalty=None,
            presence_penalty=None,
        )
        return chat_completion.choices[0].message.content

    @override
    def get(
        self,
        query: str,
        image: ImageSource,
        response_schema: Type[ResponseSchema] | None,
        model_choice: str,
    ) -> ResponseSchema | str:
        if response_schema is not None:
            error_msg = f'Response schema is not supported for model "{model_choice}"'
            raise NotImplementedError(error_msg)
        response = self._predict(
            image_url=image.to_data_url(),
            instruction=query,
            prompt=PROMPT_QA,
        )
        if response is None:
            error_msg = f'No response from model "{model_choice}" to query: "{query}"'
            raise QueryNoResponseError(error_msg, query)
        return response
