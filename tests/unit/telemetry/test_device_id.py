import machineid
from pytest_mock import MockerFixture

from askui.telemetry.device_id import get_device_id


def test_get_device_id_returns_cached_id(mocker: MockerFixture) -> None:
    # First call to get_device_id will set the cache
    mocker.patch("askui.telemetry.device_id._device_id", None)
    mocker.patch(
        "machineid.hashed_id",
        return_value="02c2431a4608f230d2d759ac888d773d274229ebd9c9093249752dd839ee3ea3",
    )
    first_id = get_device_id()

    # Second call should return the same ID
    second_id = get_device_id()
    assert first_id == second_id


def test_get_device_id_returns_hashed_id(mocker: MockerFixture) -> None:
    test_id = "02c2431a4608f230d2d759ac888d773d274229ebd9c9093249752dd839ee3ea3"
    mocker.patch("askui.telemetry.device_id._device_id", None)
    mocker.patch("machineid.hashed_id", return_value=test_id)
    device_id = get_device_id()
    assert device_id == test_id


def test_get_device_id_returns_none_on_error(mocker: MockerFixture) -> None:
    mocker.patch("askui.telemetry.device_id._device_id", None)
    mocker.patch("machineid.hashed_id", side_effect=machineid.MachineIdNotFound)
    device_id = get_device_id()
    assert device_id is None
