from collections import defaultdict
from typing import Any, TypeVar

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class IdentityDefaultDict(defaultdict[_KT, _VT]):
    """
    A `defaultdict` variant that returns the key itself if the key is not found.

    Args:
        d (dict[_KT, _VT] | None, optional): Initial dictionary to populate the mapping.
            If `None`, an empty dict is used.

    Example:
        ```python
        d = IdentityDefaultDict({'a': 1})
        print(d['a'])  # 1
        print(d['b'])  # 'b'
        ```

    Returns:
        IdentityDefaultDict: An instance of the mapping.

    Notes:
        This is useful for mapping lookups where missing keys should fall back to the
        key itself (e.g., identity mapping).
    """

    def __init__(self, d: dict[_KT, _VT] | None = None) -> None:
        _d = d or {}
        super().__init__(None, _d)

    def __missing__(self, key: Any) -> Any:
        return key
