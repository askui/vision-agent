import logging
import logging.handlers
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import cached_property
from multiprocessing import Process, Queue
from pathlib import Path
from time import sleep, time
from typing import Optional, TypeVar, Union
from uuid import uuid4

import mss
import mss.screenshot
import mss.tools
from mss.models import Monitor
from PIL import Image
from pydantic import AwareDatetime, validate_call

from askui.tools.pynput.change_detector import ChangeDetector, PixelMatchChangeDetector

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Type definitions for queues
LogQueue = Queue[logging.LogRecord]
CapturedFrameQueue = Queue[Union[CapturedFrame, None]]

# Create a queue handler for multiprocessing
queue_handler = logging.handlers.QueueHandler(LogQueue())
logger.addHandler(queue_handler)

# Create a stream handler for the main process
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(
    logging.Formatter("%(processName)s - %(levelname)s - %(message)s")
)
logger.addHandler(stream_handler)


def _setup_worker_logging(queue: LogQueue) -> None:
    """Set up logging for worker processes.

    Args:
        queue: The queue to send logs to
    """
    queue_listener = logging.handlers.QueueListener(queue, *logger.handlers)
    queue_listener.start()
    worker_logger = logging.getLogger()
    worker_logger.addHandler(logging.handlers.QueueHandler(queue))
    worker_logger.setLevel(logging.DEBUG)


MSSImage = mss.screenshot.ScreenShot
T = TypeVar("T")


# TODO Can we make the naming of the dataclasses more consistent?
@dataclass(frozen=True)
class CapturedFrame:
    """Represents a captured frame with its metadata.

    Attributes:
        image (MSSImage): The raw screenshot data
        capture_time (float): Unix timestamp when the frame was captured
    """

    image: MSSImage
    capture_time: float  # TODO Any good reason why this is not an `AwareDatetime` and called `timestamp` to be consistent with `Screenshot`?


@dataclass(frozen=True)
class Screenshot:
    """Represents a captured screenshot with metadata."""

    timestamp: AwareDatetime
    path: Path

    @cached_property
    def image(self) -> Image.Image:
        return Image.open(self.path)


