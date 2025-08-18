from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from markitdown import MarkItDown

_MARKDOWN_CONVERTER = MarkItDown()


def convert_to_markdown(source: Path | bytes | BinaryIO) -> str:
    """Converts a source to markdown text.

    Args:
        source (Path | bytes | BinaryIO): The source to convert.

    Returns:
        str: The markdown representation of the source.
    """
    if isinstance(source, bytes):
        bytes_source = BytesIO(source)
        result = _MARKDOWN_CONVERTER.convert(bytes_source)
        return result.text_content
    result = _MARKDOWN_CONVERTER.convert(source)
    return result.text_content
