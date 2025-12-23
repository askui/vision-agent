import logging
from pathlib import Path
from typing import Annotated, Type, overload

from PIL import Image as PILImage
from pydantic import Field

from askui.models.askui.google_genai_api import AskUiGoogleGenAiApi
from askui.models.askui.inference_api import AskUiInferenceApi
from askui.models.askui.inference_api_settings import AskUiInferenceApiSettings
from askui.models.askui.models import AskUiGetModel
from askui.models.models import GetModel
from askui.reporting import NULL_REPORTER, Reporter
from askui.utils.image_utils import ImageSource
from askui.utils.source_utils import InputSource, Source, load_source

from .models.types.response_schemas import ResponseSchema

logger = logging.getLogger(__name__)


class DataExtractor:
    def __init__(
        self,
        reporter: Reporter = NULL_REPORTER,
    ) -> None:
        self._reporter = reporter
        self._get_model = self._init_default_get_model()

    def _init_default_get_model(self) -> GetModel:
        """Initialize default get model."""
        # Initialize AskUI inference API
        inference_api = AskUiInferenceApi(settings=AskUiInferenceApiSettings())

        # Initialize get model
        google_genai_api = AskUiGoogleGenAiApi()
        return AskUiGetModel(
            google_genai_api=google_genai_api,
            inference_api=inference_api,
        )

    @overload
    def get(
        self,
        query: Annotated[str, Field(min_length=1)],
        source: InputSource | Source,
        response_schema: None = None,
    ) -> str: ...
    @overload
    def get(
        self,
        query: Annotated[str, Field(min_length=1)],
        source: InputSource | Source,
        response_schema: Type[ResponseSchema],
    ) -> ResponseSchema: ...
    def get(
        self,
        query: Annotated[str, Field(min_length=1)],
        source: InputSource | Source,
        response_schema: Type[ResponseSchema] | None = None,
    ) -> ResponseSchema | str:
        logger.debug("Received instruction to get '%s'", query)
        _source = (
            load_source(source)
            if isinstance(source, (str, Path, PILImage.Image))
            else source
        )

        # Prepare message content with file path if available
        user_message_content = f'get: "{query}"' + (
            f" from '{source}'" if isinstance(source, (str, Path)) else ""
        )

        self._reporter.add_message(
            "User",
            user_message_content,
            image=_source.root if isinstance(_source, ImageSource) else None,
        )
        response = self._get_model.get(
            query=query,
            source=_source,
            response_schema=response_schema,
        )
        message_content = (
            str(response)
            if isinstance(response, (str, bool, int, float))
            else response.model_dump()
        )
        self._reporter.add_message("Agent", message_content)
        return response
