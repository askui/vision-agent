import base64
import binascii
import io
import pathlib
import re
from io import BytesIO
from pathlib import Path
from typing import Any, Literal, Tuple, Union

from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError
from PIL import Image as PILImage
from pydantic import ConfigDict, RootModel, field_validator

# Regex to capture any kind of valid base64 data url (with optional media type and ;base64)
# e.g., data:image/png;base64,... or data:;base64,... or data:,... or just ,...
_DATA_URL_GENERIC_RE = re.compile(r"^(?:data:)?[^,]*?,(.*)$", re.DOTALL)


def load_image(source: Union[str, Path, Image.Image]) -> Image.Image:
    """Load and validate an image from a PIL Image, a path, or any form of base64 data URL.

    Args:
        source (Union[str, Path, Image.Image]): The image source to load from.
            Can be a PIL Image, file path (`str` or `pathlib.Path`), or data URL.

    Returns:
        Image.Image: A valid PIL Image object.

    Raises:
        ValueError: If the input is not a valid or recognizable image.
    """
    if isinstance(source, Image.Image):
        return source

    if isinstance(source, Path) or (
        isinstance(source, str) and not source.startswith(("data:", ","))
    ):
        try:
            return Image.open(source)
        except (OSError, FileNotFoundError, UnidentifiedImageError) as e:
            error_msg = f"Could not open image from file path: {source}"
            raise ValueError(error_msg) from e

    if isinstance(source, str):
        match = _DATA_URL_GENERIC_RE.match(source)
        if match:
            try:
                image_data = base64.b64decode(match.group(1))
                return Image.open(io.BytesIO(image_data))
            except (binascii.Error, UnidentifiedImageError):
                try:
                    return Image.open(source)
                except (FileNotFoundError, UnidentifiedImageError) as e:
                    error_msg = (
                        f"Could not decode or identify image from input:"
                        f"{source[:100]}{'...' if len(source) > 100 else ''}"
                    )
                    raise ValueError(error_msg) from e

    error_msg = f"Unsupported image input type: {type(source)}"
    raise ValueError(error_msg)


def image_to_data_url(image: PILImage.Image) -> str:
    """Convert a PIL Image to a data URL.

    Args:
        image (PILImage.Image): The PIL Image to convert.

    Returns:
        str: A data URL string in the format "data:image/png;base64,..."
    """
    return f"data:image/png;base64,{image_to_base64(image=image, format_='PNG')}"


def data_url_to_image(data_url: str) -> Image.Image:
    """Convert a data URL to a PIL Image.

    Args:
        data_url (str): The data URL string to convert.

    Returns:
        Image.Image: A PIL Image object.

    Raises:
        ValueError: If the data URL is invalid or the image cannot be decoded.
    """
    data_url = data_url.split(",")[1]
    while len(data_url) % 4 != 0:
        data_url += "="
    image_data = base64.b64decode(data_url)
    return Image.open(BytesIO(image_data))


def draw_point_on_image(
    image: Image.Image, x: int, y: int, size: int = 3
) -> Image.Image:
    """Draw a red point at the specified x,y coordinates on a copy of the input image.

    Args:
        image (Image.Image): The PIL Image to draw on.
        x (int): The x-coordinate for the point.
        y (int): The y-coordinate for the point.
        size (int, optional): The size of the point in pixels. Defaults to `3`.

    Returns:
        Image.Image: A new PIL Image with the point drawn.
    """
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    draw.ellipse([x - size, y - size, x + size, y + size], fill="red")
    return img_copy


def base64_to_image(base64_string: str) -> Image.Image:
    """Convert a base64 string to a PIL Image.

    Args:
        base64_string (str): The base64 encoded image string.

    Returns:
        Image.Image: A PIL Image object.

    Raises:
        ValueError: If the base64 string is invalid or the image cannot be decoded.
    """
    image_bytes = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(image_bytes))


def image_to_base64(
    image: Union[pathlib.Path, Image.Image], format_: Literal["PNG", "JPEG"] = "PNG"
) -> str:
    """Convert an image to a base64 string.

    Args:
        image (Union[pathlib.Path, Image.Image]): The image to convert, either a PIL Image or a file path.
        format_ (Literal["PNG", "JPEG"], optional): The image format to use. Defaults to `"PNG"`.

    Returns:
        str: A base64 encoded string of the image.

    Raises:
        ValueError: If the image cannot be encoded or the format is unsupported.
    """
    image_bytes: bytes | None = None
    if isinstance(image, Image.Image):
        with io.BytesIO() as _bytes:
            image.save(_bytes, format=format_)
            image_bytes = _bytes.getvalue()
    elif isinstance(image, pathlib.Path):
        with Path.open(image, "rb") as f:
            image_bytes = f.read()
    return base64.b64encode(image_bytes).decode("utf-8")


