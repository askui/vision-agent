import hashlib
import uuid


def is_valid_uuid4(uuid_str: str) -> bool:
    """Check if string is a valid UUID4."""
    try:
        return str(uuid.UUID(uuid_str, version=4)).lower() == uuid_str.lower()
    except (ValueError, AttributeError):
        return False


def hash_to_uuid4(value: str) -> str:
    """Hash a string to a valid UUID4 string.

    The hashing is deterministic and collision resistant, meaning that it is highly
    unlikely that two different inputs produce the same output.

    Args:
        value: A string.

    Returns:
        A string representation of a valid UUID4.
    """
    b = value.encode()
    digest = hashlib.sha256(b).digest()

    # Take the first 16 bytes to form the basis of our new UUID
    raw_16 = bytearray(digest[:16])

    # Force the UUID to be version 4:
    #    - The high nibble of byte 6 should be 0x4
    raw_16[6] = (raw_16[6] & 0x0F) | 0x40

    # Force the UUID to be variant 1 (i.e., 10xx in binary):
    raw_16[8] = (raw_16[8] & 0x3F) | 0x80
    new_uuid = uuid.UUID(bytes=bytes(raw_16))
    return str(new_uuid)
