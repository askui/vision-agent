import time
from typing import Optional, TypedDict


class AccessLogLine(TypedDict):
    level: int
    event: str
    method: str
    path: str
    query: Optional[str]
    status: int
    http_version: str
    ip: Optional[str]
    port: Optional[int]


class TimeSpanData(TypedDict, total=False):
    started_at: int
    ended_at: Optional[int]


class TimeSpan:
    def __init__(self) -> None:
        self.started_at: int = time.perf_counter_ns()
        self.ended_at: Optional[int] = None

    def end(self) -> None:
        self.ended_at = time.perf_counter_ns()

    @property
    def in_ns(self) -> Optional[int]:
        if self.ended_at is None:
            return None

        return self.ended_at - self.started_at

    @property
    def in_ms(self) -> Optional[float]:
        return self.in_ns / 10**6 if self.in_ns is not None else None

    @property
    def in_s(self) -> Optional[float]:
        return self.in_ns / 10**9 if self.in_ns is not None else None
