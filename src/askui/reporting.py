import base64
import json
import platform
import random
import sys
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from importlib.metadata import distributions
from io import BytesIO
from pathlib import Path
from typing import Any, Optional, Union

from jinja2 import Template
from PIL import Image
from typing_extensions import TypedDict, override


class Reporter(ABC):
    """Abstract base class for reporters. Cannot be instantiated directly.

    Defines the interface that all reporters must implement to be used with `askui.VisionAgent`.
    """

    @abstractmethod
    def add_message(
        self,
        role: str,
        content: Union[str, dict[str, Any], list[Any]],
        image: Optional[Image.Image | list[Image.Image]] = None,
    ) -> None:
        """Add a message to the report.

        Args:
            role (str): The role of the message sender (e.g., `"User"`, `"Assistant"`,
                `"System"`)
            content (str | dict | list): The message content, which can be a string,
                dictionary, or list, e.g. `'click 2x times on text "Edit"'`
            image (PIL.Image.Image | list[PIL.Image.Image], optional): PIL Image or
                list of PIL Images to include with the message
        """
        raise NotImplementedError

    @abstractmethod
    def generate(self) -> None:
        """Generates the final report.

        Implementing this method is only required if the report is not generated
        in "real-time", e.g., on calls of `add_message()`, but must be generated
        at the end of the execution.

        This method is called when the `askui.VisionAgent` context is exited or
        `askui.VisionAgent.close()` is called.
        """


class CompositeReporter(Reporter):
    """A reporter that combines multiple reporters.

    Allows generating different reports simultaneously. Each message added will be forwarded to all
        reporters passed to the constructor. The reporters are called (`add_message()`, `generate()`) in
        the order they are ordered in the `reporters` list.

    Args:
        reporters (list[Reporter] | None, optional): List of reporters to combine
    """

    def __init__(self, reporters: list[Reporter] | None = None) -> None:
        self._reporters = reporters or []

    @override
    def add_message(
        self,
        role: str,
        content: Union[str, dict[str, Any], list[Any]],
        image: Optional[Image.Image | list[Image.Image]] = None,
    ) -> None:
        """Add a message to the report."""
        for reporter in self._reporters:
            reporter.add_message(role, content, image)

    @override
    def generate(self) -> None:
        """Generates the final report."""
        for report in self._reporters:
            report.generate()


class SystemInfo(TypedDict):
    platform: str
    python_version: str
    packages: list[str]


