import pathlib
import uuid
from abc import ABC
from typing import Annotated, Literal, Union

from PIL import Image as PILImage
from pydantic import ConfigDict, Field, validate_call

from askui.locators.relatable import Relatable
from askui.utils.image_utils import ImageSource

TextMatchType = Literal["similar", "exact", "contains", "regex"]
"""The type of match to use.

- `"similar"` uses a similarity threshold to determine if the text is a match.
- `"exact"` requires the text to be exactly the same (this is not the same as `"similar"`
  with a `similarity_threshold` of `100` as a `similarity_threshold` of `100` can still
  allow for small differences in very long texts).
- `"contains"` requires the text to contain (exactly) the specified text.
- `"regex"` uses a regular expression to match the text.
"""


DEFAULT_TEXT_MATCH_TYPE: TextMatchType = "similar"
DEFAULT_SIMILARITY_THRESHOLD = 70


class Locator(Relatable, ABC):
    """Abstract base class for all locators. Cannot be instantiated directly.
    Subclassed by all locators, e.g., `Prompt`, `Text`, `Image`, etc."""

    def _str(self) -> str:
        return "locator"


class Prompt(Locator):
    """Locator for finding ui elements by a textual prompt / description of a ui element, e.g., "green sign up button".

    Args:
        prompt (str): A textual prompt / description of a ui element, e.g., `"green sign up button"`

    Examples:
        ```python
        from askui import locators as loc
        # locates a green sign up button
        button = loc.Prompt("green sign up button")
        # locates an email text field, e.g., with label "Email" or a placeholder "john.doe@example.com"
        textfield = loc.Prompt("email text field")
        # locates the avatar in the right hand corner of the application
        avatar_top_right_corner = loc.Prompt("avatar in the top right corner of the application")
        ```
    """

    @validate_call
    def __init__(
        self,
        prompt: Annotated[
            str,
            Field(min_length=1),
        ],
    ) -> None:
        super().__init__()
        self._prompt = prompt

    def _str(self) -> str:
        return f'element with prompt "{self._prompt}"'


class Element(Locator):
    """Locator for finding ui elements by their class.

    Args:
        class_name (Literal["switch","text", "textfield"] | None, optional): The class of the ui element, e.g., `'text'` or `'textfield'`. Defaults to `None`.

    Examples:
        ```python
        from askui import locators as loc
        # locates a text elementAdd
        text = loc.Element(class_name="text")
        # locates a textfield element
        textfield = loc.Element(class_name="textfield")
        # locates any ui element detected
        element = loc.Element()
        ```
    """

    @validate_call
    def __init__(
        self,
        class_name: Literal["switch", "text", "textfield"] | None = None,
    ) -> None:
        super().__init__()
        self._class_name = class_name

    def _str(self) -> str:
        return (
            f'element with class "{self._class_name}"'
            if self._class_name
            else "element"
        )


class Text(Element):
    """Locator for finding text elements by their textual content.

    Args:
        text (str | None, optional): The text content of the ui element, e.g., `'Sign up'`. Defaults to `None`.
            If `None`, the locator will match any text element.
        match_type (TextMatchType, optional): The type of match to use. Defaults to `"similar"`.
        similarity_threshold (int, optional): A threshold for how similar the actual text content of the ui element
            needs to be to the specified text to be considered a match when `match_type` is `"similar"`.
            Takes values between `0` and `100` (inclusive, higher is more similar).
            Defaults to `70`.

    Examples:
        ```python
        from askui import locators as loc
        # locates a text element with text similar to "Sign up", e.g., "Sign up" or "Sign Up" or "Sign-Up"
        text = loc.Text("Sign up")
        # if it does not find an element, you can try decreasing the similarity threshold (default is `70`)
        text = loc.Text("Sign up", match_type="similar", similarity_threshold=50)
        # if it also locates "Sign In", you can try increasing the similarity threshold (default is `70`)
        text = loc.Text("Sign up", match_type="similar", similarity_threshold=80)
        # or use `match_type="exact"` to require an exact match (does not match other variations of "Sign up", e.g., "Sign Up" or "Sign-Up")
        text = loc.Text("Sign up", match_type="exact")
        # locates a text element starting with "Sign" or "sign" using a regular expression
        text = loc.Text("^[Ss]ign.*", match_type="regex")
        # locates a text element containing "Sign" (exact match)
        text = loc.Text("Sign", match_type="contains")
        ```
    """

    @validate_call
    def __init__(
        self,
        text: Annotated[
            str | None,
            Field(),
        ] = None,
        match_type: Annotated[
            TextMatchType,
            Field(),
        ] = DEFAULT_TEXT_MATCH_TYPE,
        similarity_threshold: Annotated[
            int,
            Field(
                ge=0,
                le=100,
            ),
        ] = DEFAULT_SIMILARITY_THRESHOLD,
    ) -> None:
        super().__init__()
        self._text = text
        self._match_type = match_type
        self._similarity_threshold = similarity_threshold

    def _str(self) -> str:
        if self._text is None:
            result = "text"
        else:
            result = "text "
            match self._match_type:
                case "similar":
                    result += f'similar to "{self._text}" (similarity >= {self._similarity_threshold}%)'
                case "exact":
                    result += f'"{self._text}"'
                case "contains":
                    result += f'containing text "{self._text}"'
                case "regex":
                    result += f'matching regex "{self._text}"'
        return result


