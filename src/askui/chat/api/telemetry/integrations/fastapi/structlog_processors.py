import logging

from structlog.types import EventDict

from . import structlog_context


def merge_starlette_contextvars(
    logger: logging.Logger,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: EventDict,
) -> EventDict:
    """
    Merges the starlette contextvars into the structlog contextvars.
    """

    if structlog_context.is_available():
        return {
            **event_dict,
            **structlog_context.get(),
        }
    return event_dict
