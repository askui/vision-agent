import logging
from pathlib import Path

from rich.logging import RichHandler

logger = logging.getLogger("askui")
if not logger.hasHandlers():
    handler = RichHandler(
        rich_tracebacks=True, show_level=True, show_time=True, show_path=True
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def configure_logging(level: str | int = logging.INFO) -> None:
    logger.setLevel(level)


def add_file_log(path: str = "./") -> None:
    file_handler = logging.FileHandler(Path(path, "vision_agent.log"))
    file_formatter = logging.Formatter("%(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
