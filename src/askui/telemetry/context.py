import os
from typing import TypedDict
from typing_extensions import NotRequired

from pydantic import ConfigDict


class AppContext(TypedDict, total=False):
    """App (askui SDK/library/package) context information."""

    __pydantic_config__ = ConfigDict(extra="allow")

    name: str
    version: str


class OSContext(TypedDict, total=False):
    """OS context information."""

    __pydantic_config__ = ConfigDict(extra="allow")

    name: str
    version: str
    release: str


class PlatformContext(TypedDict, total=False):
    """Platform context information."""

    __pydantic_config__ = ConfigDict(extra="allow")

    arch: str
    python_version: str


class DeviceContext(TypedDict, total=False):
    """Device context information."""

    __pydantic_config__ = ConfigDict(extra="allow")

    id: str


class TelemetryContext(TypedDict, total=False):
    """Context information."""

    __pydantic_config__ = ConfigDict(extra="allow")

    app: AppContext
    user_id: NotRequired[str]
    anonymous_id: str
    group_id: NotRequired[str]
    os: OSContext
    platform: PlatformContext
    device: NotRequired[DeviceContext]
    session_id: str
    call_stack: list[str]


class CallStack:
    def __init__(self, max_depth: int = 100) -> None:
        self._stack: list[str] = []
        self._max_depth = max_depth

    @property
    def current(self) -> list[str]:
        return self._stack

    def push_call(self) -> str:
        """Generates call id and adds it to the call stack and returns it"""
        if len(self._stack) >= self._max_depth:
            raise ValueError("Call stack is at max depth")

        call_id = os.urandom(8).hex()
        self._stack.append(call_id)
        return call_id

    def pop_call(self) -> str:
        """Removes the last call from the call stack and returns it"""
        return self._stack.pop()
