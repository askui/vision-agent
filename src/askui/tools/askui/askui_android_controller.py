import re
import time
from PIL import Image
from askui.models.utils import scale_coordinates_back, scale_image_with_padding
from ppadb.client import Client as AdbClient
import io
from typing import Optional, Union, List, Tuple, Dict, Any
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from io import StringIO

from PIL import Image, ImageDraw

from askui.reporting.report import SimpleReportGenerator
from askui.utils import ANDROID_KEY, draw_point_on_image, resize_to_max_edge

class AndroidDisplay:
    def __init__(
        self, unique_display_id: int, display_name: str, display_index: int
    ) -> None:
        self.unique_display_id = unique_display_id
        self.display_name = display_name
        self.display_index = display_index

    def __repr__(self) -> str:
        return (
            f"AndroidDisplay(unique_display_id={self.unique_display_id}, "
            f"display_name={self.display_name}, display_index={self.display_index})"
        )

@dataclass
class UIElementNode:
    """Class representing a single UI element node from the XML hierarchy."""
    
    # Basic properties
    index: int
    text: str
    resource_id: str
    class_name: str
    package: str
    content_desc: str
    
    # Boolean properties
    checkable: bool
    checked: bool
    clickable: bool
    enabled: bool
    focusable: bool
    focused: bool
    scrollable: bool
    long_clickable: bool
    password: bool
    selected: bool
    
    # Position/bounds
    bounds: Tuple[Tuple[int, int], Tuple[int, int]]  # ((left, top), (right, bottom))
    
    # Hierarchy
    children: List['UIElementNode']
    parent: Optional['UIElementNode'] = None

    @staticmethod
    def parse_bounds(bounds_str: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Parse bounds string "[left,top][right,bottom]" into tuple."""
        bounds_parts = bounds_str.replace('[', '').replace(']', ',').split(',')
        return ((int(bounds_parts[0]), int(bounds_parts[1])), 
                (int(bounds_parts[2]), int(bounds_parts[3])))

    def get_center_position(self) -> Tuple[int, int]:
        """Get the center position of the element."""
        left, top = self.bounds[0]
        right, bottom = self.bounds[1]
        return ((left + right) // 2, (top + bottom) // 2)
    
    def is_visible(self) -> bool:
        """Check if the element is visible (has non-zero size and is enabled)."""
        left, top = self.bounds[0]
        right, bottom = self.bounds[1]
        return (right - left > 0 and bottom - top > 0 and self.enabled)

    def to_dict(self, scale_factor: float = 1.0) -> Dict[str, Any]:
        """Convert the node to a dictionary representation with optional scaling."""
        # Scale the bounds
        (left, top), (right, bottom) = self.bounds
        scaled_bounds = (
            (int(left * scale_factor), int(top * scale_factor)),
            (int(right * scale_factor), int(bottom * scale_factor))
        )
        
        # Get center position and scale it
        center_x, center_y = self.get_center_position()
        scaled_center = (int(center_x * scale_factor), int(center_y * scale_factor))
        
        return {
            "type": "element",
            "properties": {
                "text": self.text,
                "resource_id": self.resource_id,
                "class_name": self.class_name,
                "package": self.package,
                "content_desc": self.content_desc,
            },
            "state": {
                "checkable": self.checkable,
                "checked": self.checked,
                "clickable": self.clickable,
                "enabled": self.enabled,
                "focusable": self.focusable,
                "focused": self.focused,
                "scrollable": self.scrollable,
                "long_clickable": self.long_clickable,
                "password": self.password,
                "selected": self.selected,
                "visible": self.is_visible(),
            },
            "position": {
                "bounds": {
                    "left": scaled_bounds[0][0],
                    "top": scaled_bounds[0][1],
                    "right": scaled_bounds[1][0],
                    "bottom": scaled_bounds[1][1],
                },
                "center": {
                    "x": scaled_center[0],
                    "y": scaled_center[1],
                }
            },
            "children": [child.to_dict(scale_factor) for child in self.children]
        }
    
    def __str__(self) -> str:
        """String representation of the node."""
        return f"{self.class_name}(text='{self.text}', resource_id='{self.resource_id}')"


class UIElementNodeCollection:
    """Class representing a collection of UI element nodes."""
    
    def __init__(self, root_node: Optional[UIElementNode] = None):
        self.root = root_node
        
    @classmethod
    def from_xml_string(cls, xml_string: str) -> 'UIElementNodeCollection':
        """Create a UIElementNodeCollection from an XML string."""
        # Parse XML string
        tree = ET.parse(StringIO(xml_string))
        root = tree.getroot()
        
        # Create the collection
        collection = cls()
        collection.root = cls._create_node_from_element(root)
        return collection
    
    @classmethod
    def _create_node_from_element(cls, element: ET.Element) -> UIElementNode:
        """Create a UIElementNode from an XML element."""
        # Parse bounds
        bounds = UIElementNode.parse_bounds(element.get('bounds', '[0,0][0,0]'))

        # Create node
        node = UIElementNode(
            index=int(element.get('index', 0)),
            text=element.get('text', ''),
            resource_id=element.get('resource-id', ''),
            class_name=element.get('class', ''),
            package=element.get('package', ''),
            content_desc=element.get('content-desc', ''),
            checkable=element.get('checkable', 'false').lower() == 'true',
            checked=element.get('checked', 'false').lower() == 'true',
            clickable=element.get('clickable', 'false').lower() == 'true',
            enabled=element.get('enabled', 'false').lower() == 'true',
            focusable=element.get('focusable', 'false').lower() == 'true',
            focused=element.get('focused', 'false').lower() == 'true',
            scrollable=element.get('scrollable', 'false').lower() == 'true',
            long_clickable=element.get('long-clickable', 'false').lower() == 'true',
            password=element.get('password', 'false').lower() == 'true',
            selected=element.get('selected', 'false').lower() == 'true',
            bounds=bounds,
            children=[]
        )
        
        # Process children
        for child_element in element.findall('node'):
            child_node = cls._create_node_from_element(child_element)
            child_node.parent = node
            node.children.append(child_node)
            
        return node

    def to_json(self, scale_factor: float) -> Dict[str, Any]:
        return self.root.to_dict(scale_factor)

class AskUiAndroidControllerClient:
    def __init__(self, report: SimpleReportGenerator | None = None) -> None:
        self._client = None
        self._device = None
        self._mouse_position = (0, 0)
        self._displays: list[AndroidDisplay] = []
        self._selected_display: Optional[AndroidDisplay] = None
        self.report = report
        self.original_resolution = (0, 0)
        self.scaled_resolution = (0, 0)

    def _reset_screen_resolution(self) -> None:
        self.original_resolution = self.get_screen_resolution()
        self.scaled_resolution = resize_to_max_edge(self.original_resolution, 1200)

    def rescale_back_coordinates(self, x: int, y: int):
        if self.original_resolution == (0, 0):
            raise RuntimeError("Screen resolution not set")
        if self.scaled_resolution == (0, 0):
            raise RuntimeError("Scaled resolution not set")
        return scale_coordinates_back(
            x,
            y,
            self.original_resolution[0],
            self.original_resolution[1],
            self.scaled_resolution[0],
            self.scaled_resolution[1],
        )

    def get_connected_displays(self) -> list[AndroidDisplay]:
        self._check_if_device_is_connected()
        displays = []
        output = self._device.shell("dumpsys SurfaceFlinger --display-id")

        index = 0
        for line in output.splitlines():
            if line.startswith("Display"):
                match = re.match(r"Display (\d+) .* displayName=\"([^\"]+)\"", line)
                if match:
                    unique_display_id = int(match.group(1))
                    display_name = match.group(2)
                    displays.append(
                        AndroidDisplay(unique_display_id, display_name, index)
                    )
                    index += 1
        return displays

    def _check_if_device_is_connected(self) -> None:
        if not self._client or not self._device:
            raise RuntimeError("No device connected")
        devices = self._client.devices()
        if not devices:
            raise RuntimeError("No devices connected")

        for device in devices:
            if device.serial == self._device.serial:
                return
        raise Exception(f"Device {self._device.serial} not found in connected devices")

    def connect(self) -> None:
        self._client = AdbClient()
        self.set_device_by_index(0)
        self._add_report_message("AgentOS", f"connect() to {self._device.serial}")

    def disconnect(self) -> None:
        self._client = None
        self._device = None

    def _set_display(self, display: AndroidDisplay) -> None:
        self._selected_display = display
        self._mouse_position = (0, 0)
        self._reset_screen_resolution()
        self._add_report_message("AgentOS", f"select display {str(display)}")

    def set_display_by_index(self, displayNumber: int = 0) -> None:
        self._displays = self.get_connected_displays()
        if not self._displays:
            raise RuntimeError("No displays connected")
        if displayNumber >= len(self._displays):
            raise RuntimeError(
                f"Display number {displayNumber} out of range it must be less than {len(self._displays)}"
            )
        self._set_display(self._displays[displayNumber])

    def set_display_by_id(self, display_id: int) -> None:
        self._displays = self.get_connected_displays()
        if not self._displays:
            raise RuntimeError("No displays connected")
        for display in self._displays:
            if display.display_id == display_id:
                self._set_display(display)
                return
        raise RuntimeError(f"Display ID {display_id} not found")

    def set_display_by_name(self, display_name: str) -> None:
        self._displays = self.get_connected_displays()
        if not self._displays:
            raise RuntimeError("No displays connected")
        for display in self._displays:
            if display.display_name == display_name:
                self._set_display(display)
                return
        raise RuntimeError(f"Display name {display_name} not found")

    def set_device_by_index(self, device_index: int = 0) -> None:
        devices = self._client.devices()
        if not devices:
            raise RuntimeError("No devices connected")
        if device_index >= len(devices):
            raise RuntimeError(
                f"Device index {device_index} out of range it must be less than {len(devices)}"
            )
        self._device = devices[device_index]
        self._add_report_message("AgentOS", f"set_display({device_index})")
        self.set_display_by_index(0)

    def set_device_by_name(self, displayName: str) -> None:
        devices = self._client.devices()
        if not devices:
            raise RuntimeError("No devices connected")
        for device in devices:
            if device.serial == displayName:
                self._device = device
                self.set_display_by_index(0)
                self._add_report_message("AgentOS", f"set_display({displayName})")
                return
        raise RuntimeError(f"Device name {displayName} not found")

    def screenshot(self, report: bool = True) -> Image.Image:
        self._check_if_device_is_connected()
        connection_to_device = self._device.create_connection()
        connection_to_device.send(
            f"shell:/system/bin/screencap -p -d {self._selected_display.unique_display_id}"
        )
        response = connection_to_device.read_all()
        if response and len(response) > 5 and response[5] == 0x0D:
            response = response.replace(b"\r\n", b"\n")
        image = Image.open(io.BytesIO(response))
        if report:
            self._add_report_message(
                "AgentOS", f"screenshot() with size {image.size}", image
            )
        return image

    def get_cursor_position(self) -> tuple[int, int]:
        self._add_report_message(
            "AgentOS", f"get_cursor_position() = {self._mouse_position}"
        )
        return self._mouse_position

    def tap(self, x: int, y: int) -> None:
        self._check_if_device_is_connected()
        self._device.shell(
            f"input -d {self._selected_display.display_index} tap {x} {y}"
        )
        self._mouse_position = (x, y)
        self._add_report_message(
            "AgentOS",
            f"tap({x}, {y})",
            draw_point_on_image(self.screenshot(report=False), x, y, size=10),
        )

    def swipe(
        self, x1: int, y1: int, x2: int, y2: int, duration_in_ms: int = 1000
    ) -> None:
        self._check_if_device_is_connected()
        self._device.shell(
            f"input -d {self._selected_display.display_index} swipe {x1} {y1} {x2} {y2} {duration_in_ms}"
        )
        self._mouse_position = (x2, y2)
        self._add_report_message(
            "AgentOS", f"swipe({x1}, {y1}, {x2}, {y2}, {duration_in_ms})"
        )

    def drag_and_drop(
        self, x1: int, y1: int, x2: int, y2: int, duration_in_ms: int = 1000
    ) -> None:
        self._check_if_device_is_connected()
        self._device.shell(
            f"input -d {self._selected_display.display_index} draganddrop {x1} {y1} {x2} {y2} {duration_in_ms}"
        )
        self._mouse_position = (x2, y2)
        self._add_report_message(
            "AgentOS", f"drag_and_drop({x1}, {y1}, {x2}, {y2}, {duration_in_ms})"
        )

    def move_mouse(self, x: int, y: int) -> None:
        self._mouse_position = (x, y)
        self._add_report_message(
            "AgentOS",
            f"move_mouse({x}, {y})",
            draw_point_on_image(self.screenshot(report=False), x, y, size=10),
        )

    def roll(self, dx: int, dy: int) -> None:
        self._check_if_device_is_connected()
        self._device.shell(
            f"input -d {self._selected_display.display_index} roll {dx} {dy}"
        )
        self._mouse_position = (
            self._mouse_position[0] + dx,
            self._mouse_position[1] + dy,
        )
        self._add_report_message("AgentOS", f"roll({dx}, {dy})")

    def key_event(self, key: ANDROID_KEY) -> None:
        self._check_if_device_is_connected()
        self._device.shell(
            f"input -d {self._selected_display.display_index} keyevent {key.capitalize()}"
        )
        self._add_report_message("AgentOS", f"key_event({key.capitalize()})")

    def shell(self, command: str) -> str:
        self._check_if_device_is_connected()
        result = self._device.shell(command)
        self._add_report_message("AgentOS", f"shell({command})")
        return result

    def debug_draw(self, x1, y1, x2, y2) -> None:
        self._check_if_device_is_connected()
        image = self.screenshot(report=False)
        draw = ImageDraw.Draw(image)
        draw.rectangle([x1, y1, x2, y2], outline="red", width=10)
        self._add_report_message(
            "AgentOS", f"debug_draw({x1}, {y1}, {x2}, {y2})", image
        )
        return image

    def get_screen_resolution(self) -> tuple[int, int]:
        self._check_if_device_is_connected()
        image = self.screenshot(report=False)
        return image.size

    def _add_report_message(
        self,
        role: str,
        content: Union[str, dict, list],
        image: Optional[Image.Image] = None,
    ):
        if self.report is not None:
            self.report.add_message(
                role,
                content,
                scale_image_with_padding(image, 553, 1200) if image else None,
            )
    def _get_scale_factor(self) -> float:
        return min(self.scaled_resolution[0] / self.original_resolution[0],self.scaled_resolution[1] / self.original_resolution[1])
    
    def try_to_get_ui_hierarchy(self) -> Optional[UIElementNodeCollection]:
        self._check_if_device_is_connected()
        dump_file = f"/sdcard/window_dump_{int(time.time() * 1000)}.xml" 
        dump_output = self._device.shell(f"uiautomator dump {dump_file}")
        if not dump_output or 'ERROR' in dump_output:
            return None
        xml_output = self._device.shell(f"cat {dump_file}")
        if not xml_output or "No such file" in xml_output:
            return None
        collection =UIElementNodeCollection.from_xml_string(xml_output)
        self._device.shell(f"rm -rf {dump_file}")
        return collection
