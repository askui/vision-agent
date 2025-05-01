import machineid

from askui.logger import logger

_HASH_KEY = "askui"

_device_id: str | None = None


def get_device_id() -> str | None:
    """Get the device ID (hashed) of the host device

    Returns None if the device ID is not found.
    """
    global _device_id
    if _device_id is None:
        try:
            _device_id = machineid.hashed_id(app_id=_HASH_KEY)
        except machineid.MachineIdNotFound:
            logger.debug("Device ID not found")
            return None
    return _device_id
