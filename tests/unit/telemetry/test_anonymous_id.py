import uuid
from collections.abc import Generator

import machineid
import pytest
from pytest_mock import MockerFixture

from askui.telemetry.anonymous_id import get_anonymous_id


@pytest.fixture(autouse=True)
def reset_caches() -> Generator[None, None, None]:
    """Reset the module-level caches before each test."""
    import askui.telemetry.anonymous_id
    import askui.telemetry.device_id

    askui.telemetry.anonymous_id._anonymous_id = None
    askui.telemetry.device_id._device_id = None
    yield
    askui.telemetry.anonymous_id._anonymous_id = None
    askui.telemetry.device_id._device_id = None


def test_get_anonymous_id_returns_cached_id() -> None:
    # First call to get_anonymous_id will set the cache
    first_id = get_anonymous_id()

    # Second call should return the same ID
    second_id = get_anonymous_id()
    assert first_id == second_id


def test_get_anonymous_id_uses_device_id_when_available(mocker: MockerFixture) -> None:
    test_device_id = "test-device-id"
    expected_anonymous_id = "7c810ac9-d1be-4620-a665-95f9554920ec"

    mocker.patch(
        "askui.telemetry.anonymous_id._read_anonymous_id_from_file", return_value=None
    )
    mocker.patch("askui.telemetry.device_id.get_device_id", return_value=test_device_id)
    mocker.patch("askui.telemetry.utils.is_valid_uuid4", return_value=False)
    mocker.patch(
        "askui.telemetry.utils.hash_to_uuid4", return_value=expected_anonymous_id
    )
    mocker.patch(
        "askui.telemetry.anonymous_id.hash_to_uuid4", return_value=expected_anonymous_id
    )
    mock_write = mocker.patch(
        "askui.telemetry.anonymous_id._write_anonymous_id_to_file"
    )

    anonymous_id = get_anonymous_id()
    assert anonymous_id == expected_anonymous_id
    mock_write.assert_called_once_with(expected_anonymous_id)


def test_get_anonymous_id_uses_random_uuid_when_device_id_unavailable(
    mocker: MockerFixture,
) -> None:
    test_id = "1c9cb557-1c83-45b0-8aa8-6938c84d5893"

    mocker.patch(
        "askui.telemetry.anonymous_id._read_anonymous_id_from_file", return_value=None
    )
    mocker.patch("machineid.hashed_id", side_effect=machineid.MachineIdNotFound())
    mocker.patch("askui.telemetry.device_id.get_device_id", return_value=None)
    mocker.patch("askui.telemetry.utils.is_valid_uuid4", return_value=False)
    mocker.patch("uuid.uuid4", return_value=uuid.UUID(test_id.upper()))
    mock_write = mocker.patch(
        "askui.telemetry.anonymous_id._write_anonymous_id_to_file"
    )

    anonymous_id = get_anonymous_id()
    assert anonymous_id == test_id
    mock_write.assert_called_once_with(test_id)


def test_get_anonymous_id_reads_from_file(mocker: MockerFixture) -> None:
    test_id = "1c9cb557-1c83-45b0-8aa8-6938c84d5893"
    mocker.patch(
        "askui.telemetry.anonymous_id._read_anonymous_id_from_file",
        return_value=test_id,
    )
    mocker.patch("askui.telemetry.utils.is_valid_uuid4", return_value=True)

    anonymous_id = get_anonymous_id()
    assert anonymous_id == test_id


def test_get_anonymous_id_writes_to_file(mocker: MockerFixture) -> None:
    test_id = "1c9cb557-1c83-45b0-8aa8-6938c84d5893"

    mocker.patch(
        "askui.telemetry.anonymous_id._read_anonymous_id_from_file", return_value=None
    )
    mocker.patch("machineid.hashed_id", side_effect=machineid.MachineIdNotFound())
    mocker.patch("askui.telemetry.device_id.get_device_id", return_value=None)
    mocker.patch("askui.telemetry.utils.is_valid_uuid4", return_value=False)
    mocker.patch("uuid.uuid4", return_value=uuid.UUID(test_id.upper()))
    mock_write = mocker.patch(
        "askui.telemetry.anonymous_id._write_anonymous_id_to_file"
    )

    get_anonymous_id()
    mock_write.assert_called_once_with(test_id)
