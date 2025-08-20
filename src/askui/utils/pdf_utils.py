from io import BufferedReader, BytesIO
from pathlib import Path

from pydantic import ConfigDict, RootModel


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
    root: bytes | Path

    @property
    def reader(self) -> BufferedReader | BytesIO:
        if isinstance(self.root, Path):
            return self.root.open("rb")
        return BytesIO(self.root)


__all__ = [
    "PdfSource",
]
