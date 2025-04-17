from abc import ABC
import pathlib
from typing import Annotated, Literal, Union
import uuid

from PIL import Image as PILImage
from pydantic import ConfigDict, Field, validate_call

from askui.utils.image_utils import ImageSource
from askui.locators.relatable import Relatable


class Locator(Relatable, ABC):
    """Base class for all locators."""
    pass


class Description(Locator):
    """Locator for finding ui elements by a textual description of the ui element."""

    @validate_call
    def __init__(self, description: str) -> None:
        super().__init__()
        self._description = description
        
    @property
    def description(self) -> str:
        return self._description

    def _str_with_relation(self) -> str:
        result = f'element with description "{self.description}"'
        return result + super()._relations_str()

    def __str__(self) -> str:
        self.raise_if_cycle()
        return self._str_with_relation()


class Element(Locator):
    """Locator for finding ui elements by a class name assigned to the ui element, e.g., by a computer vision model."""
    @validate_call
    def __init__(
        self,
        class_name: Literal["text", "textfield"] | None = None,
    ) -> None:
        super().__init__()
        self._class_name = class_name

    @property
    def class_name(self) -> Literal["text", "textfield"] | None:
        return self._class_name

    def _str_with_relation(self) -> str:
        result = (
            f'element with class "{self.class_name}"'
            if self.class_name
            else "element"
        )
        return result + super()._relations_str()

    def __str__(self) -> str:
        self.raise_if_cycle()
        return self._str_with_relation()


TextMatchType = Literal["similar", "exact", "contains", "regex"]
DEFAULT_TEXT_MATCH_TYPE: TextMatchType = "similar"
DEFAULT_SIMILARITY_THRESHOLD = 70


class Text(Element):
    """Locator for finding text elements by their content."""
    @validate_call
    def __init__(
        self,
        text: str | None = None,
        match_type: TextMatchType = DEFAULT_TEXT_MATCH_TYPE,
        similarity_threshold: Annotated[int, Field(ge=0, le=100)] = DEFAULT_SIMILARITY_THRESHOLD,
    ) -> None:
        super().__init__()
        self._text = text
        self._match_type = match_type
        self._similarity_threshold = similarity_threshold

    @property
    def text(self) -> str | None:
        return self._text

    @property
    def match_type(self) -> TextMatchType:
        return self._match_type
    
    @property
    def similarity_threshold(self) -> int:
        return self._similarity_threshold

    def _str_with_relation(self) -> str:
        if self.text is None:
            result = "text"
        else:
            result = "text "
            match self.match_type:
                case "similar":
                    result += f'similar to "{self.text}" (similarity >= {self.similarity_threshold}%)'
                case "exact":
                    result += f'"{self.text}"'
                case "contains":
                    result += f'containing text "{self.text}"'
                case "regex":
                    result += f'matching regex "{self.text}"'
        return result + super()._relations_str()

    def __str__(self) -> str:
        self.raise_if_cycle()
        return self._str_with_relation()


class ImageBase(Locator, ABC):
    def __init__(
        self,
        threshold: float,
        stop_threshold: float,
        mask: list[tuple[float, float]] | None,
        rotation_degree_per_step: int,
        name: str,
        image_compare_format: Literal["RGB", "grayscale", "edges"],
    ) -> None:
        super().__init__()
        self._threshold = threshold
        self._stop_threshold = stop_threshold
        self._mask = mask
        self._rotation_degree_per_step = rotation_degree_per_step
        self._name = name
        self._image_compare_format = image_compare_format
        
    @property
    def threshold(self) -> float:
        return self._threshold
    
    @property
    def stop_threshold(self) -> float:
        return self._stop_threshold
    
    @property
    def mask(self) -> list[tuple[float, float]] | None:
        return self._mask
    
    @property
    def rotation_degree_per_step(self) -> int:
        return self._rotation_degree_per_step
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def image_compare_format(self) -> Literal["RGB", "grayscale", "edges"]:
        return self._image_compare_format


def _generate_name() -> str:
    return f"anonymous custom element {uuid.uuid4()}"


class Image(ImageBase):
    """Locator for finding ui elements by an image."""
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        image: Union[PILImage.Image, pathlib.Path, str],
        threshold: Annotated[float, Field(ge=0, le=1)] = 0.5,
        stop_threshold: Annotated[float, Field(ge=0, le=1)] = 0.9,
        mask: Annotated[list[tuple[float, float]] | None, Field(min_length=3)] = None,
        rotation_degree_per_step: Annotated[int, Field(ge=0, lt=360)] = 0,
        name: str | None = None,
        image_compare_format: Literal["RGB", "grayscale", "edges"] = "grayscale",
    ) -> None:
        super().__init__(
            threshold=threshold,
            stop_threshold=stop_threshold,
            mask=mask,
            rotation_degree_per_step=rotation_degree_per_step,
            image_compare_format=image_compare_format,
            name=_generate_name() if name is None else name,
        )  # type: ignore
        self._image = ImageSource(image)
        
    @property
    def image(self) -> ImageSource:
        return self._image

    def _str_with_relation(self) -> str:
        result = f'element "{self.name}" located by image'
        return result + super()._relations_str()

    def __str__(self) -> str:
        self.raise_if_cycle()
        return self._str_with_relation()


class AiElement(ImageBase):
    """Locator for finding ui elements by an image and other kinds data saved on the disk."""
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        name: str,
        threshold: Annotated[float, Field(ge=0, le=1)] = 0.5,
        stop_threshold: Annotated[float, Field(ge=0, le=1)] = 0.9,
        mask: Annotated[list[tuple[float, float]] | None, Field(min_length=3)] = None,
        rotation_degree_per_step: Annotated[int, Field(ge=0, lt=360)] = 0,
        image_compare_format: Literal["RGB", "grayscale", "edges"] = "grayscale",
    ) -> None:
        super().__init__(
            name=name,
            threshold=threshold,
            stop_threshold=stop_threshold,
            mask=mask,
            rotation_degree_per_step=rotation_degree_per_step,
            image_compare_format=image_compare_format,
        )  # type: ignore

    def _str_with_relation(self) -> str:
        result = f'ai element named "{self.name}"'
        return result + super()._relations_str()

    def __str__(self) -> str:
        self.raise_if_cycle()
        return self._str_with_relation()
