"""Geometry types for representing points and coordinates."""

from typing import Annotated

from pydantic import Field

Point = tuple[int, int]
"""
A tuple of two integers representing the coordinates of a point on the screen.
"""

PointList = Annotated[list[Point], Field(min_length=1)]
"""
A list of points representing the coordinates of elements on the screen.
"""
