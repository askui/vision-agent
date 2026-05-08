import logging
import pathlib
import subprocess
import sys
import time
import uuid
from urllib.parse import urlparse

from typing_extensions import override

from askui.models.shared.tool_tags import ToolTags
from askui.tools.askui.askui_controller_settings import AskUiControllerSettings
from askui.tools.utils import process_exists, wait_for_port

logger = logging.getLogger(__name__)


_DEFAULT_LOCAL_ADDRESS = "localhost:23000"
_ASKUI_CORE_SERVICE_NAME = "askuicoreservice"
_ASKUI_CORE_SERVICE_PORT = 26000


def _generate_session_guid() -> str:
    return "{" + str(uuid.uuid4()) + "}"


def _is_askui_core_service_running() -> bool:
    """Return `True` when the `askuicoreservice` Windows service is RUNNING."""
    if sys.platform != "win32":
        return False
    try:
        result = subprocess.run(
            ["sc", "query", _ASKUI_CORE_SERVICE_NAME],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        logger.debug("Failed to query %s service", _ASKUI_CORE_SERVICE_NAME)
        return False
    if result.returncode != 0:
        return False
    return "RUNNING" in result.stdout.upper()


def _replace_port(address: str, port: int) -> str:
    addr = address if "://" in address else "//" + address
    parsed = urlparse(addr)
    host = parsed.hostname or "localhost"
    return f"{host}:{port}"


class TargetComputer:
    """
    Base class describing a target computer (i.e. an AskUI Remote Device Controller
    server) that the `AskUiControllerClient` can connect to.

    Each target has a unique session GUID, a gRPC address, plus optional `tags` and
    `description` for categorization.

    Args:
        address (str): gRPC address of the controller server
            (e.g. ``"localhost:23000"``).
        tags (list[str] | None, optional): Tags for categorizing the target.
        description (str | None, optional): Human-readable description.
    """

    def __init__(
        self,
        address: str,
        description: str,
        tags: list[str] | None = None,
    ) -> None:
        self._session_guid = _generate_session_guid()
        self._address = address
        self._tags = tags or []
        self._description = description

    @property
    def session_guid(self) -> str:
        """Unique session GUID assigned to this target computer."""
        return self._session_guid

    @property
    def address(self) -> str:
        """gRPC address of the target computer."""
        return self._address

    @property
    def tags(self) -> list[str]:
        """Tags assigned to this target computer."""
        return list(self._tags)

    @property
    def description(self) -> str:
        """Description of this target computer."""
        return self._description

    @property
    def is_local(self) -> bool:
        """Whether this target represents a locally-managed controller process."""
        return False

    def start(self, clean_up: bool = False) -> None:
        """Start the underlying controller process. No-op for non-local targets."""

    def stop(self, force: bool = False) -> None:
        """Stop the underlying controller process. No-op for non-local targets."""

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"session_guid={self._session_guid!r}, "
            f"address={self._address!r}, "
            f"tags={self._tags!r}, "
            f"description={self._description!r})"
        )


class LocalTargetComputer(TargetComputer):
    """
    Local target computer: manages an AskUI Remote Device Controller subprocess on
    this machine.

    Args:
        settings (AskUiControllerSettings | None, optional): Process-level settings
            (executable path, args). Defaults to a fresh `AskUiControllerSettings`.
        address (str, optional): gRPC address. Defaults to ``"localhost:23000"``.
        autostart (bool, optional): Whether `start()` actually launches the process.
            Defaults to `True`.
        discover_service (bool, optional): On Windows, probe for a running
            ``askuicoreservice`` and, if found, switch the address to port
            ``26000`` and disable autostart. Defaults to `True`.
        tags (list[str] | None, optional)
        description (str | None, optional)
    """

    def __init__(
        self,
        description: str = "Local target computer",
        settings: AskUiControllerSettings | None = None,
        address: str = "localhost:23000",
        autostart: bool = True,
        discover_service: bool = True,
        tags: list[str] | None = None,
    ) -> None:
        if discover_service and _is_askui_core_service_running():
            logger.info(
                "Detected running %s; using port %s and disabling autostart",
                _ASKUI_CORE_SERVICE_NAME,
                _ASKUI_CORE_SERVICE_PORT,
            )
            address = _replace_port(address, _ASKUI_CORE_SERVICE_PORT)
            autostart = False
        tags = tags or []
        tags.append(ToolTags.LOCAL.value)
        super().__init__(address=address, tags=tags, description=description)
        self._autostart = autostart
        self._settings = settings or AskUiControllerSettings()
        self._process: subprocess.Popen[bytes] | None = None

    @property
    @override
    def is_local(self) -> bool:
        return True

    @property
    def autostart(self) -> bool:
        """Whether `start()` launches the controller process."""
        return self._autostart

    def _parse_port(self) -> int:
        addr = self._address if "://" in self._address else "//" + self._address
        parsed = urlparse(addr)
        if parsed.port is None:
            error_msg = f"Could not parse port from address: {self._address}"
            raise ValueError(error_msg)
        return parsed.port

    def _start_process(
        self,
        path: pathlib.Path,
        args: str | None = None,
    ) -> None:
        commands = [str(path)]
        if args:
            commands.extend(args.split())
        if not logger.isEnabledFor(logging.DEBUG):
            self._process = subprocess.Popen(
                commands, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        else:
            self._process = subprocess.Popen(commands)
        wait_for_port(self._parse_port())

    @override
    def start(self, clean_up: bool = False) -> None:
        """
        Start the controller process if `autostart` is enabled.

        Args:
            clean_up (bool, optional): Whether to clean up existing processes
                (only on Windows) before starting. Defaults to `False`.
        """
        if not self._autostart:
            logger.debug(
                "Skipping local controller start because autostart is disabled"
            )
            return
        if (
            sys.platform == "win32"
            and clean_up
            and process_exists("AskuiRemoteDeviceController.exe")
        ):
            self.clean_up()
        logger.debug(
            "Starting AskUI Remote Device Controller",
            extra={"path": str(self._settings.controller_path)},
        )
        self._start_process(
            self._settings.controller_path, self._settings.controller_args
        )
        time.sleep(0.5)

    def clean_up(self) -> None:
        subprocess.run("taskkill.exe /IM AskUI*")
        time.sleep(0.1)

    @override
    def stop(self, force: bool = False) -> None:
        """
        Stop the controller process.

        Args:
            force (bool, optional): Whether to forcefully terminate the process.
                Defaults to `False`.
        """
        if self._process is None:
            return

        try:
            if force:
                self._process.kill()
                if sys.platform == "win32":
                    self.clean_up()
            else:
                self._process.terminate()
        except Exception:  # noqa: BLE001 - We want to catch all other exceptions here
            logger.exception("Controller error")
        finally:
            self._process = None


class RemoteTargetComputer(TargetComputer):
    """
    Remote target computer: the client connects to an already-running controller on
    another machine.

    No process management is performed; `start()` and `stop()` are no-ops.

    Args:
        address (str): gRPC address of the remote controller (required).
        tags (list[str] | None, optional)
        description (str | None, optional)
    """

    def __init__(
        self,
        address: str,
        description: str,
        tags: list[str] | None = None,
    ) -> None:
        tags = tags or []
        tags.append(ToolTags.REMOTE.value)
        super().__init__(address=address, tags=tags, description=description)


__all__ = [
    "LocalTargetComputer",
    "RemoteTargetComputer",
    "TargetComputer",
]
