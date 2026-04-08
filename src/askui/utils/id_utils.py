import time
import uuid
from typing import Any

from pydantic import Field


def generate_time_ordered_id(prefix: str) -> str:
    """Generate a time-ordered ID with format: prefix_timestamp_random.

    Args:
        prefix (str): Prefix for the ID (e.g. 'thread', 'msg')

    Returns:
        str: Time-ordered ID string
    """

    timestamp_hex = f"{time.time_ns():x}"
    random_hex = uuid.uuid4().hex[:12]
    return f"{prefix}_{timestamp_hex}{random_hex}"


def IdField(prefix: str) -> Any:
    return Field(
        pattern=rf"^{prefix}_[a-z0-9]+$",
    )