class ScreenShooter:
    """A class for continuous screen capture with change detection and storage.

    This class provides functionality to:
    - Capture screenshots continuously from selected screen/monitor
    - Detect screen changes using configurable algorithms
    - Store screenshots efficiently on disk
    - Retrieve screenshots by timestamp with various filters
    - Manage capture lifecycle (start/stop)

    The class maintains an ordered list of screenshots and only persists changed frames
    to optimize memory usage.

    Attributes:
        _screenshots (SortedList[Screenshot]): Chronologically ordered list of screenshots
        _storage_path (Path): Directory path for screenshot storage
        _is_capturing (bool): Current capture state
        _capture_queue (CapturedFrameQueue): Queue for passing screenshots between processes
        _capture_process (Process): Process handling screen capture
        _save_process (Process): Process handling screenshot storage
        _monitor (Monitor | tuple[int, int, int, int]): Monitor configuration for capture
        _capture_interval (float | None): Minimum time between captures in seconds
        _max_screenshots (int | None): Maximum number of screenshots to keep
        _max_age (timedelta | None): Maximum age of screenshots to keep
        _change_detector (ChangeDetector): Change detector to use
    """

    def __init__(
        self,
        monitor: Monitor | tuple[int, int, int, int],
        storage_path: Optional[Path] = None,
        capture_interval: Optional[float] = None,
        max_screenshots: Optional[int] = None,
        max_age: Optional[timedelta] = None,
        change_detector: ChangeDetector | None = None,
    ) -> None:
        """Initialize the screen shooter.

        Args:
            monitor (Monitor | tuple[int, int, int, int]): Monitor to capture.
            storage_path (Path, optional): Directory to store screenshots. Defaults to temp directory.
            capture_interval (float, optional): Minimum time between captures in seconds.
            max_screenshots (int, optional): Maximum number of screenshots to keep.
            max_age (timedelta, optional): Maximum age of screenshots to keep.
            change_detector (ChangeDetector, optional): Change detector to use. Defaults to `PixelMatchChangeDetector`.
        """
        self._storage_path = storage_path or Path.cwd() / "screenshots"
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._is_capturing = False
        self._capture_queue: CapturedFrameQueue = Queue()
        self._capture_process: Optional[Process] = None
        self._save_process: Optional[Process] = None
        self._monitor = monitor
        self._capture_interval = capture_interval
        self._max_screenshots = max_screenshots
        self._max_age = max_age
        self._change_detector = change_detector or PixelMatchChangeDetector()

    def start(self) -> None:
        """Start capturing screenshots in a separate process.

        If the screen shooter is already capturing, it will not start a new capture.
        """
        if self._is_capturing:
            return

        self._is_capturing = True
        log_queue: LogQueue = Queue()

        self._capture_process = Process(
            target=self._capture_worker,
            args=(
                self._capture_queue,
                self._monitor,
                self._capture_interval,
                log_queue,
            ),
            daemon=True,
        )
        self._save_process = Process(
            target=self._save_worker,
            args=(
                self._capture_queue,
                self._storage_path,
                self._change_detector,
                log_queue,
            ),
            daemon=True,
        )
        self._cleanup_process = None
        if self._max_screenshots is not None or self._max_age is not None:
            self._cleanup_process = Process(
                target=self._cleanup_worker,
                args=(
                    self._storage_path,
                    self._max_screenshots,
                    self._max_age,
                    self._capture_interval,
                    log_queue,
                ),
                daemon=True,
            )
        self._capture_process.start()
        self._save_process.start()
        if self._cleanup_process:
            self._cleanup_process.start()

    @staticmethod
    def _cleanup_worker(
        storage_path: Path,
        max_screenshots: int | None,
        max_age: timedelta | None,
        capture_interval: float | None,
        log_queue: LogQueue | None = None,
    ) -> None:
        """Worker process that cleans up old screenshots.

        Args:
            storage_path (Path): Directory to clean up.
            max_screenshots (int | None): Maximum number of screenshots to keep.
            max_age (timedelta | None): Maximum age of screenshots to keep.
            capture_interval (float | None): Minimum time between captures in seconds.
            log_queue (LogQueue | None): Queue to send logs to.
        """
        if log_queue:
            _setup_worker_logging(log_queue)

    @staticmethod
    def _capture_worker(
        queue: CapturedFrameQueue,
        monitor: Monitor | tuple[int, int, int, int],
        capture_interval: float | None = None,
        log_queue: LogQueue | None = None,
    ) -> None:
        """Worker process that captures screenshots.

        Args:
            queue (CapturedFrameQueue): Queue to put captured frames in.
            monitor (Monitor | tuple[int, int, int, int]): Monitor configuration for capture.
            capture_interval (float | None): Minimum time between captures in seconds.
            log_queue (LogQueue | None): Queue to send logs to.
        """
        if log_queue:
            _setup_worker_logging(log_queue)

        try:
            with mss.mss() as sct:
                _capture_interval = capture_interval or 0.0
                buffer_in_s = 0.001
                sleep_time = max(0, _capture_interval - buffer_in_s)
                last_capture = time()
                while True:
                    if sleep_time > 0:
                        sleep(sleep_time)
                        current_time = time()
                        if current_time - last_capture < _capture_interval:
                            continue

                    screenshot = sct.grab(monitor)
                    last_capture = time()
                    queue.put(
                        CapturedFrame(image=screenshot, capture_time=last_capture)
                    )
                    logger.debug("Captured screenshot")
        except Exception as e:  # noqa: BLE001
            logger.error("Error capturing screenshot: %s", e)
            queue.put(None)

    @staticmethod
    def _save_worker(
        queue: CapturedFrameQueue,
        storage_path: Path,
        change_detector: ChangeDetector,
        log_queue: LogQueue | None = None,
    ) -> None:
        """Worker process that saves screenshots and detects changes.

        Args:
            queue (CapturedFrameQueue): Queue to get captured frames from.
            storage_path (Path): Directory to save screenshots.
            change_detector (ChangeDetector): Change detector to use.
            log_queue (LogQueue | None): Queue to send logs to.
        """
        if log_queue:
            _setup_worker_logging(log_queue)

        while True:
            frame = queue.get()
            if frame is None:
                break

            pil_img = Image.frombytes("RGB", frame.image.size, frame.image.rgb)  # type: ignore[attr-defined]
            if not change_detector.detect_change(pil_img):
                continue

            timestamp = datetime.fromtimestamp(frame.capture_time, tz=timezone.utc)
            filepath = (
                storage_path
                / f"screenshot_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}_{uuid4().hex[:8]}.png"
            )
            pil_img.save(filepath, format="PNG")
            logger.debug("Saved screenshot %s", str(filepath))

    def stop(self) -> bool:
        """Stop capturing screenshots and cleanup processes.

        If the screen shooter is not capturing, it will not stop.

        Returns:
            `True` if the screen shooter was stopped, `False` otherwise.
        """
        if not self._is_capturing:
            return False

        self._is_capturing = False
        self._capture_queue.put(None)  # Signal save process to stop

        if self._capture_process:
            self._capture_process.join(timeout=1)
        if self._save_process:
            self._save_process.join(timeout=1)
        if self._cleanup_process:
            self._cleanup_process.join(timeout=1)

        logger.debug("Stopped screen capture and save processes")
        return True

    @validate_call
    def get_screenshots(
        self,
        le: AwareDatetime | None = None,
        lt: AwareDatetime | None = None,
        gt: AwareDatetime | None = None,
        ge: AwareDatetime | None = None,
        limit: int | None = None,
    ) -> list[Screenshot]:
        """Get screenshots filtered by timestamp comparison operators.

        Args:
            le (AwareDatetime | None, optional): Less than or equal to timestamp.
            lt (AwareDatetime | None, optional): Less than timestamp.
            gt (AwareDatetime | None, optional): Greater than timestamp.
            ge (AwareDatetime | None, optional): Greater than or equal to timestamp.
            limit (int | None, optional): Maximum number of screenshots to return. Returns
                all by default. It returns the most recent screenshots matching the filters.

        Returns:
            List of screenshots ordered chronologically that match the filters.
            If no filters are provided, returns all screenshots.

        Raises:
            ValueError: If any datetime argument is not timezone-aware.
        """
        # Convert all timestamps to UTC for consistent comparison
        timestamps = {
            "le": le.astimezone(timezone.utc) if le is not None else None,
            "lt": lt.astimezone(timezone.utc) if lt is not None else None,
            "gt": gt.astimezone(timezone.utc) if gt is not None else None,
            "ge": ge.astimezone(timezone.utc) if ge is not None else None,
        }

        # TODO CAN: Optimise parsing and saving
        # TODO CAN: Caching/faster?
        # Get all screenshot files and parse their timestamps
        screenshots: list[Screenshot] = []
        for file_path in sorted(self._storage_path.glob("screenshot_*.png")):
            try:
                # Parse timestamp from filename: screenshot_YYYYMMDD_HHMMSS_ffffff_uuid.png
                timestamp_str = file_path.stem.split("_")[
                    1:3
                ]  # Get YYYYMMDD and HHMMSS parts
                timestamp = datetime.strptime(
                    f"{timestamp_str[0]}_{timestamp_str[1]}", "%Y%m%d_%H%M%S"
                ).replace(tzinfo=timezone.utc)

                # Apply filters
                if timestamps["gt"] is not None and timestamp <= timestamps["gt"]:
                    continue
                if timestamps["ge"] is not None and timestamp < timestamps["ge"]:
                    continue
                if timestamps["lt"] is not None and timestamp >= timestamps["lt"]:
                    continue
                if timestamps["le"] is not None and timestamp > timestamps["le"]:
                    continue

                screenshots.append(Screenshot(timestamp=timestamp, path=file_path))
            except (ValueError, IndexError) as e:
                logger.warning(
                    "Failed to parse screenshot filename %s: %s", file_path.name, e
                )
                continue

        if limit is not None:
            screenshots = screenshots[-limit:]

        return screenshots


if __name__ == "__main__":
    screen_shooter = ScreenShooter(monitor=mss.mss().monitors[1])
    screen_shooter.start()
    sleep(15)
    screen_shooter.stop()
