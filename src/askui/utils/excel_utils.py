from io import BytesIO
from pathlib import Path

from pydantic import ConfigDict, RootModel

from askui.utils.markdown_utils import convert_to_markdown


class OfficeDocumentSource(RootModel):
    """Represents an Excel source that can be read as markdown.

    The class can be initialized with:
    - A file path (str or pathlib.Path)

    Attributes:
        root (bytes | Path): The underlying Excel bytes or file path.

    Args:
        root (Excel): The Excel source to load from.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    root: bytes | Path

    @property
    def reader(self) -> BytesIO:
        markdown_content = convert_to_markdown(self.root)
        return BytesIO(markdown_content.encode())


__all__ = [
    "OfficeDocumentSource",
]
