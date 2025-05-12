import uuid
from pathlib import Path

from askui.logger import logger
from askui.telemetry.device_id import get_device_id
from askui.telemetry.utils import hash_to_uuid4, is_valid_uuid4

_ANONYMOUS_ID_FILE_PATH = Path.home() / ".askui" / "ADK" / "anonymous_id"
_anonymous_id: str | None = None


def _read_anonymous_id_from_file() -> str | None:
    """Read anonymous ID from file if it exists."""
    try:
        if _ANONYMOUS_ID_FILE_PATH.exists():
            return _ANONYMOUS_ID_FILE_PATH.read_text().strip()
    except OSError as e:
        logger.warning(f"Failed to read anonymous ID from file: {str(e)}")
    return None


def _write_anonymous_id_to_file(anonymous_id: str) -> bool:
    """Write anonymous ID to file, creating directories if needed."""
    try:
        _ANONYMOUS_ID_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _ANONYMOUS_ID_FILE_PATH.write_text(anonymous_id)
    except OSError as e:
        logger.warning(f"Failed to write anonymous ID to file: {str(e)}")
    else:
        return True
    return False


def get_anonymous_id() -> str:
    """Get an anonymous (user) ID for telemetry purposes.

    Returns:
        str: A UUID v4 string in lowercase format.

    The function follows this process:
    1. Returns cached ID if available in memory
    2. Attempts to read ID from disk (`~/.askui/ADK/anonymous_id`) if not in memory
    3. If ID doesn't exist or is invalid, generates a new one:
       - Derived from device ID if available
       - Random UUID if device ID unavailable
    4. Writes new ID to disk for persistence and returns it
    5. If writing to disk fails, just returns the new ID for each run
    - Only going to be same across runs if it can be derived from the device ID,
      otherwise it's random
    """
    global _anonymous_id
    if _anonymous_id is None:
        aid = _read_anonymous_id_from_file()
        if aid is None or not is_valid_uuid4(aid):
            machine_id = get_device_id()
            if machine_id:
                aid = hash_to_uuid4(machine_id).lower()
            else:
                aid = str(uuid.uuid4()).lower()
            _write_anonymous_id_to_file(aid)
        _anonymous_id = aid
    return _anonymous_id
