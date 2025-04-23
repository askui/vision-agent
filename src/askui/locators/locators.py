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
    
    def _str(self) -> str:
        return "locator"

    pass


class Prompt(Locator):
    """Locator for finding ui elements by a textual prompt / description of a ui element, e.g., "green sign up button"."""

    @validate_call
    def __init__(
        self,
        prompt: Annotated[
            str,
            Field(
                description="""A textual prompt / description of a ui element, e.g., "green sign up button"."""
            ),
        ],
    ) -> None:
        """Initialize a Prompt locator.

        Args:
            prompt: A textual prompt / description of a ui element, e.g., "green sign up button"
        """
        super().__init__()
        self._prompt = prompt

    @property
    def prompt(self) -> str:
        return self._prompt
    
    def _str(self) -> str:
        return f'element with prompt "{self.prompt}"'


class Element(Locator):
    """Locator for finding ui elements by a class name assigned to the ui element, e.g., by a computer vision model."""

    @validate_call
    def __init__(
        self,
        class_name: Annotated[
            Literal["text", "textfield"] | None,
            Field(
                description="""The class name of the ui element, e.g., 'text' or 'textfield'."""
            ),
        ] = None,
    ) -> None:
        """Initialize an Element locator.

        Args:
            class_name: The class name of the ui element, e.g., 'text' or 'textfield'
        """
        super().__init__()
        self._class_name = class_name

    @property
    def class_name(self) -> Literal["text", "textfield"] | None:
        return self._class_name

    def _str(self) -> str:
        return (
            f'element with class "{self.class_name}"' if self.class_name else "element"
        )


TextMatchType = Literal["similar", "exact", "contains", "regex"]
DEFAULT_TEXT_MATCH_TYPE: TextMatchType = "similar"
DEFAULT_SIMILARITY_THRESHOLD = 70


class Text(Element):
    """Locator for finding text elements by their content."""

    @validate_call
    def __init__(
        self,
        text: Annotated[
            str | None,
            Field(
                description="""The text content of the ui element, e.g., 'Sign up'."""
            ),
        ] = None,
        match_type: Annotated[
            TextMatchType,
            Field(
                description="""The type of match to use. Defaults to 'similar'.
            'similar' uses a similarity threshold to determine if the text is a match.
            'exact' requires the text to be exactly the same.
            'contains' requires the text to contain the specified text.
            'regex' uses a regular expression to match the text."""
            ),
        ] = DEFAULT_TEXT_MATCH_TYPE,
        similarity_threshold: Annotated[
            int,
            Field(
                ge=0,
                le=100,
                description="""A threshold for how similar the text 
            needs to be to the text content of the ui element to be considered a match. 
            Takes values between 0 and 100 (higher is more similar). Defaults to 70. 
            Only used if match_type is 'similar'.""",
            ),
        ] = DEFAULT_SIMILARITY_THRESHOLD,
    ) -> None:
        """Initialize a Text locator.

        Args:
            text: The text content of the ui element, e.g., 'Sign up'
            match_type: The type of match to use. Defaults to 'similar'. 'similar' uses a similarity threshold to
                determine if the text is a match. 'exact' requires the text to be exactly the same. 'contains'
                requires the text to contain the specified text. 'regex' uses a regular expression to match the text.
            similarity_threshold: A threshold for how similar the text needs to be to the text content of the ui
                element to be considered a match. Takes values between 0 and 100 (higher is more similar).
                Defaults to 70. Only used if match_type is 'similar'.
        """
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

    def _str(self) -> str:
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
        return result


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
        if threshold > stop_threshold:
            raise ValueError(
                f"threshold ({threshold}) must be less than or equal to stop_threshold ({stop_threshold})"
            )
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
    
    def _params_str(self) -> str:
        return (
            "("
            + ", ".join([
                f"threshold: {self.threshold}",
                f"stop_threshold: {self.stop_threshold}",
                f"rotation_degree_per_step: {self.rotation_degree_per_step}",
                f"image_compare_format: {self.image_compare_format}",
                f"mask: {self.mask}"
            ])
            + ")"
        )
    
    def _str(self) -> str:
        return (
            f'element "{self.name}" located by image '
            + self._params_str()
        )


