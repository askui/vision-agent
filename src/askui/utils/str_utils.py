from typing import Any, TypeVar, overload

T = TypeVar("T", dict[str, Any], list[Any], str)


@overload
def truncate_long_strings(
    json_data: dict[str, Any],
    max_length: int = 100,
    truncate_length: int = 20,
    tag: str = "[shortened]",
) -> dict[str, Any]: ...


@overload
def truncate_long_strings(
    json_data: list[Any],
    max_length: int = 100,
    truncate_length: int = 20,
    tag: str = "[shortened]",
) -> list[Any]: ...


@overload
def truncate_long_strings(
    json_data: str,
    max_length: int = 100,
    truncate_length: int = 20,
    tag: str = "[shortened]",
) -> str: ...


def truncate_long_strings(
    json_data: T,
    max_length: int = 100,
    truncate_length: int = 20,
    tag: str = "[shortened]",
) -> T:
    """
    Traverse and truncate long strings in JSON data.

    Args:
        json_data: The JSON data to process. Can be a dict, list, or str.
        max_length: Maximum length of a string before truncation occurs.
        truncate_length: Number of characters to keep when truncating.
        tag: Tag to append to truncated strings.

    Returns:
        Processed JSON data with truncated long strings. Returns the same type as input.

    Examples:
        >>> truncate_long_strings({"key": "a" * 101})
        {'key': 'aaaaaaaaaaaaaaaaaaaa... [shortened]'}

        >>> truncate_long_strings(["short", "a" * 101])
        ['short', 'aaaaaaaaaaaaaaaaaaaa... [shortened]']

        >>> truncate_long_strings("a" * 101)
        'aaaaaaaaaaaaaaaaaaaa... [shortened]'
    """
    if isinstance(json_data, dict):
        return {
            k: truncate_long_strings(v, max_length, truncate_length, tag)
            for k, v in json_data.items()
        }
    if isinstance(json_data, list):
        return [
            truncate_long_strings(item, max_length, truncate_length, tag)
            for item in json_data
        ]
    if isinstance(json_data, str) and len(json_data) > max_length:
        return f"{json_data[:truncate_length]}... {tag}"
    return json_data
