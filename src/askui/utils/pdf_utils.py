from pathlib import Path
from typing import Any, Union

from pydantic import ConfigDict, RootModel, field_validator

Pdf = Union[str, Path]
"""Type of the input PDFs for `askui.VisionAgent.get()`, etc.

Accepts:
- Relative or absolute file path (`str` or `pathlib.Path`)
"""


def load_pdf(source: Union[str, Path]) -> bytes:
    """Load a PDF from a path and return its bytes.

    Args:
        source (Union[str, Path]): The PDF source to load from.

    Returns:
        bytes: The PDF content as bytes.

    Raises:
        FileNotFoundError: If the file is not found.
        ValueError: If the file is too large.
    """
    filepath = Path(source)
    if not filepath.is_file():
        err_msg = f"No such file or directory: '{source}'"
        raise FileNotFoundError(err_msg)

    return filepath.read_bytes()


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
        return load_pdf(v)


__all__ = [
    "PdfSource",
    "Pdf",
    "load_pdf",
]
