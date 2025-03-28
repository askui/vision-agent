from typing import TypedDict
from typing_extensions import NotRequired

from pydantic import ConfigDict


class AppContext(TypedDict, total=False):
    """App context information for analytics events."""

    __pydantic_config__ = ConfigDict(extra="allow")

    name: str
    version: str


class AnalyticsContext(TypedDict, total=False):
    """Context information for analytics events."""

    __pydantic_config__ = ConfigDict(extra="allow")

    app: AppContext
    group_id: NotRequired[str]
