from pathlib import Path
from jinja2 import Template
from datetime import datetime
from typing import List, Dict, Optional, Union
import platform
import sys
from importlib.metadata import distributions
import base64
from io import BytesIO
from PIL import Image
import json


class SimpleReportGenerator:
    def __init__(self, report_dir: str = "reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)
        self.messages: List[Dict] = []
        self.system_info = self._collect_system_info()
        
    def _collect_system_info(self) -> Dict[str, str]:
        """Collect system and Python information"""
        return {
            "platform": platform.platform(),
            "python_version": sys.version.split()[0],
            "packages": sorted([f"{dist.metadata['Name']}=={dist.version}" 
                              for dist in distributions()])
        }
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    def _format_content(self, content: Union[str, dict, list]) -> str:
        """Format content based on its type"""
        if isinstance(content, (dict, list)):
            return json.dumps(content, indent=2)
        return str(content)
    
    def add_message(self, role: str, content: Union[str, dict, list], image: Optional[Image.Image] = None):
        """Add a message to the report, optionally with an image"""
        message = {
            "timestamp": datetime.now(),
            "role": role,
            "content": self._format_content(content),
            "is_json": isinstance(content, (dict, list)),
            "image": self._image_to_base64(image) if image else None
        }
        self.messages.append(message)
    
    def generate_report(self) -> str:
        """Generate HTML report using a Jinja template"""
        template_str = """
        <html>
            <head>
                <title>Vision Agent Report - {{ timestamp }}</title>
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github.min.css">
                <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
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
                        const hiddenPackages = document.getElementById('hiddenPackages');
                        const toggleButton = document.getElementById('toggleButton');
                        
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
                                <span id="toggleButton" class="show-more" onclick="togglePackages()">Show more...</span>
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
                                {% if msg.image %}
                                    <br>
                                    <img src="data:image/png;base64,{{ msg.image }}" 
                                         class="message-image" 
                                         alt="Message image">
                                {% endif %}
                            </td>
                        </tr>
                    {% endfor %}
                </table>
            </body>
        </html>
        """
        
        template = Template(template_str)
        html = template.render(
            timestamp=datetime.now(),
            messages=self.messages,
            system_info=self.system_info
        )
        
        report_path = self.report_dir / f"report_{datetime.now():%Y%m%d_%H%M%S}.html"
        report_path.write_text(html)
        return str(report_path)
