from collections.abc import MutableMapping
from typing import Any


def flatten_dict(
    d: MutableMapping[Any, Any], parent_key: str = "", sep: str = "."
) -> MutableMapping[str, Any]:
    result: list[tuple[str, Any]] = []
    for k, v in d.items():
        k = str(k)
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            result.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            result.append((new_key, v))
    return dict(result)