def scale_image_with_padding(
    image: Image.Image, max_width: int, max_height: int
) -> Image.Image:
    """Scale an image to fit within specified dimensions while maintaining aspect ratio and adding padding.

    Args:
        image (Image.Image): The PIL Image to scale.
        max_width (int): The maximum width of the output image.
        max_height (int): The maximum height of the output image.

    Returns:
        Image.Image: A new PIL Image that fits within the specified dimensions with padding.
    """
    original_width, original_height = image.size
    aspect_ratio = original_width / original_height
    if (max_width / max_height) > aspect_ratio:
        scale_factor = max_height / original_height
    else:
        scale_factor = max_width / original_width
    scaled_width = int(original_width * scale_factor)
    scaled_height = int(original_height * scale_factor)
    scaled_image = image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
    pad_left = (max_width - scaled_width) // 2
    pad_top = (max_height - scaled_height) // 2
    return ImageOps.expand(
        scaled_image,
        border=(
            pad_left,
            pad_top,
            max_width - scaled_width - pad_left,
            max_height - scaled_height - pad_top,
        ),
        fill=(0, 0, 0),  # Black padding
    )


def scale_coordinates_back(
    x: float,
    y: float,
    original_width: int,
    original_height: int,
    max_width: int,
    max_height: int,
) -> Tuple[float, float]:
    """Convert coordinates from a scaled and padded image back to the original image coordinates.

    Args:
        x (float): The x-coordinate in the scaled image.
        y (float): The y-coordinate in the scaled image.
        original_width (int): The width of the original image.
        original_height (int): The height of the original image.
        max_width (int): The maximum width used for scaling.
        max_height (int): The maximum height used for scaling.

    Returns:
        Tuple[float, float]: A tuple of (original_x, original_y) coordinates.

    Raises:
        ValueError: If the coordinates are outside the padded image area.
    """
    aspect_ratio = original_width / original_height
    if (max_width / max_height) > aspect_ratio:
        scale_factor = max_height / original_height
        scaled_width = int(original_width * scale_factor)
        scaled_height = max_height
    else:
        scale_factor = max_width / original_width
        scaled_width = max_width
        scaled_height = int(original_height * scale_factor)
    pad_left = (max_width - scaled_width) // 2
    pad_top = (max_height - scaled_height) // 2
    adjusted_x = x - pad_left
    adjusted_y = y - pad_top
    if (
        adjusted_x < 0
        or adjusted_y < 0
        or adjusted_x > scaled_width
        or adjusted_y > scaled_height
    ):
        error_msg = "Coordinates are outside the padded image area"
        raise ValueError(error_msg)
    original_x = adjusted_x / scale_factor
    original_y = adjusted_y / scale_factor
    return original_x, original_y


Img = Union[str, Path, PILImage.Image]
"""Type of the input images for `askui.VisionAgent.get()`, `askui.VisionAgent.locate()`, etc.

Accepts:
- `PIL.Image.Image`
- Relative or absolute file path (`str` or `pathlib.Path`)
- Data URL (e.g., `"data:image/png;base64,..."`)
"""


class ImageSource(RootModel):
    """A Pydantic model that represents an image source and provides methods to convert it to different formats.

    The model can be initialized with:
    - A PIL Image object
    - A file path (str or pathlib.Path)
    - A data URL string

    Attributes:
        root (PILImage.Image): The underlying PIL Image object.

    Args:
        root (Img): The image source to load from.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    root: PILImage.Image

    def __init__(self, root: Img, **kwargs: dict[str, Any]) -> None:
        super().__init__(root=root, **kwargs)

    @field_validator("root", mode="before")
    @classmethod
    def validate_root(cls, v: Any) -> PILImage.Image:
        return load_image(v)

    def to_data_url(self) -> str:
        """Convert the image to a data URL.

        Returns:
            str: A data URL string in the format `"data:image/png;base64,..."`
        """
        return image_to_data_url(image=self.root)

    def to_base64(self) -> str:
        """Convert the image to a base64 string.

        Returns:
            str: A base64 encoded string of the image.
        """
        return image_to_base64(image=self.root)
