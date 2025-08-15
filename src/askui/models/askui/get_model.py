from typing import Type

from google.genai.errors import ClientError
from typing_extensions import override

from askui.logger import logger
from askui.models.askui.google_genai_api import AskUiGoogleGenAiApi
from askui.models.askui.inference_api import AskUiInferenceApi
from askui.models.exceptions import QueryNoResponseError, QueryUnexpectedResponseError
from askui.models.models import GetModel
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.source_utils import Source


class AskUiGetModel(GetModel):
    """A GetModel implementation that is supposed to be as comprehensive and
    powerful as possible using the available AskUi models.

    This model first attempts to use the Google GenAI API for information extraction.
    If the Google GenAI API fails (e.g., no response, unexpected response, or other
    errors), it falls back to using the AskUI Inference API.

    Args:
        google_genai_api (AskUiGoogleGenAiApi): The Google GenAI API instance to use
            as primary.
        inference_api (AskUiInferenceApi): The Inference API instance to use as
            fallback.
    """

    def __init__(
        self,
        google_genai_api: AskUiGoogleGenAiApi,
        inference_api: AskUiInferenceApi,
    ) -> None:
        self._google_genai_api = google_genai_api
        self._inference_api = inference_api

    @override
    def get(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None,
        model_choice: str,
    ) -> ResponseSchema | str:
        try:
            logger.debug("Attempting to use Google GenAI API")
            return self._google_genai_api.get(
                query=query,
                source=source,
                response_schema=response_schema,
                model_choice=model_choice,
            )
        except (
            ClientError,
            QueryNoResponseError,
            QueryUnexpectedResponseError,
            NotImplementedError,
        ) as e:
            if isinstance(e, ClientError) and e.code != 400:
                raise
            logger.debug(
                f"Google GenAI API failed with error that may not occur with other "
                f"models/apis: {e}"
                ". Falling back to Inference API..."
            )
            return self._inference_api.get(
                query=query,
                source=source,
                response_schema=response_schema,
                model_choice=model_choice,
            )
