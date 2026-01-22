"""Fallback model implementations for graceful degradation."""

import logging
from typing import Annotated, Type

from pydantic import Field
from typing_extensions import override

from askui.locators.locators import Locator
from askui.models.models import GetModel, LocateModel
from askui.models.shared.settings import GetSettings, LocateSettings
from askui.models.types.geometry import PointList
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.image_utils import ImageSource
from askui.utils.source_utils import Source

logger = logging.getLogger(__name__)


class FallbackLocateModel(LocateModel):
    """
    A LocateModel that tries multiple models in sequence until one succeeds.

    This model implements a fallback pattern where if the primary model fails to locate
    an element, it automatically tries the next model in the list. This is useful for
    graceful degradation and robust element location.

    Args:
        models (list[LocateModel]): List of LocateModel instances to try in order.
            Must contain at least one model.

    Example:
        ```python
        from askui import VisionAgent
        from askui.models.askui.models import (
            AskUiPtaLocateModel,
            AskUiOcrLocateModel,
        )
        from askui.models.fallback_model import FallbackLocateModel

        # Create fallback model that tries PTA first, then OCR
        fallback_model = FallbackLocateModel(
            models=[
                AskUiPtaLocateModel(...),
                AskUiOcrLocateModel(...),
            ]
        )

        with VisionAgent(locate_model=fallback_model) as agent:
            agent.click("Submit button")
        ```
    """

    def __init__(
        self,
        models: Annotated[list[LocateModel], Field(min_length=1)],
    ) -> None:
        self._models = models

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> PointList:
        """
        Attempts to locate an element using each model in sequence.

        Tries each model in the order they were provided. If a model fails (raises an
        exception), the next model is tried. If all models fail, the exception from the
        last model is raised.

        Args:
            locator (str | Locator): The locator to use for finding the element.
            image (ImageSource): The image source to search in.
            locate_settings (LocateSettings): Settings for the locate operation.

        Returns:
            PointList: List of points where the element was located.

        Raises:
            Exception: The exception from the last model if all models fail.
        """
        last_exception = None

        for i, model in enumerate(self._models):
            try:
                logger.debug(
                    "Trying locate model %d/%d",
                    i + 1,
                    len(self._models),
                )
                result = model.locate(
                    locator=locator,
                    image=image,
                    locate_settings=locate_settings,
                )
                logger.debug(
                    "Locate model %d/%d succeeded",
                    i + 1,
                    len(self._models),
                )
                return result  # noqa: TRY300
            except Exception as e:  # noqa: BLE001, PERF203
                logger.debug(
                    "Locate model %d/%d failed: %s",
                    i + 1,
                    len(self._models),
                    str(e),
                )
                last_exception = e
                continue

        # All models failed, raise the last exception
        if last_exception:
            raise last_exception
        # This should never happen since we validated min_length=1
        msg = "No models provided to FallbackLocateModel"
        raise ValueError(msg)


class FallbackGetModel(GetModel):
    """
    A GetModel that tries multiple models in sequence until one succeeds.

    This model implements a fallback pattern where if the primary model fails to extract
    data, it automatically tries the next model in the list. This is useful for graceful
    degradation and robust data extraction.

    Args:
        models (list[GetModel]): List of GetModel instances to try in order.
            Must contain at least one model.

    Example:
        ```python
        from askui import VisionAgent
        from askui.models.askui.gemini_get_model import AskUiGeminiGetModel
        from askui.models.anthropic.models import ClaudeGetModel
        from askui.models.fallback_model import FallbackGetModel

        # Create fallback model that tries Gemini first, then Claude
        fallback_model = FallbackGetModel(
            models=[
                AskUiGeminiGetModel(...),
                ClaudeGetModel(...),
            ]
        )

        with VisionAgent(get_model=fallback_model) as agent:
            result = agent.get("What is the main heading?")
        ```
    """

    def __init__(
        self,
        models: Annotated[list[GetModel], Field(min_length=1)],
    ) -> None:
        self._models = models

    @override
    def get(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None,
        get_settings: GetSettings,
    ) -> ResponseSchema | str:
        """
        Attempts to extract data using each model in sequence.

        Tries each model in the order they were provided. If a model fails (raises an
        exception), the next model is tried. If all models fail, the exception from the
        last model is raised.

        Args:
            query (str): The query describing what data to extract.
            source (Source): The source to extract data from.
            response_schema (Type[ResponseSchema] | None): Optional schema for
                structured output.
            get_settings (GetSettings): Settings for the get operation.

        Returns:
            ResponseSchema | str: The extracted data, either as a string or
                structured schema.

        Raises:
            Exception: The exception from the last model if all models fail.
        """
        last_exception = None

        for i, model in enumerate(self._models):
            try:
                logger.debug(
                    "Trying get model %d/%d",
                    i + 1,
                    len(self._models),
                )
                result = model.get(
                    query=query,
                    source=source,
                    response_schema=response_schema,
                    get_settings=get_settings,
                )
                logger.debug(
                    "Get model %d/%d succeeded",
                    i + 1,
                    len(self._models),
                )
                return result  # noqa: TRY300
            except Exception as e:  # noqa: BLE001, PERF203
                logger.debug(
                    "Get model %d/%d failed: %s",
                    i + 1,
                    len(self._models),
                    str(e),
                )
                last_exception = e
                continue

        # All models failed, raise the last exception
        if last_exception:
            raise last_exception
        # This should never happen since we validated min_length=1
        msg = "No models provided to FallbackGetModel"
        raise ValueError(msg)
