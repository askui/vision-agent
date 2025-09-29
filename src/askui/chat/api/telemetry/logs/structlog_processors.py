import logging

from structlog.types import EventDict

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
