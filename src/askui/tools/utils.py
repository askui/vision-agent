import socket
import subprocess
import sys
import time


def wait_for_port(port: int, host: str = "localhost", timeout: float = 5.0) -> None:
    """Wait until a port starts accepting TCP connections.
    Args:
        port: Port number.
        host: Host address on which the port should exist.
        timeout: In seconds. How long to wait before raising errors.
    Raises:
        TimeoutError: The port isn't accepting connection after time specified in
            `timeout`.
    """
    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                break
        except OSError as ex:
            time.sleep(0.01)
            if time.perf_counter() - start_time >= timeout:
                error_msg = (
                    "Waited too long for the port {} on host {} to start accepting "
                    "connections.".format(port, host)
                )
                raise TimeoutError(error_msg) from ex


def process_exists(process_name: str) -> bool:
    call = "TASKLIST", "/FI", "imagename eq %s" % process_name
    # use buildin check_output right away
    output = subprocess.check_output(call).decode("utf-16-le", errors="ignore")
    # check in last line for process name
    last_line = output.strip().split("\r\n")[-1]
    # because Fail message could be translated
    return last_line.lower().startswith(process_name.lower())


def wait_with_progress(
    wait_duration: float,
    message: str = "Waiting",
    refresh_interval: float = 0.2,
    progress_bar_width: int = 30,
) -> None:
    start = time.monotonic()
    while True:
        elapsed_time = time.monotonic() - start
        progress = min(1.0, elapsed_time / wait_duration)
        filled = int(progress_bar_width * progress)
        bar = (
            "=" * filled
            + (">" if filled < progress_bar_width else "")
            + " " * max(0, progress_bar_width - filled - 1)
        )
        pct = int(progress * 100)
        line = (
            f"\r  {message}: [{bar}] {pct}% ({elapsed_time:.1f}s"
            f" / {wait_duration:.1f}s)"
        )
        sys.stdout.write(line)
        sys.stdout.flush()
        if elapsed_time >= wait_duration:
            break
        sleep_for = min(
            refresh_interval,
            wait_duration - elapsed_time,
        )
        if sleep_for > 0:
            time.sleep(sleep_for)
    sys.stdout.write("\n")
    sys.stdout.flush()
