"""Custom model implementations for flexible user-defined models."""

from collections.abc import Callable
from typing import Type

from typing_extensions import override

from askui.locators.locators import Locator
from askui.models.models import (
    DetectedElement,
    GetModel,
    LocateModel,
    PointList,
)
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.image_utils import ImageSource
from askui.utils.source_utils import Source


class CustomGetModel(GetModel):
    """A flexible custom GetModel that allows users to provide their own implementation.

    This model allows you to create custom get models without defining a new class.
    You provide the model name and a function that implements the get logic.

    Args:
        model_name (str): The name of your custom model
        get_fn (Callable): A function that takes (query, source, response_schema) and
            returns either a ResponseSchema instance or a string

    Example:
        ```python
        from askui import VisionAgent
        from askui.models import CustomGetModel

        def my_get_logic(query, source, response_schema):
            # Your custom implementation here
            return f"Custom response to: {query}"

        custom_model = CustomGetModel(
            model_name="my-custom-model",
            get_fn=my_get_logic
        )

        with VisionAgent() as agent:
            result = agent.get("What's on screen?", get_model=custom_model)
            print(result)  # "Custom response to: What's on screen?"
        ```
    """

    def __init__(
        self,
        model_name: str,
        get_fn: Callable[
            [str, Source, Type[ResponseSchema] | None], ResponseSchema | str
        ],
    ):
        self.model_name = model_name
        self._get_fn = get_fn

    @override
    def get(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None,
    ) -> ResponseSchema | str:
        return self._get_fn(query, source, response_schema)


class CustomLocateModel(LocateModel):
    """A flexible custom LocateModel that allows users to provide their own implementation.

    This model allows you to create custom locate models without defining a new class.
    You provide the model name and functions that implement the locate logic.

    Args:
        model_name (str): The name of your custom model
        locate_fn (Callable): A function that takes (locator, image) and returns a PointList
        locate_all_fn (Callable, optional): A function that takes (image) and returns a
            list of DetectedElement. If not provided, locate_all_elements will raise
            NotImplementedError.

    Example:
        ```python
        from askui import VisionAgent
        from askui.models import CustomLocateModel

        def my_locate_logic(locator, image):
            # Your custom implementation here
            return [(100, 100)]

        def my_locate_all_logic(image):
            # Your custom implementation for locate_all_elements
            return []

        custom_model = CustomLocateModel(
            model_name="my-custom-locate",
            locate_fn=my_locate_logic,
            locate_all_fn=my_locate_all_logic
        )

        with VisionAgent() as agent:
            point = agent.locate("Submit button", locate_model=custom_model)
            print(point)  # (100, 100)
        ```
    """

    def __init__(
        self,
        model_name: str,
        locate_fn: Callable[[str | Locator, ImageSource], PointList],
        locate_all_fn: Callable[[ImageSource], list[DetectedElement]] | None = None,
    ):
        self.model_name = model_name
        self._locate_fn = locate_fn
        self._locate_all_fn = locate_all_fn

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
    ) -> PointList:
        return self._locate_fn(locator, image)

    @override
    def locate_all_elements(
        self,
        image: ImageSource,
    ) -> list[DetectedElement]:
        if self._locate_all_fn is None:
            raise NotImplementedError(
                f"locate_all_elements is not implemented for {self.model_name}. "
                "Provide a locate_all_fn function when creating the CustomLocateModel."
            )
        return self._locate_all_fn(image)
