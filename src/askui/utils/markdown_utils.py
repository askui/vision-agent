from io import BytesIO
from pathlib import Path
from typing import BinaryIO


def convert_to_markdown(source: Path | bytes | BinaryIO) -> str:
    """Converts a source to markdown text.

    Args:
        source (Path | bytes | BinaryIO): The source to convert.

    Returns:
        str: The markdown representation of the source.
    """
    try:
        from markitdown import MarkItDown
    except ImportError:
        error_msg = (
            "Office document support is not available."
            " Please install it with `pip install askui[office-document]`."
        )
        raise ImportError(error_msg)  # noqa: B904
    markdown_converter = MarkItDown()
    if isinstance(source, bytes):
        bytes_source = BytesIO(source)
        result = markdown_converter.convert(bytes_source)
        return result.text_content
    result = markdown_converter.convert(source)
    return result.text_content