def _generate_name() -> str:
    return f"anonymous image {uuid.uuid4()}"


class Image(ImageBase):
    """Locator for finding ui elements by an image."""

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        image: Union[PILImage.Image, pathlib.Path, str],
        threshold: Annotated[
            float,
            Field(
                ge=0,
                le=1,
                description="""A threshold for how similar UI elements need to be to the image to be considered a match. 
            Takes values between 0.0 (= all elements are recognized) and 1.0 (= elements need to look exactly 
            like defined). Defaults to 0.5. Important: The threshold impacts the prediction quality.""",
            ),
        ] = 0.5,
        stop_threshold: Annotated[
            float | None,
            Field(
                ge=0,
                le=1,
                description="""A threshold for when to stop searching for UI elements similar to the image. As soon 
            as UI elements have been found that are at least as similar as the stop_threshold, the search stops. Should 
            be greater than or equal to threshold. Takes values between 0.0 and 1.0. Defaults to value of `threshold` if 
            not provided. Important: The stop_threshold impacts the prediction speed.""",
            ),
        ] = None,
        mask: Annotated[
            list[tuple[float, float]] | None,
            Field(
                min_length=3,
                description="A polygon to match only a certain area of the image.",
            ),
        ] = None,
        rotation_degree_per_step: Annotated[
            int,
            Field(
                ge=0,
                lt=360,
                description="""A step size in rotation degree. Rotates the image by rotation_degree_per_step until 
            360° is exceeded. Range is between 0° - 360°. Defaults to 0°. Important: This increases the prediction time 
            quite a bit. So only use it when absolutely necessary.""",
            ),
        ] = 0,
        name: str | None = None,
        image_compare_format: Annotated[
            Literal["RGB", "grayscale", "edges"],
            Field(
                description="""A color compare style. Defaults to 'grayscale'. 
            Important: The image_compare_format impacts the prediction time as well as quality. As a rule of thumb, 
            'edges' is likely to be faster than 'grayscale' and 'grayscale' is likely to be faster than 'RGB'. For 
            quality it is most often the other way around."""
            ),
        ] = "grayscale",
    ) -> None:
        """Initialize an Image locator.

        Args:
            image: The image to match against (PIL Image, path, or string)
            threshold: A threshold for how similar UI elements need to be to the image to be considered a match.
                Takes values between 0.0 (= all elements are recognized) and 1.0 (= elements need to look exactly
                like defined). Defaults to 0.5. Important: The threshold impacts the prediction quality.
            stop_threshold: A threshold for when to stop searching for UI elements similar to the image. As soon
                as UI elements have been found that are at least as similar as the stop_threshold, the search stops.
                Should be greater than or equal to threshold. Takes values between 0.0 and 1.0. Defaults to value of
                `threshold` if not provided. Important: The stop_threshold impacts the prediction speed.
            mask: A polygon to match only a certain area of the image. Must have at least 3 points.
            rotation_degree_per_step: A step size in rotation degree. Rotates the image by rotation_degree_per_step
                until 360° is exceeded. Range is between 0° - 360°. Defaults to 0°. Important: This increases the
                prediction time quite a bit. So only use it when absolutely necessary.
            name: Optional name for the image. Defaults to generated UUID.
            image_compare_format: A color compare style. Defaults to 'grayscale'. Important: The image_compare_format
                impacts the prediction time as well as quality. As a rule of thumb, 'edges' is likely to be faster
                than 'grayscale' and 'grayscale' is likely to be faster than 'RGB'. For quality it is most often
                the other way around.
        """
        super().__init__(
            threshold=threshold,
            stop_threshold=stop_threshold or threshold,
            mask=mask,
            rotation_degree_per_step=rotation_degree_per_step,
            image_compare_format=image_compare_format,
            name=_generate_name() if name is None else name,
        )  # type: ignore
        self._image = ImageSource(image)

    @property
    def image(self) -> ImageSource:
        return self._image


