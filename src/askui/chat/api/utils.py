import base64
import os
import time


def generate_time_ordered_id(prefix: str) -> str:
    """Generate a time-ordered ID with format: prefix_timestamp_random.

    Args:
        prefix: Prefix for the ID (e.g. 'thread', 'msg')

    Returns:
        Time-ordered ID string
    """
    # Get current timestamp in milliseconds
    timestamp = int(time.time() * 1000)
    # Convert to base32 for shorter string (removing padding)
    timestamp_b32 = (
        base64.b32encode(str(timestamp).encode()).decode().rstrip("=").lower()
    )
    # Get 12 random bytes and convert to base32 (removing padding)
    random_bytes = os.urandom(12)
    random_b32 = base64.b32encode(random_bytes).decode().rstrip("=").lower()
    return f"{prefix}_{timestamp_b32}{random_b32}"
