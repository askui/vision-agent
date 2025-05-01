import uuid

from askui.telemetry.utils import hash_to_uuid4, is_valid_uuid4


def test_is_valid_uuid4() -> None:
    # Valid UUID4
    assert is_valid_uuid4(str(uuid.uuid4()))
    assert is_valid_uuid4("123e4567-e89b-4456-a456-426614174000")  # Version 4 UUID
    assert is_valid_uuid4("123E4567-E89B-4456-A456-426614174000")  # Case doesn't matter

    # Invalid UUID4
    assert not is_valid_uuid4("not-a-uuid")
    assert not is_valid_uuid4("12345678-1234-5678-1234-56781234567")  # Too short
    assert not is_valid_uuid4("12345678-1234-5678-1234-5678123456789")  # Too long
    assert not is_valid_uuid4("123e4567-e89b-1234-a456-426614174000")  # Wrong version


def test_hash_to_uuid4_string_input() -> None:
    guid = "12345678901234567890123456789012"
    result = hash_to_uuid4(guid)

    # Verify it's a valid UUID
    uuid_obj = uuid.UUID(result)
    assert uuid_obj.version == 4
    assert uuid_obj.variant == uuid.RFC_4122


def test_hash_to_uuid4_bytes_input() -> None:
    guid = b"12345678901234567890123456789012"
    result = hash_to_uuid4(guid.decode())  # Convert bytes to str

    # Verify it's a valid UUID
    uuid_obj = uuid.UUID(result)
    assert uuid_obj.version == 4
    assert uuid_obj.variant == uuid.RFC_4122


def test_hash_to_uuid4_short_input() -> None:
    guid = "1234567890"
    result = hash_to_uuid4(guid)

    # Should still work with shorter input
    uuid_obj = uuid.UUID(result)
    assert uuid_obj.version == 4
    assert uuid_obj.variant == uuid.RFC_4122


def test_hash_to_uuid4_deterministic() -> None:
    guid = "12345678901234567890123456789012"
    result1 = hash_to_uuid4(guid)
    result2 = hash_to_uuid4(guid)

    # Same input should produce same output
    assert result1 == result2


def test_hash_to_uuid4_different_inputs() -> None:
    guid1 = "12345678901234567890123456789012"
    guid2 = "98765432109876543210987654321098"
    result1 = hash_to_uuid4(guid1)
    result2 = hash_to_uuid4(guid2)

    # Different inputs should produce different outputs
    assert result1 != result2