class AiElement(ImageBase):
    """Locator for finding ui elements by an image and other kinds data saved on the disk."""

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        name: str,
        threshold: Annotated[
            float,
            Field(
                ge=0,
                le=1,
                description="""A threshold for how similar UI elements need to be to be considered a match. 
            Takes values between 0.0 (= all elements are recognized) and 1.0 (= elements need to be an exact match). 
            Defaults to 0.5. Important: The threshold impacts the prediction quality.""",
            ),
        ] = 0.5,
        stop_threshold: Annotated[
            float | None,
            Field(
                ge=0,
                le=1,
                description="""A threshold for when to stop searching for UI elements. As soon 
            as UI elements have been found that are at least as similar as the stop_threshold, the search stops. 
            Should be greater than or equal to threshold. Takes values between 0.0 and 1.0. 
            Defaults to value of `threshold` if not provided. 
            Important: The stop_threshold impacts the prediction speed.""",
            ),
        ] = None,
        mask: Annotated[
            list[tuple[float, float]] | None,
            Field(
                min_length=3,
                description="A polygon to match only a certain area of the image of the element saved on disk.",
            ),
        ] = None,
        rotation_degree_per_step: Annotated[
            int,
            Field(
                ge=0,
                lt=360,
                description="""A step size in rotation degree. Rotates the image of the element saved on disk by 
            rotation_degree_per_step until 360° is exceeded. Range is between 0° - 360°. Defaults to 0°. 
            Important: This increases the prediction time quite a bit. So only use it when absolutely necessary.""",
            ),
        ] = 0,
        image_compare_format: Annotated[
            Literal["RGB", "grayscale", "edges"],
            Field(
                description="""A color compare style. Defaults to 'grayscale'. 
            Important: The image_compare_format impacts the prediction time as well as quality. As a rule of thumb, 
            'edges' is likely to be faster than 'grayscale' and 'grayscale' is likely to be faster than 'RGB'. For 
            quality it is most often the other way around."""
            ),
        ] = "grayscale",
    ) -> None:
        """Initialize an AiElement locator.

        Args:
            name: Name of the AI element
            threshold: A threshold for how similar UI elements need to be to be considered a match. Takes values
                between 0.0 (= all elements are recognized) and 1.0 (= elements need to be an exact match).
                Defaults to 0.5. Important: The threshold impacts the prediction quality.
            stop_threshold: A threshold for when to stop searching for UI elements. As soon as UI elements have
                been found that are at least as similar as the stop_threshold, the search stops. Should be greater
                than or equal to threshold. Takes values between 0.0 and 1.0. Defaults to value of `threshold` if not
                provided. Important: The stop_threshold impacts the prediction speed.
            mask: A polygon to match only a certain area of the image of the element saved on disk. Must have at
                least 3 points.
            rotation_degree_per_step: A step size in rotation degree. Rotates the image of the element saved on
                disk by rotation_degree_per_step until 360° is exceeded. Range is between 0° - 360°. Defaults to 0°.
                Important: This increases the prediction time quite a bit. So only use it when absolutely necessary.
            image_compare_format: A color compare style. Defaults to 'grayscale'. Important: The image_compare_format
                impacts the prediction time as well as quality. As a rule of thumb, 'edges' is likely to be faster
                than 'grayscale' and 'grayscale' is likely to be faster than 'RGB'. For quality it is most often
                the other way around.
        """
        super().__init__(
            name=name,
            threshold=threshold,
            stop_threshold=stop_threshold or threshold,
            mask=mask,
            rotation_degree_per_step=rotation_degree_per_step,
            image_compare_format=image_compare_format,
        )  # type: ignore

    def _str(self) -> str:
        return (
            f'ai element named "{self.name}" '
            + self._params_str()
        )
