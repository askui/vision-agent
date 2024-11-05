import logging
from rich.logging import RichHandler


logger = logging.getLogger("askui")
if not logger.hasHandlers():
    handler = RichHandler(rich_tracebacks=True, show_level=True, show_time=True, show_path=True)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def configure_logging(level=logging.INFO):
    logger.setLevel(level)
