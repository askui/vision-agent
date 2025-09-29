import logging

import structlog

from .settings import LogFormat, LogLevel, LogSettings
from .structlog_processors import (
    drop_color_message_key_processor,
    flatten_dict_processor,
)


def setup_structlog(
    root_logger: logging.Logger,
    settings: LogSettings,
    pre_processors: list[structlog.types.Processor] | None = None,
) -> None:
    shared_processors = (pre_processors or []) + get_shared_processors(settings)
    structlog.configure(
        processors=shared_processors
        + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            get_renderer(settings.format),
        ],
    )
    configure_stdlib_logger(root_logger, settings.level, formatter)


def configure_stdlib_logger(
    logger: logging.Logger, log_level: LogLevel, formatter: logging.Formatter
) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(log_level.value)


EVENT_KEY = "message"


def get_shared_processors(settings: LogSettings) -> list[structlog.types.Processor]:
    """Returns a list of processors, i.e., a processor chain, that can be shared between
    structlog and stdlib loggers so that their content is consistent."""
    format_dependent_processors = get_format_dependent_processors(settings.format)
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ExtraAdder(),
        drop_color_message_key_processor,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        *format_dependent_processors,
        structlog.processors.EventRenamer(EVENT_KEY),
    ]


def get_format_dependent_processors(
    log_format: LogFormat,
) -> list[structlog.types.Processor]:
    if log_format == LogFormat.JSON:
        return [structlog.processors.format_exc_info]
    return [
        structlog.dev.set_exc_info,
        flatten_dict_processor,
    ]


def get_renderer(log_format: LogFormat) -> structlog.types.Processor:
    if log_format == LogFormat.JSON:
        return structlog.processors.JSONRenderer()
    return structlog.dev.ConsoleRenderer(event_key=EVENT_KEY)
