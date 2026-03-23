"""
Parse UIAutomator hierarchy dump XML from Android (normalized shell output).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

# Match & that is not start of a valid XML entity
_RE_INVALID_AMP = re.compile(r"&(?!(?:amp|lt|gt|apos|quot|#\d+|#x[0-9a-fA-F]+);)")  # noqa: E501
_RE_BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")

_XML_START_MARKERS = ("<?xml", "<hierarchy")


@dataclass
class UIElement:
    """Parsed UI element from UIAutomator dump."""

    text: str
    resource_id: str
    content_desc: str
    class_name: str
    bounds: str
    clickable: bool
    enabled: bool
    package: str
    _center: tuple[int, int] | None = None

    @property
    def center(self) -> tuple[int, int] | None:
        """Return (x, y) center of bounds, or None if bounds invalid."""
        if self._center is not None:
            return self._center
        m = _RE_BOUNDS.match(self.bounds)
        if not m:
            return None
        x1, y1, x2, y2 = (int(g) for g in m.groups())
        self._center = ((x1 + x2) // 2, (y1 + y2) // 2)
        return self._center

    def __str__(self) -> str:
        """Short description for list output."""
        parts: list[str] = [f"clickable={self.clickable}"]
        if self.center:
            parts.append(f"center=(x={self.center[0]}, y={self.center[1]})")
        if self.text:
            parts.append(f'text="{self.text}"')
        if self.resource_id:
            parts.append(f'resource-id="{self.resource_id}"')
        if self.content_desc:
            parts.append(f'content-desc="{self.content_desc}"')
        if self.class_name:
            parts.append(f"class={self.class_name.split('.')[-1]}")
        return " | ".join(parts)

    def set_center(self, center: tuple[int, int]) -> None:
        """Set the center of the element."""
        self._center = center

    @classmethod
    def from_xml_attrib(cls, attrib: Mapping[str, str]) -> UIElement | None:
        """Build from XML node attributes, or None if there are no bounds."""
        bounds = attrib.get("bounds", "").strip()
        if not bounds:
            return None
        return cls(
            text=attrib.get("text", ""),
            resource_id=attrib.get("resource-id", ""),
            content_desc=attrib.get("content-desc", ""),
            class_name=attrib.get("class", ""),
            bounds=bounds,
            clickable=attrib.get("clickable", "false") == "true",
            enabled=attrib.get("enabled", "true") == "true",
            package=attrib.get("package", ""),
        )

    @staticmethod
    def from_json(json_content: Mapping[str, str]) -> UIElement:
        """Build a UIElement from a string-keyed mapping (e.g. JSON object)."""
        return UIElement(
            text=json_content.get("text", ""),
            resource_id=json_content.get("resource-id", ""),
            content_desc=json_content.get("content-desc", ""),
            class_name=json_content.get("class", ""),
            bounds=json_content.get("bounds", ""),
            clickable=json_content.get("clickable", "false") == "true",
            enabled=json_content.get("enabled", "true") == "true",
            package=json_content.get("package", ""),
        )


class UIElementCollection:
    """Collection of UI elements."""

    def __init__(self, elements: list[UIElement]) -> None:
        self._elements = list(elements)

    def get_all(self) -> list[UIElement]:
        """Return a copy of all elements."""
        return list(self._elements)

    def __iter__(self) -> Iterator[UIElement]:
        return iter(self._elements)

    def __len__(self) -> int:
        return len(self._elements)

    def __str__(self) -> str:
        """String representation of the collection."""
        return "\n".join(str(element) for element in self._elements)

    @staticmethod
    def _normalize_dump_string(raw: str) -> str:
        """
        Normalize raw shell output to valid XML before parsing.

        Handles encoding, ADB/shell cruft, control chars, and unescaped & in attributes.
        """
        raw = raw.strip().lstrip("\ufeff")
        start_indices = [raw.find(marker) for marker in _XML_START_MARKERS]
        valid = [i for i in start_indices if i >= 0]
        if valid:
            raw = raw[min(valid) :]
        end_tag = "</hierarchy>"
        j = raw.rfind(end_tag)
        if j >= 0:
            raw = raw[: j + len(end_tag)]
        raw = "".join(c for c in raw if c in "\n\t" or ord(c) >= 32)
        return _RE_INVALID_AMP.sub("&amp;", raw)

    @staticmethod
    def build_from_xml_dump(xml_content: str) -> UIElementCollection:
        """Build a UIElementCollection from a UIAutomator dump XML string."""
        elements: list[UIElement] = []
        xml_content = UIElementCollection._normalize_dump_string(xml_content)
        if not xml_content:
            return UIElementCollection(elements)
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            return UIElementCollection(elements)

        def collect(node: ET.Element) -> None:
            elem = UIElement.from_xml_attrib(node.attrib)
            if elem is not None:
                elements.append(elem)
            for child in node:
                collect(child)

        collect(root)
        return UIElementCollection(elements)
