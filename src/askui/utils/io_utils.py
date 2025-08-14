import base64
import binascii
import re
from pathlib import Path
from typing import Union

from filetype import guess  # type: ignore[import-untyped]

_DATA_URL_WITH_MIMETYPE_RE = re.compile(r"^data:([^;,]+)[^,]*?,(.*)$", re.DOTALL)


def source_file_type(source: Union[str, Path]) -> str:
    """Determines the MIME type of a source.

    The source can be a file path or a data URL.

    Args:
        source (Union[str , Path]): The source to determine the type of.
            Can be a file path (`str` or `pathlib.Path`) or a data URL.

    Returns:
        str: The MIME type of the source, or "unknown" if it cannot be determined.
    """

    # when source is a data url
    if isinstance(source, str) and source.startswith("data:"):
        match = _DATA_URL_WITH_MIMETYPE_RE.match(source)
        if match and match.group(1):
            return match.group(1)
    else:
        kind = guess(str(source))
        if kind is not None and kind.mime is not None:
            return str(kind.mime)

    return "unknown"


def read_bytes(source: Union[str, Path]) -> bytes:
    """Read the bytes of a source.

    The source can be a file path or a data URL.

    Args:
        source (Union[str, Path]): The source to read the bytes from.

    Returns:
        bytes: The content of the source as bytes.
    """
    # when source is a file path and not a data url
    if isinstance(source, Path) or (
        isinstance(source, str) and not source.startswith(("data:", ","))
    ):
        filepath = Path(source)
        if not filepath.is_file():
            err_msg = f"No such file or directory: '{source}'"
            raise ValueError(err_msg)

        return filepath.read_bytes()

    # when source is a data url
    if isinstance(source, str) and source.startswith(("data:", ",")):
        match = _DATA_URL_WITH_MIMETYPE_RE.match(source)
        if match:
            try:
                return base64.b64decode(match.group(2))
            except binascii.Error as e:
                error_msg = (
                    "Could not decode base64 data from input: "
                    f"{source[:100]}{'...' if len(source) > 100 else ''}"
                )
                raise ValueError(error_msg) from e

    msg = f"Unsupported source type: {type(source)}"
    raise ValueError(msg)


__all__ = ["read_bytes"]
