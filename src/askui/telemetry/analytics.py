from typing import TypedDict
from typing_extensions import NotRequired

from pydantic import ConfigDict


class AppContext(TypedDict, total=False):
    """App context information for analytics events."""

    __pydantic_config__ = ConfigDict(extra="allow")

    name: str
    version: str


class OSContext(TypedDict, total=False):
    """OS context information for analytics events."""

    __pydantic_config__ = ConfigDict(extra="allow")

    name: str
    version: str
    release: str


class PlatformContext(TypedDict, total=False):
    """Platform context information for analytics events."""

    __pydantic_config__ = ConfigDict(extra="allow")

    arch: str
    python_version: str


class AnalyticsContext(TypedDict, total=False):
    """Context information for analytics events."""

    __pydantic_config__ = ConfigDict(extra="allow")

    # don't mixup with library context with refers to the segment-analytics-python library
    app: AppContext
    group_id: NotRequired[str]
    os: OSContext
    platform: PlatformContext
