from pathlib import Path
from typing import Any, Union

from pydantic import ConfigDict, RootModel, field_validator

from askui.utils.io_utils import read_bytes

Pdf = Union[str, Path]
"""Type of the input PDFs for `askui.VisionAgent.get()`, etc.

Accepts:
- Relative or absolute file path (`str` or `pathlib.Path`)
"""


class PdfSource(RootModel):
    """A class that represents a PDF source.
    It provides methods to convert it to different formats.

    The class can be initialized with:
    - A file path (str or pathlib.Path)

    Attributes:
        root (bytes): The underlying PDF bytes.

    Args:
        root (Pdf): The PDF source to load from.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    root: bytes

    def __init__(self, root: Pdf, **kwargs: dict[str, Any]) -> None:
        super().__init__(root=root, **kwargs)

    @field_validator("root", mode="before")
    @classmethod
    def validate_root(cls, v: Any) -> bytes:
        return read_bytes(v)


__all__ = [
    "PdfSource",
    "Pdf",
]
