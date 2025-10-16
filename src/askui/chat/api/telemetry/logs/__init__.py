import logging as logging_stdlib
import sys
from types import TracebackType

from structlog import types as structlog_types

from .settings import LogSettings
from .structlog import setup_structlog


def setup_uncaught_exception_logging(logger: logging_stdlib.Logger) -> None:
    def handle_uncaught_exception(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        """
        Log any uncaught exception instead of letting it be printed by Python
        (but leave KeyboardInterrupt untouched to allow users to Ctrl+C to stop)
        See https://stackoverflow.com/a/16993115/3641865
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.error(
            "Uncaught exception raised", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_uncaught_exception


def propagate_logs_up(loggers: list[str]) -> None:
    for logger_name in loggers:
        logger = logging_stdlib.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True


def silence_logs(loggers: list[str]) -> None:
    for logger_name in loggers:
        logger = logging_stdlib.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = False


def setup_logging(
    settings: LogSettings,
    pre_processors: list[structlog_types.Processor] | None = None,
) -> None:
    logging_stdlib.captureWarnings(True)
    root_logger = logging_stdlib.getLogger()
    setup_structlog(root_logger, settings, pre_processors)
    setup_uncaught_exception_logging(root_logger)
