from pathlib import Path
from typing import Union

from filetype import guess  # type: ignore[import-untyped]
from PIL import Image

from askui.utils.image_utils import ImageSource
from askui.utils.pdf_utils import PdfSource

Source = Union[ImageSource, PdfSource]


def load_source(source: Union[str, Path, Image.Image]) -> Source:
    """Load a source and return appropriate Source object based on file type."""

    if isinstance(source, Image.Image):
        return ImageSource(source)

    filepath = Path(source)
    if not filepath.is_file():
        msg = f"No such file or directory: '{source}'"
        raise FileNotFoundError(msg)

    kind = guess(str(filepath))
    if kind and kind.mime == "application/pdf":
        return PdfSource(source)
    if kind and kind.mime.startswith("image/"):
        return ImageSource(source)
    msg = f"Unsupported file type: {filepath.suffix}"
    raise ValueError(msg)


__all__ = ["load_source", "Source"]
