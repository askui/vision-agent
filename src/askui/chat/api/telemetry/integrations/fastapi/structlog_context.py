from copy import deepcopy
from typing import Any

from starlette_context import context

STRUCTLOG_REQUEST_CONTEXT_KEY = "structlog_context"


def is_available() -> bool:
    return context.exists()


def get() -> dict[str, Any]:
    return deepcopy(context.get(STRUCTLOG_REQUEST_CONTEXT_KEY, {}))


def bind(**kw: Any) -> None:
    new_context = get()
    new_context.update(kw)
    context[STRUCTLOG_REQUEST_CONTEXT_KEY] = new_context


def reset() -> None:
    context[STRUCTLOG_REQUEST_CONTEXT_KEY] = {}
