from pathlib import Path
from typing import Annotated, Type, overload

from PIL import Image as PILImage
from pydantic import Field

from askui.models.models import ModelRegistry
from askui.reporting import NULL_REPORTER, Reporter
from askui.utils.image_utils import ImageSource
from askui.utils.source_utils import InputSource, Source, load_source

from .logger import logger
from .models.model_router import ModelRouter, initialize_default_model_registry
from .models.types.response_schemas import ResponseSchema


class DataExtractor:
    def __init__(
        self,
        reporter: Reporter = NULL_REPORTER,
        models: ModelRegistry | None = None,
    ) -> None:
        self._reporter = reporter
        self._model_router = self._init_model_router(
            reporter=reporter,
            models=models or {},
        )

    def _init_model_router(
        self,
        reporter: Reporter,
        models: ModelRegistry,
    ) -> ModelRouter:
        _models = initialize_default_model_registry(
            reporter=reporter,
        )
        _models.update(models)
        return ModelRouter(
            reporter=reporter,
            models=_models,
        )

    @overload
    def get(
        self,
        query: Annotated[str, Field(min_length=1)],
        source: InputSource | Source,
        model: str,
        response_schema: None = None,
    ) -> str: ...
    @overload
    def get(
        self,
        query: Annotated[str, Field(min_length=1)],
        source: InputSource | Source,
        model: str,
        response_schema: Type[ResponseSchema],
    ) -> ResponseSchema: ...
    def get(
        self,
        query: Annotated[str, Field(min_length=1)],
        source: InputSource | Source,
        model: str,
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
        response = self._model_router.get(
            source=_source,
            query=query,
            response_schema=response_schema,
            model_choice=model,
        )
        message_content = (
            str(response)
            if isinstance(response, (str, bool, int, float))
            else response.model_dump()
        )
        self._reporter.add_message("Agent", message_content)
        return response
