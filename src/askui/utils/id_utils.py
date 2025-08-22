from typing import Any

import bson
from pydantic import Field


def generate_time_ordered_id(prefix: str) -> str:
    """Generate a time-ordered ID with format: prefix_timestamp_random.

    Args:
        prefix (str): Prefix for the ID (e.g. 'thread', 'msg')

    Returns:
        str: Time-ordered ID string
    """

    return f"{prefix}_{str(bson.ObjectId())}"


def IdField(prefix: str) -> Any:
    return Field(
        pattern=rf"^{prefix}_[a-z0-9]+$",
    )
