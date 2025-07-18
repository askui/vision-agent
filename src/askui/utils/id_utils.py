import base64
import os
import time
from typing import Any

from pydantic import Field


def generate_time_ordered_id(prefix: str) -> str:
    """Generate a time-ordered ID with format: prefix_timestamp_random.

    Args:
        prefix (str): Prefix for the ID (e.g. 'thread', 'msg')

    Returns:
        str: Time-ordered ID string
    """
    timestamp = int(time.time() * 1000)
    timestamp_b32 = (
        base64.b32encode(str(timestamp).encode()).decode().rstrip("=").lower()
    )
    random_bytes = os.urandom(12)
    random_b32 = base64.b32encode(random_bytes).decode().rstrip("=").lower()
    return f"{prefix}_{timestamp_b32}{random_b32}"


def IdField(prefix: str) -> Any:
    return Field(
        pattern=rf"^{prefix}_[a-z0-9]+$",
    )
