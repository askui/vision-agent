import logging
from pathlib import Path
from typing import Annotated, Type, overload

from PIL import Image as PILImage
from pydantic import Field

from askui.models.defaults import default_get_model
from askui.models.models import GetModel
from askui.models.shared.settings import GetSettings
from askui.reporting import NULL_REPORTER, Reporter
from askui.utils.image_utils import ImageSource
from askui.utils.source_utils import InputSource, Source, load_source

from .models.types.response_schemas import ResponseSchema

logger = logging.getLogger(__name__)


class DataExtractor:
    """Data extraction utility using GetModel for images/PDFs."""

    def __init__(
        self,
        get_model: GetModel | None = None,
        reporter: Reporter = NULL_REPORTER,
    ) -> None:
        self._get_model = get_model or default_get_model()
        self._reporter = reporter
        self.get_settings = GetSettings()

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
            source=_source,
            query=query,
            response_schema=response_schema,
            get_settings=self.get_settings,
        )
        message_content = (
            str(response)
            if isinstance(response, (str, bool, int, float))
            else response.model_dump()
        )
        self._reporter.add_message("Agent", message_content)
        return response
