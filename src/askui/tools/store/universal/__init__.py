"""Universal tools that work with any agent type.

These tools don't require agent_os and can be used with VisionAgent,
AndroidVisionAgent, or any other agent type.
"""

from .print_to_console import PrintToConsoleTool
from .write_to_file_tool import WriteToFileTool

__all__ = [
    "PrintToConsoleTool",
    "WriteToFileTool",
]
