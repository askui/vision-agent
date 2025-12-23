import abc
import re
from collections.abc import Iterator
from typing import Annotated, Type

from pydantic import BaseModel, ConfigDict, Field, RootModel

from askui.locators.locators import Locator
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.image_utils import ImageSource
from askui.utils.source_utils import Source


class ModelName:
    """Enumeration of all available model names in AskUI.

    This enum is not really an `enum.Enum` but rather a collection of literal strings.
    It provides type-safe access to model identifiers used throughout the
    library. Each model name corresponds to a specific AI model or model composition
    that can be used for different tasks like acting, getting information, or locating
    elements.
    """

    ASKUI = "askui"
    ASKUI__GEMINI__2_5__FLASH = "askui/gemini-2.5-flash"
    ASKUI__GEMINI__2_5__PRO = "askui/gemini-2.5-pro"
    ASKUI__AI_ELEMENT = "askui-ai-element"
    ASKUI__COMBO = "askui-combo"
    ASKUI__OCR = "askui-ocr"
    ASKUI__PTA = "askui-pta"
    CLAUDE__SONNET__4__20250514 = "claude-sonnet-4-20250514"
    CLAUDE__HAIKU__4_5__20250514 = "claude-haiku-4-5-20251001"
    CLAUDE__SONNET__4_5__20250514 = "claude-sonnet-4-5-20250929"
    CLAUDE__OPUS__4_5__20250514 = "claude-opus-4-5-20251101"
    GEMINI__2_5__FLASH = "gemini-2.5-flash"
    GEMINI__2_5__PRO = "gemini-2.5-pro"
    HF__SPACES__ASKUI__PTA_1 = "AskUI/PTA-1"
    HF__SPACES__OS_COPILOT__OS_ATLAS_BASE_7B = "OS-Copilot/OS-Atlas-Base-7B"
    HF__SPACES__QWEN__QWEN2_VL_2B_INSTRUCT = "Qwen/Qwen2-VL-2B-Instruct"
    HF__SPACES__QWEN__QWEN2_VL_7B_INSTRUCT = "Qwen/Qwen2-VL-7B-Instruct"
    HF__SPACES__SHOWUI__2B = "showlab/ShowUI-2B"
    TARS = "tars"


Point = tuple[int, int]
"""
A tuple of two integers representing the coordinates of a point on the screen.
"""

PointList = Annotated[list[Point], Field(min_length=1)]
"""
A list of points representing the coordinates of elements on the screen.
"""


class BoundingBox(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )

    xmin: int
    ymin: int
    xmax: int
    ymax: int

    @staticmethod
    def from_json(data: dict[str, float]) -> "BoundingBox":
        return BoundingBox(
            xmin=int(data["xmin"]),
            ymin=int(data["ymin"]),
            xmax=int(data["xmax"]),
            ymax=int(data["ymax"]),
        )

    def __str__(self) -> str:
        return f"[{self.xmin}, {self.ymin}, {self.xmax}, {self.ymax}]"

    @property
    def width(self) -> int:
        """The width of the bounding box."""
        return self.xmax - self.xmin

    @property
    def height(self) -> int:
        """The height of the bounding box."""
        return self.ymax - self.ymin

    @property
    def center(self) -> Point:
        """The center point of the bounding box."""
        return int((self.xmin + self.xmax) / 2), int((self.ymin + self.ymax) / 2)


class DetectedElement(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )

    name: str
    text: str
    bounding_box: BoundingBox

    @staticmethod
    def from_json(data: dict[str, str | float | dict[str, float]]) -> "DetectedElement":
        return DetectedElement(
            name=str(data["name"]),
            text=str(data["text"]),
            bounding_box=BoundingBox.from_json(data["bndbox"]),  # type: ignore
        )

    def __str__(self) -> str:
        return f"[name={self.name}, text={self.text}, bndbox={str(self.bounding_box)}]"

    @property
    def center(self) -> Point:
        """The center point of the detected element."""
        return self.bounding_box.center

    @property
    def width(self) -> int:
        """The width of the detected element."""
        return self.bounding_box.width

    @property
    def height(self) -> int:
        """The height of the detected element."""
        return self.bounding_box.height


class GetModel(abc.ABC):
    """Abstract base class for models that can extract information from images and PDFs.

    Models implementing this interface can be used with the `get()` method of
    `VisionAgent` to extract information from screenshots, other images or PDFs.
    These models analyze visual content and return structured or unstructured
    information based on queries.

    Example:
        ```python
        from askui import GetModel, VisionAgent, ResponseSchema, Source
        from typing import Type

        class MyGetModel(GetModel):
            model_name = "my-custom-model"  # Fixed model name

            def get(
                self,
                query: str,
                source: Source,
                response_schema: Type[ResponseSchema] | None,
            ) -> ResponseSchema | str:
                # Implement custom get logic
                return "Custom response"

        # Pass the custom model directly to the get() method
        with VisionAgent() as agent:
            custom_model = MyGetModel()
            result = agent.get("what's on screen?", get_model=custom_model)
        ```
    """

    @abc.abstractmethod
    def get(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None,
    ) -> ResponseSchema | str:
        """Extract information from a source based on a query.

        Args:
            query (str): A description of what information to extract
            source (Source): The source to analyze (screenshot, image or PDF)
            response_schema (Type[ResponseSchema] | None): Optional Pydantic model class
                defining the expected response structure

        Returns:
            Either a string response or a Pydantic model instance if response_schema is
            provided

        Note:
            The model should use its own model_name attribute internally to determine
            which underlying model to use.
        """
        raise NotImplementedError


class LocateModel(abc.ABC):
    """Abstract base class for models that can locate UI elements in images.

    Models implementing this interface can be used with the `locate()` method of
    `VisionAgent` to find UI elements on screen. These models analyze visual content
    to determine the coordinates of elements based on descriptions or locators.

    Example:
        ```python
        from askui import LocateModel, VisionAgent, Locator, ImageSource, PointList

        class MyLocateModel(LocateModel):
            model_name = "my-custom-model"  # Fixed model name

            def locate(
                self,
                locator: str | Locator,
                image: ImageSource,
            ) -> PointList:
                # Implement custom locate logic
                return [(100, 100)]

            def locate_all_elements(
                self,
                image: ImageSource,
            ) -> list[DetectedElement]:
                # Implement custom locate all logic
                return []

        # Pass the custom model directly to the locate() method
        with VisionAgent() as agent:
            custom_model = MyLocateModel()
            point = agent.locate("button", locate_model=custom_model)
        ```
    """

    @abc.abstractmethod
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
    ) -> PointList:
        """Find the coordinates of a UI element in an image.

        Args:
            locator (str | Locator): A description or locator object identifying the
                element to find
            image (ImageSource): The image to analyze (screenshot or provided image)

        Returns:
            A list of (x, y) coordinates where the element was found, minimum length 1

        Note:
            The model should use its own model_name or model composition attribute
            internally to determine which underlying model to use.
        """
        raise NotImplementedError

    def locate_all_elements(
        self,
        image: ImageSource,
    ) -> list[DetectedElement]:
        """Locate all elements in an image.

        Args:
            image (ImageSource): The image to analyze (screenshot or provided image)

        Returns:
            A list of detected elements

        Note:
            The model should use its own model_name or model composition attribute
            internally to determine which underlying model to use.
        """
        raise NotImplementedError
