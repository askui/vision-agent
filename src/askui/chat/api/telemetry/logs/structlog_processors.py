import logging

from structlog import DropEvent
from structlog.types import EventDict, Processor

from askui.chat.api.telemetry.logs.settings import LogFilter

from .utils import flatten_dict


def flatten_dict_processor(
    logger: logging.Logger,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: EventDict,
) -> EventDict:
    """
    Flattens a nested event dictionary deeply. Nested keys are concatenated with dot notation.
    """
    return flatten_dict(event_dict)


def drop_color_message_key_processor(
    logger: logging.Logger,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: EventDict,
) -> EventDict:
    """
    Uvicorn logs the message a second time in the extra `color_message`, but we don't
    need it. This processor drops the key from the event dict if it exists.
    """
    event_dict.pop("color_message", None)
    return event_dict


def null_processor(
    logger: logging.Logger,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: EventDict,
) -> EventDict:
    """
    A processor that does nothing.
    """
    return event_dict


def create_filter_processor(filters: list[LogFilter] | None) -> Processor:
    """
    Creates a structlog processor that filters out log lines based on field matches.

    Args:
        filters (dict[str, Any] | None): Dictionary of field names to values to filter out.
            If a log line has a field with a matching value, it will be filtered out.

    Returns:
        A structlog processor function that filters log lines.
    """
    if not filters:
        return null_processor

    def filter_processor(
        logger: logging.Logger,  # noqa: ARG001
        method_name: str,  # noqa: ARG001
        event_dict: EventDict,
    ) -> EventDict:
        """
        Filters out log lines where any field matches the filter values.
        Returns None to drop the log line, or the event_dict to keep it.
        """
        for filter_ in filters:
            if filter_.type == "equals":
                if (
                    filter_.key in event_dict
                    and event_dict[filter_.key] == filter_.value
                ):
                    raise DropEvent
        return event_dict

    return filter_processor