class SimpleHtmlReporter(Reporter):
    """A reporter that generates HTML reports with conversation logs and system information.

    Args:
        report_dir (str, optional): Directory where reports will be saved.
            Defaults to `reports`.
    """

    def __init__(self, report_dir: str = "reports") -> None:
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)
        self.messages: list[dict[str, Any]] = []
        self.system_info = self._collect_system_info()

    def _collect_system_info(self) -> SystemInfo:
        """Collect system and Python information"""
        return {
            "platform": platform.platform(),
            "python_version": sys.version.split()[0],
            "packages": sorted(
                [f"{dist.metadata['Name']}=={dist.version}" for dist in distributions()]
            ),
        }

    def _image_to_base64(self, image: Image.Image) -> str:
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def _format_content(self, content: Union[str, dict[str, Any], list[Any]]) -> str:
        if isinstance(content, (dict, list)):
            return json.dumps(content, indent=2)
        return str(content)

    @override
    def add_message(
        self,
        role: str,
        content: Union[str, dict[str, Any], list[Any]],
        image: Optional[Image.Image | list[Image.Image]] = None,
    ) -> None:
        """Add a message to the report."""
        if image is None:
            _images = []
        elif isinstance(image, list):
            _images = image
        else:
            _images = [image]

        message = {
            "timestamp": datetime.now(tz=timezone.utc),
            "role": role,
            "content": self._format_content(content),
            "is_json": isinstance(content, (dict, list)),
            "images": [self._image_to_base64(img) for img in _images],
        }
        self.messages.append(message)

    @override
    def generate(self) -> None:
        """Generate an HTML report file.

        Creates a timestamped HTML file in the `report_dir` containing:
        - System information
        - All collected messages with their content and images
        - Syntax-highlighted JSON content
        """
        template_str = """
        <html>
            <head>
                <title>Vision Agent Report - {{ timestamp }}</title>
                <link rel="stylesheet"
                    href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github.min.css">
                <script
                    src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js">
                </script>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 20px;
                    }
                    th, td {
                        padding: 8px;
                        text-align: left;
                        border: 1px solid #ddd;
                    }
                    th { background-color: #f2f2f2; }
                    .assistant { background-color: #f8f8f8; }
                    .user { background-color: #fff; }
                    .system-info {
                        width: auto;
                        min-width: 50%;
                    }
                    .package-list {
                        font-family: monospace;
                    }
                    .hidden-packages {
                        display: none !important;
                    }
                    .visible-packages {
                        display: block !important;
                    }
                    .show-more {
                        color: blue;
                        cursor: pointer;
                        text-decoration: underline;
                        margin-top: 5px;
                        display: inline-block;
                    }
                    .message-image {
                        max-width: 800px;
                        max-height: 600px;
                        margin: 10px 0;
                    }
                    pre {
                        margin: 0;
                        white-space: pre-wrap;
                    }
                    pre code {
                        padding: 10px !important;
                        border-radius: 4px;
                        font-size: 14px;
                    }
                    .json-content {
                        background-color: #f6f8fa;
                        border-radius: 4px;
                        margin: 5px 0;
                    }
                </style>
                <script>
                    function togglePackages() {
                        const hiddenPackages = document.getElementById(
                            'hiddenPackages'
                        );
                        const toggleButton = document.getElementById(
                            'toggleButton'
                        );

                        if (hiddenPackages.classList.contains('hidden-packages')) {
                            hiddenPackages.classList.remove('hidden-packages');
                            hiddenPackages.classList.add('visible-packages');
                            toggleButton.textContent = 'Show less';
                        } else {
                            hiddenPackages.classList.remove('visible-packages');
                            hiddenPackages.classList.add('hidden-packages');
                            toggleButton.textContent = 'Show more...';
                        }
                    }

                    document.addEventListener('DOMContentLoaded', (event) => {
                        document.querySelectorAll('pre code').forEach((block) => {
                            hljs.highlightBlock(block);
                        });
                    });
                </script>
            </head>
            <body>
                <h1>Vision Agent Report</h1>
                <p>Generated: {{ timestamp }}</p>

                <h2>System Information</h2>
                <table class="system-info">
                    <tr>
                        <th>Platform</th>
                        <td>{{ system_info.platform }}</td>
                    </tr>
                    <tr>
                        <th>Python Version</th>
                        <td>{{ system_info.python_version }}</td>
                    </tr>
                    <tr>
                        <th>Installed Packages</th>
                        <td class="package-list">
                            {% for package in system_info.packages[:5] %}
                            {{ package }}<br>
                            {% endfor %}
                            {% if system_info.packages|length > 5 %}
                                <div id="hiddenPackages" class="hidden-packages">
                                {% for package in system_info.packages[5:] %}
                                    {{ package }}<br>
                                {% endfor %}
                                </div>
                                <span id="toggleButton" class="show-more"
                                    onclick="togglePackages()">Show more...</span>
                            {% endif %}
                        </td>
                    </tr>
                </table>

                <h2>Conversation Log</h2>
                <table>
                    <tr>
                        <th>Time</th>
                        <th>Role</th>
                        <th>Content</th>
                    </tr>
                    {% for msg in messages %}
                        <tr class="{{ msg.role.lower() }}">
                            <td>{{ msg.timestamp.strftime('%H:%M:%S') }}</td>
                            <td>{{ msg.role }}</td>
                            <td>
                                {% if msg.is_json %}
                                    <div class="json-content">
                                        <pre><code class="json">{{ msg.content }}</code></pre>
                                    </div>
                                {% else %}
                                    {{ msg.content }}
                                {% endif %}
                                {% for image in msg.images %}
                                    <br>
                                    <img src="data:image/png;base64,{{ image }}"
                                         class="message-image"
                                         alt="Message image">
                                {% endfor %}
                            </td>
                        </tr>
                    {% endfor %}
                </table>
            </body>
        </html>
        """

        template = Template(template_str)
        html = template.render(
            timestamp=datetime.now(tz=timezone.utc),
            messages=self.messages,
            system_info=self.system_info,
        )

        report_path = (
            self.report_dir / f"report_{datetime.now(tz=timezone.utc):%Y%m%d%H%M%S%f}"
            f"{random.randint(0, 1000):03}.html"
        )
        report_path.write_text(html)
