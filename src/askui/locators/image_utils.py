from typing import Any, Union
from pathlib import Path
from PIL import Image, Image as PILImage, UnidentifiedImageError
import base64
import io
import re
import binascii

from pydantic import RootModel, field_validator, ConfigDict

from askui.tools.utils import image_to_base64

# Regex to capture any kind of valid base64 data url (with optional media type and ;base64)
# e.g., data:image/png;base64,... or data:;base64,... or data:,... or just ,...
_DATA_URL_GENERIC_RE = re.compile(r"^(?:data:)?[^,]*?,(.*)$", re.DOTALL)


def load_image(source: Union[str, Path, Image.Image]) -> Image.Image:
    """
    Load and validate an image from a PIL Image, a path (`str` or `pathlib.Path`), or any form of base64 data URL.

    Accepts:
      - `PIL.Image.Image`
      - File path (`str` or `pathlib.Path`)
      - Data URL (e.g., "data:image/png;base64,...", "data:,...", ",...")

    Returns:
        A valid `PIL.Image.Image` object.

    Raises:
        ValueError: If input is not a valid or recognizable image.
    """
    if isinstance(source, Image.Image):
        return source

    if isinstance(source, Path) or (isinstance(source, str) and not source.startswith(("data:", ","))):
        try:
            return Image.open(source)
        except (OSError, FileNotFoundError, UnidentifiedImageError) as e:
            raise ValueError(f"Could not open image from file path: {source}") from e

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
                    raise ValueError(f"Could not decode or identify image from input: {source[:100]}{'...' if len(source) > 100 else ''}") from e

    raise ValueError(f"Unsupported image input type: {type(source)}")


class ImageSource(RootModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    root: PILImage.Image
    
    def __init__(self, root: Union[str, Path, PILImage.Image], **kwargs):
        super().__init__(root=root, **kwargs)

    @field_validator("root", mode="before")
    @classmethod
    def validate_root(cls, v: Any) -> PILImage.Image:
        return load_image(v)
    
    def to_data_url(self) -> str:
        return f"data:image/png;base64,{image_to_base64(self.root)}"
