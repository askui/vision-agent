from abc import ABC
import pathlib
from typing import Literal, Union
import uuid

from PIL import Image as PILImage
from pydantic import BaseModel, Field

from askui.locators.image_utils import ImageSource
from askui.locators.relatable import Relatable


class Locator(Relatable, BaseModel, ABC):
    """Base class for all locators."""
    pass


class Description(Locator):
    """Locator for finding ui elements by a textual description of the ui element."""

    description: str

    def __init__(self, description: str, **kwargs) -> None:
        super().__init__(description=description, **kwargs)  # type: ignore

    def _str_with_relation(self) -> str:
        result = f'element with description "{self.description}"'
        return result + super()._relations_str()

    def __str__(self) -> str:
        self.raise_if_cycle()
        return self._str_with_relation()


class Class(Locator):
    """Locator for finding ui elements by a class name assigned to the ui element, e.g., by a computer vision model."""
    class_name: Literal["text", "textfield"] | None = None

    def __init__(
        self,
        class_name: Literal["text", "textfield"] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(class_name=class_name, **kwargs)  # type: ignore

    def _str_with_relation(self) -> str:
        result = (
            f'element with class "{self.class_name}"'
            if self.class_name
            else "element that has a class"
        )
        return result + super()._relations_str()

    def __str__(self) -> str:
        self.raise_if_cycle()
        return self._str_with_relation()


TextMatchType = Literal["similar", "exact", "contains", "regex"]


class Text(Class):
    """Locator for finding text elements by their content."""
    text: str | None = None
    match_type: TextMatchType = "similar"
    similarity_threshold: int = Field(default=70, ge=0, le=100)

    def __init__(
        self,
        text: str | None = None,
        match_type: TextMatchType = "similar",
        similarity_threshold: int = 70,
        **kwargs,
    ) -> None:
        super().__init__(
            text=text,
            match_type=match_type,
            similarity_threshold=similarity_threshold,
            **kwargs,
        )  # type: ignore

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


class ImageMetadata(Locator):
    threshold: float = Field(default=0.5, ge=0, le=1)
    stop_threshold: float = Field(default=0.9, ge=0, le=1)
    mask: list[tuple[float, float]] | None = Field(default=None, min_length=3)
    rotation_degree_per_step: int = Field(default=0, ge=0, lt=360)
    image_compare_format: Literal["RGB", "grayscale", "edges"] = "grayscale"
    name: str


def _generate_name() -> str:
    return f"anonymous custom element {uuid.uuid4()}"


class Image(ImageMetadata):
    """Locator for finding ui elements by an image."""
    image: ImageSource

    def __init__(
        self,
        image: Union[ImageSource, PILImage.Image, pathlib.Path, str],
        threshold: float = 0.5,
        stop_threshold: float = 0.9,
        mask: list[tuple[float, float]] | None = None,
        rotation_degree_per_step: int = 0,
        image_compare_format: Literal["RGB", "grayscale", "edges"] = "grayscale",
        name: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            image=image,
            threshold=threshold,
            stop_threshold=stop_threshold,
            mask=mask,
            rotation_degree_per_step=rotation_degree_per_step,
            image_compare_format=image_compare_format,
            name=_generate_name() if name is None else name,
            **kwargs,
        )  # type: ignore

    def _str_with_relation(self) -> str:
        result = f'element "{self.name}" located by image'
        return result + super()._relations_str()

    def __str__(self) -> str:
        self.raise_if_cycle()
        return self._str_with_relation()


class AiElement(ImageMetadata):
    """Locator for finding ui elements by an image and other kinds data saved on the disk."""
    def __init__(
        self,
        name: str,
        threshold: float = 0.5,
        stop_threshold: float = 0.9,
        mask: list[tuple[float, float]] | None = None,
        rotation_degree_per_step: int = 0,
        image_compare_format: Literal["RGB", "grayscale", "edges"] = "grayscale",
        **kwargs,
    ) -> None:
        super().__init__(
            name=name,
            threshold=threshold,
            stop_threshold=stop_threshold,
            mask=mask,
            rotation_degree_per_step=rotation_degree_per_step,
            image_compare_format=image_compare_format,
            **kwargs,
        )  # type: ignore

    def _str_with_relation(self) -> str:
        result = f'ai element named "{self.name}"'
        return result + super()._relations_str()

    def __str__(self) -> str:
        self.raise_if_cycle()
        return self._str_with_relation()