class ImageBase(Locator, ABC):
    """Abstract base class for image locators. Cannot be instantiated directly."""

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
            error_msg = f"threshold ({threshold}) must be less than or equal to stop_threshold ({stop_threshold})"
            raise ValueError(error_msg)
        self._threshold = threshold
        self._stop_threshold = stop_threshold
        self._mask = mask
        self._rotation_degree_per_step = rotation_degree_per_step
        self._name = name
        self._image_compare_format = image_compare_format

    def _params_str(self) -> str:
        return (
            "("
            + ", ".join(
                [
                    f"threshold: {self._threshold}",
                    f"stop_threshold: {self._stop_threshold}",
                    f"rotation_degree_per_step: {self._rotation_degree_per_step}",
                    f"image_compare_format: {self._image_compare_format}",
                    f"mask: {self._mask}",
                ]
            )
            + ")"
        )

    def _str(self) -> str:
        return f'element "{self._name}" located by image ' + self._params_str()


def _generate_name() -> str:
    return f"anonymous image {uuid.uuid4()}"


class Image(ImageBase):
    """Locator for finding ui elements by an image.

    Args:
        image (Union[PIL.Image.Image, pathlib.Path, str]): The image to match against (PIL Image, path, or string)
        threshold (float, optional): A threshold for how similar UI elements need to be to the image to be considered a match.
            Takes values between `0.0` (= all elements are recognized) and `1.0` (= elements need to look exactly
            like defined). Defaults to `0.5`. Important: The threshold impacts the prediction quality.
        stop_threshold (float | None, optional): A threshold for when to stop searching for UI elements similar to the image. As soon
            as UI elements have been found that are at least as similar as the `stop_threshold`, the search stops.
            Should be greater than or equal to `threshold`. Takes values between `0.0` and `1.0`. Defaults to value of
            `threshold` if not provided. Important: The `stop_threshold` impacts the prediction speed.
        mask (list[tuple[float, float]] | None, optional): A polygon to match only a certain area of the image. Must have at least 3 points.
            Defaults to `None`.
        rotation_degree_per_step (int, optional): A step size in rotation degree. Rotates the image by `rotation_degree_per_step`
            until 360° is exceeded. Range is between `0°` - `360°`. Defaults to `0°`. Important: This increases the
            prediction time quite a bit. So only use it when absolutely necessary.
        name (str | None, optional): Name for the image. Defaults to random name.
        image_compare_format (Literal["RGB", "grayscale", "edges"], optional): A color compare style. Defaults to `'grayscale'`. **Important**:
            The `image_compare_format` impacts the prediction time as well as quality. As a rule of thumb,
            `'edges'` is likely to be faster than `'grayscale'` and `'grayscale'` is likely to be faster than `'RGB'`.
            For quality it is most often the other way around.

    Examples:
        ```python
        from askui import locators as loc
        from PIL import Image as PILImage
        from pathlib import Path

        # locates an element using an image of the element
        # passed as `str` path
        image = loc.Image("path/to/image.png")
        # passed as `pathlib.Path`
        image = loc.Image(Path("path/to/image.png"))
        # passed as `PIL.Image.Image`
        image = loc.Image(PILImage.open("path/to/image.png"))
        # passed as data url `str`
        image = loc.Image("data:image/png;base64,...")
        ```
    """

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        image: Union[PILImage.Image, pathlib.Path, str],
        threshold: Annotated[
            float,
            Field(
                ge=0.0,
                le=1.0,
            ),
        ] = 0.5,
        stop_threshold: Annotated[
            float | None,
            Field(
                ge=0.0,
                le=1.0,
            ),
        ] = None,
        mask: Annotated[
            list[tuple[float, float]] | None,
            Field(
                min_length=3,
            ),
        ] = None,
        rotation_degree_per_step: Annotated[
            int,
            Field(
                ge=0,
                lt=360,
            ),
        ] = 0,
        name: str | None = None,
        image_compare_format: Annotated[
            Literal["RGB", "grayscale", "edges"],
            Field(),
        ] = "grayscale",
    ) -> None:
        super().__init__(
            threshold=threshold,
            stop_threshold=stop_threshold or threshold,
            mask=mask,
            rotation_degree_per_step=rotation_degree_per_step,
            image_compare_format=image_compare_format,
            name=_generate_name() if name is None else name,
        )
        self._image = ImageSource(image)


