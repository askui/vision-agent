from typing import Any


def compact(d: dict[Any, Any]) -> dict[Any, Any]:
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = compact(v)
        if not (not v and type(v) not in (bool, int, float, complex)):
            result[k] = v
    return result
