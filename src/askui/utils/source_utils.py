import base64
import re
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Literal, Union

from filetype import guess  # type: ignore[import-untyped]
from PIL import Image as PILImage

from askui.utils.excel_utils import OfficeDocumentSource
from askui.utils.image_utils import ImageSource
from askui.utils.pdf_utils import PdfSource

InputSource = Union[str, Path, PILImage.Image]
"""
Type of the input images and files for `askui.VisionAgent.get()` and images for 
`askui.VisionAgent.locate()`, etc.

Accepts:
- `PIL.Image.Image`
- Relative or absolute file path (`str` or `pathlib.Path`)
- Data URL (e.g., `"data:image/png;base64,..."`)
"""

Source = Union[ImageSource, PdfSource, OfficeDocumentSource]

_DATA_URL_WITH_MIMETYPE_RE = re.compile(r"^data:([^;,]+)([^,]*)?,(.*)$", re.DOTALL)

_SupportedImageMimeTypes = Literal["image/png", "image/jpeg", "image/gif", "image/webp"]
_SupportedApplicationMimeTypes = Literal[
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]
_SupportedMimeTypes = _SupportedImageMimeTypes | _SupportedApplicationMimeTypes

_SUPPORTED_MIME_TYPES: list[_SupportedMimeTypes] = [
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]


class _SourceType(Enum):
    DATA_URL = "data_url"
    FILE = "file"
    UNKNOWN = "unknown"


@dataclass
class _SourceAnalysis:
    type: _SourceType = _SourceType.UNKNOWN
    mime: str | None = None
    content: Path | bytes | None = None

    @property
    def is_supported(self) -> bool:
        return bool(self.mime) and self.mime in _SUPPORTED_MIME_TYPES

    @property
    def is_pdf(self) -> bool:
        return self.mime == "application/pdf"

    @property
    def is_supported_office_document(self) -> bool:
        return self.mime in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]

    @property
    def is_image(self) -> bool:
        if self.mime:
            return self.mime.startswith("image/")
        return False


def _analyze_data_url(source: str) -> _SourceAnalysis | None:
    if (
        (match := _DATA_URL_WITH_MIMETYPE_RE.match(source))
        and (mime := match.group(1))
        and (is_base64 := match.group(2) == ";base64")
        and (data := match.group(3))
    ):
        data_decoded = base64.b64decode(data) if is_base64 else data.encode()
        return _SourceAnalysis(
            type=_SourceType.DATA_URL,
            mime=mime,
            content=data_decoded,
        )
    return None


def _analyze_file(source: str | Path) -> _SourceAnalysis | None:
    if (kind := guess(str(source))) and (mime := kind.mime):
        return _SourceAnalysis(
            type=_SourceType.FILE,
            mime=mime,
            content=Path(source),
        )
    return None


def _analyze_source(source: Union[str, Path]) -> _SourceAnalysis:
    """Analyze a source (data url (`str`) or file path (`str` or `Path`)).

    Args:
        source (Union[str, Path]): The source to analyze.

    Returns:
        SourceAnalysis: The analysis of the source.

    Raises:
        binascii.Error: If the data within data url cannot be decoded.
        FileNotFoundError: If the source is regarded to be a file path and does not
            exist.
    """
    if isinstance(source, str) and (result := _analyze_data_url(source)):
        return result
    if result := _analyze_file(source):
        return result
    return _SourceAnalysis(type=_SourceType.UNKNOWN)


def load_source(source: Union[str, Path, PILImage.Image]) -> Source:
    """Load a source and return it as an ImageSource or PdfSource.

    Args:
        source (Union[str, Path]): The source to load.

    Returns:
        Source: The loaded source as an ImageSource or PdfSource.

    Raises:
        ValueError: If the source is not a valid image or PDF file.
        FileNotFoundError: If the source is regarded to be a file path and does not
            exist.
        binascii.Error: If the data within data url cannot be decoded.
    """

    if isinstance(source, PILImage.Image):
        return ImageSource(source)
    source_analysis = _analyze_source(source)
    if not source_analysis.is_supported:
        msg = (
            f"Unsupported mime type: {source_analysis.mime} "
            f"(supported: {_SUPPORTED_MIME_TYPES})"
        )
        raise ValueError(msg)
    if not source_analysis.content:
        msg = "No content to read from"
        raise ValueError(msg)
    if source_analysis.is_pdf:
        return PdfSource(source_analysis.content)
    if source_analysis.is_supported_office_document:
        return OfficeDocumentSource(source_analysis.content)
    if source_analysis.is_image:
        return ImageSource(
            PILImage.open(
                BytesIO(source_analysis.content)
                if isinstance(source_analysis.content, bytes)
                else source_analysis.content
            )
        )
    msg = "Unsupported source type"
    raise ValueError(msg)


def load_image_source(source: Union[str, Path, PILImage.Image]) -> ImageSource:
    """Load a source and return it as an ImageSource.

    Args:
        source (Union[str, Path]): The source to load.

    Returns:
        ImageSource: The loaded source.

    Raises:
        ValueError: If the source is not a valid image.
        FileNotFoundError: If the source is regarded to be a file path and does not
            exist.
        binascii.Error: If the data within data url cannot be decoded.
    """
    result = load_source(source)
    if not isinstance(result, ImageSource):
        msg = "Source is not an image"
        raise TypeError(msg)
    return result


__all__ = ["Source", "load_source", "load_image_source", "InputSource"]
