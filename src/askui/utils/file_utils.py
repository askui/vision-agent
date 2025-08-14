from pathlib import Path
from typing import Union

from PIL import Image as PILImage

from askui.utils.image_utils import ImageSource
from askui.utils.io_utils import source_file_type
from askui.utils.pdf_utils import PdfSource

# to avoid circular imports from image_utils and pdf_utils on read_bytes
Source = Union[ImageSource, PdfSource]

ALLOWED_IMAGE_TYPES = [
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
]

PDF_TYPE = "application/pdf"

ALLOWED_MIMETYPES = [PDF_TYPE] + ALLOWED_IMAGE_TYPES


def load_source(source: Union[str, Path, PILImage.Image]) -> Source:
    """Load a source and return it as an ImageSource or PdfSource.

    Args:
        source (Union[str, Path]): The source to load.

    Returns:
        Source: The loaded source as an ImageSource or PdfSource.

    Raises:
        ValueError: If the source is not a valid image or PDF file.
    """
    if isinstance(source, PILImage.Image):
        return ImageSource(source)

    file_type = source_file_type(source)
    if file_type in ALLOWED_IMAGE_TYPES:
        return ImageSource(source)
    if file_type == PDF_TYPE:
        return PdfSource(source)
    msg = f"Unsupported file type: {file_type}"
    raise ValueError(msg)


__all__ = ["Source", "load_source"]
