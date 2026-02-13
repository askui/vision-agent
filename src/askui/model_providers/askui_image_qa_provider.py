"""AskUIImageQAProvider — image Q&A via AskUI's hosted Gemini proxy."""

import json as json_lib
import logging
from functools import cached_property
from importlib.metadata import PackageNotFoundError
from typing import Type

from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from typing_extensions import override

from askui.model_providers.image_qa_provider import ImageQAProvider
from askui.models.shared.settings import GetSettings
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.source_utils import Source

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_ID = "gemini-2.5-flash"
_MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024


def _is_retryable_error(exception: BaseException) -> bool:
    """Check if the exception is a retryable API error."""
    try:
        from google.genai.errors import APIError

        from askui.models.askui.retry_utils import RETRYABLE_HTTP_STATUS_CODES

        if isinstance(exception, APIError):
            return exception.code in RETRYABLE_HTTP_STATUS_CODES
    except ImportError:
        pass
    return False


class AskUIImageQAProvider(ImageQAProvider):
    """Image Q&A provider that routes requests through AskUI's hosted Gemini proxy.

    Supports multimodal Q&A and structured output extraction from images and
    PDFs. Credentials are read from the ``ASKUI_WORKSPACE_ID`` and
    ``ASKUI_TOKEN`` environment variables lazily — validation happens on the
    first API call, not at construction time.

    Args:
        model_id (str, optional): Gemini model to use. Defaults to
            ``"gemini-2.5-flash"``.

    Example:
        ```python
        from askui import AgentSettings, ComputerAgent
        from askui.model_providers import AskUIImageQAProvider

        agent = ComputerAgent(settings=AgentSettings(
            image_qa_provider=AskUIImageQAProvider(
                model_id="gemini-2.5-pro",
            )
        ))
        ```
    """

    def __init__(
        self,
        model_id: str = _DEFAULT_MODEL_ID,
    ) -> None:
        self._model_id = model_id

    @cached_property
    def _genai_client(self):  # type: ignore[no-untyped-def]
        """Lazily initialise the GenAI client via the AskUI proxy on first use."""
        try:
            import google.genai as genai
            from google.genai import types as genai_types
        except ImportError as e:
            raise PackageNotFoundError from e

        from askui.models.askui.inference_api_settings import AskUiInferenceApiSettings

        _api_settings = AskUiInferenceApiSettings()
        return genai.Client(
            vertexai=True,
            api_key="DummyValueRequiredByGenaiClient",
            http_options=genai_types.HttpOptions(
                base_url=f"{_api_settings.base_url}/proxy/vertexai",
                headers={
                    "Authorization": _api_settings.authorization_header,
                },
            ),
        )

    def _source_to_part(self, source: Source):  # type: ignore[no-untyped-def]
        """Convert a Source to a Google GenAI Part.

        Args:
            source (Source): The image, PDF, or office document source.

        Returns:
            genai_types.Part: The corresponding GenAI part.

        Raises:
            ValueError: If the source data exceeds the size limit.
        """
        import google.genai.types as genai_types

        from askui.utils.excel_utils import OfficeDocumentSource
        from askui.utils.image_utils import ImageSource

        if isinstance(source, ImageSource):
            data = source.to_bytes()
            if len(data) > _MAX_FILE_SIZE_BYTES:
                limit = _MAX_FILE_SIZE_BYTES
                err_msg = f"Image file size exceeds the limit of {limit} bytes."
                raise ValueError(err_msg)
            return genai_types.Part.from_bytes(data=data, mime_type="image/png")
        if isinstance(source, OfficeDocumentSource):
            with source.reader as r:
                return genai_types.Part.from_text(text=r.read().decode())
        # PDF and other sources
        with source.reader as r:
            data = r.read()
            if len(data) > _MAX_FILE_SIZE_BYTES:
                err_msg = (
                    f"PDF file size exceeds the limit of {_MAX_FILE_SIZE_BYTES} bytes."
                )
                raise ValueError(err_msg)
            return genai_types.Part.from_bytes(data=data, mime_type="application/pdf")

    @retry(
        stop=stop_after_attempt(4),  # 3 retries after the initial attempt
        wait=wait_exponential(multiplier=30, min=30, max=120),
        retry=retry_if_exception(_is_retryable_error),
        reraise=True,
    )
    @override
    def query(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None,
        get_settings: GetSettings,
    ) -> ResponseSchema | str:
        """Query the AskUI-hosted Gemini model with an image or document source.

        Args:
            query (str): The question or extraction instruction.
            source (Source): The image or document source to analyze.
            response_schema (Type[ResponseSchema] | None): Optional Pydantic
                model defining the expected response structure.
            get_settings (GetSettings): Settings for this query.

        Returns:
            ResponseSchema | str: Extracted information.

        Raises:
            NotImplementedError: If a recursive response schema is provided.
        """
        import google.genai.types as genai_types
        from pydantic import ValidationError

        from askui.models.exceptions import (
            QueryNoResponseError,
            QueryUnexpectedResponseError,
        )
        from askui.models.types.response_schemas import to_response_schema
        from askui.prompts.get_prompts import SYSTEM_PROMPT_GET

        try:
            _response_schema = to_response_schema(response_schema)
            json_schema = json_lib.dumps(_response_schema.model_json_schema())
            logger.debug(
                "Json schema used for response",
                extra={"json_schema": json_schema},
            )

            content = genai_types.Content(
                parts=[
                    self._source_to_part(source),
                    genai_types.Part.from_text(text=query),
                ],
                role="user",
            )

            system_prompt = (
                str(get_settings.system_prompt)
                if get_settings.system_prompt
                else str(SYSTEM_PROMPT_GET)
            )

            response = self._genai_client.models.generate_content(
                model=f"models/{self._model_id}",
                contents=content,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": _response_schema,
                    "system_instruction": system_prompt,
                },
            )
            json_str = response.text
            if json_str is None:
                raise QueryNoResponseError(
                    message="No response from the model", query=query
                )
            try:
                return _response_schema.model_validate_json(json_str).root
            except ValidationError as e:
                error_message = str(e.errors())
                raise QueryUnexpectedResponseError(
                    message=(f"Unexpected response from the model: {error_message}"),
                    query=query,
                    response=json_str,
                ) from e
        except RecursionError as e:
            error_message = (
                "Recursive response schemas are not supported by AskUIImageQAProvider"
            )
            raise NotImplementedError(error_message) from e
