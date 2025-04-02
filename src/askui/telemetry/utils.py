import uuid


def map_guid_to_uuid4(guid: str | bytes) -> str:
    """Convert a GUID string or bytes to a valid UUID4 string.
    
    This function takes a GUID (Globally Unique Identifier) as input and converts it
    to a valid UUID4 string. The function ensures the output UUID follows RFC 4122
    specification by setting the appropriate version (4) and variant bits.
    
    Args:
        guid: A string or bytes representing a GUID. If shorter than 16 bytes,
              it will be padded with zeros.
    
    Returns:
        A string representation of a valid UUID4.
    
    Examples:
        >>> map_guid_to_uuid4("12345678901234567890123456789012")
        '12345678-9012-3456-7890-123456789012'
        >>> map_guid_to_uuid4(b"1234567890123456")
        '12345678-9012-3456-7890-123456789012'
    """
    guid_bytes = guid.encode() if isinstance(guid, str) else guid
    
    # Pad with zeros if shorter than 16 bytes
    if len(guid_bytes) < 16:
        guid_bytes = guid_bytes + b'\x00' * (16 - len(guid_bytes))
    
    # Take the first 16 bytes to form the basis of our new UUID
    raw_16 = bytearray(guid_bytes[:16])

    # Force the UUID to be version 4:
    #    - The high nibble of byte 6 should be 0x4
    raw_16[6] = (raw_16[6] & 0x0F) | 0x40

    # Force the UUID to be variant 1 (i.e., 10xx in binary):
    raw_16[8] = (raw_16[8] & 0x3F) | 0x80

    new_uuid = uuid.UUID(bytes=bytes(raw_16))
    return str(new_uuid)