class AiElement(ImageBase):
    """
    Locator for finding ui elements by data (e.g., image) collected with the [AskUIRemoteDeviceSnippingTool](http://localhost:3000/02-api-reference/02-askui-suite/02-askui-suite/AskUIRemoteDeviceSnippingTool/Public/AskUI-NewAIElement) using the `name` assigned to the AI element during *snipping* to retrieve the data used for locating the ui element(s).

    Args:
        name (str): Name of the AI element
        threshold (float, optional): A threshold for how similar UI elements need to be to the image to be considered a match.
            Takes values between `0.0` (= all elements are recognized) and `1.0` (= elements need to look exactly
            like defined). Defaults to `0.5`. Important: The threshold impacts the prediction quality.
        stop_threshold (float | None, optional): A threshold for when to stop searching for UI elements similar to the image. As soon
            as UI elements have been found that are at least as similar as the `stop_threshold`, the search stops.
            Should be greater than or equal to `threshold`. Takes values between `0.0` and `1.0`. Defaults to value of
            `threshold` if not provided. Important: The `stop_threshold` impacts the prediction speed.
        mask (list[tuple[float, float]] | None, optional): A polygon to match only a certain area of the image. Must have at least 3 points.
            Defaults to `None`.
        rotation_degree_per_step (int, optional): A step size in rotation degree. Rotates the image by rotation_degree_per_step
            until 360° is exceeded. Range is between `0°` - `360°`. Defaults to `0°`. Important: This increases the
            prediction time quite a bit. So only use it when absolutely necessary.
        name (str | None, optional): Name for the image. Defaults to random name.
        image_compare_format (Literal["RGB", "grayscale", "edges"], optional): A color compare style. Defaults to `'grayscale'`. **Important**:
            The `image_compare_format` impacts the prediction time as well as quality. As a rule of thumb,
            `'edges'` is likely to be faster than `'grayscale'` and `'grayscale'` is likely to be faster than `'RGB'`.
            For quality it is most often the other way around.
    """

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        name: str,
        threshold: Annotated[
            float,
            Field(
                ge=0.0,
                le=1.0,
            ),
        ] = 0.5,
        stop_threshold: Annotated[
            float | None,
            Field(
                ge=0.0,
                le=1.0,
            ),
        ] = None,
        mask: Annotated[
            list[tuple[float, float]] | None,
            Field(
                min_length=3,
            ),
        ] = None,
        rotation_degree_per_step: Annotated[
            int,
            Field(
                ge=0,
                lt=360,
            ),
        ] = 0,
        image_compare_format: Annotated[
            Literal["RGB", "grayscale", "edges"],
            Field(),
        ] = "grayscale",
    ) -> None:
        super().__init__(
            name=name,
            threshold=threshold,
            stop_threshold=stop_threshold or threshold,
            mask=mask,
            rotation_degree_per_step=rotation_degree_per_step,
            image_compare_format=image_compare_format,
        )

    def _str(self) -> str:
        return f'ai element named "{self._name}" ' + self._params_str()
