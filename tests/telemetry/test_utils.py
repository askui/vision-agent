import uuid
from askui.telemetry.utils import map_guid_to_uuid4


def test_map_guid_to_uuid4_string_input():
    guid = "12345678901234567890123456789012"
    result = map_guid_to_uuid4(guid)

    # Verify it's a valid UUID
    uuid_obj = uuid.UUID(result)
    assert uuid_obj.version == 4
    assert uuid_obj.variant == uuid.RFC_4122


def test_map_guid_to_uuid4_bytes_input():
    guid = b"12345678901234567890123456789012"
    result = map_guid_to_uuid4(guid)

    # Verify it's a valid UUID
    uuid_obj = uuid.UUID(result)
    assert uuid_obj.version == 4
    assert uuid_obj.variant == uuid.RFC_4122


def test_map_guid_to_uuid4_short_input():
    guid = "1234567890"
    result = map_guid_to_uuid4(guid)

    # Should still work with shorter input
    uuid_obj = uuid.UUID(result)
    assert uuid_obj.version == 4
    assert uuid_obj.variant == uuid.RFC_4122


def test_map_guid_to_uuid4_deterministic():
    guid = "12345678901234567890123456789012"
    result1 = map_guid_to_uuid4(guid)
    result2 = map_guid_to_uuid4(guid)

    # Same input should produce same output
    assert result1 == result2


def test_map_guid_to_uuid4_different_inputs():
    guid1 = "12345678901234567890123456789012"
    guid2 = "98765432109876543210987654321098"
    result1 = map_guid_to_uuid4(guid1)
    result2 = map_guid_to_uuid4(guid2)

    # Different inputs should produce different outputs
    assert result1 != result2
