from .base import Tool, ToolResult
import os

class FileWriteTool(Tool):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

        super().__init__(
            name="file_write_tool",
            description="Writes content to a file in the base directory. Overwrites if the file already exists.",
            input_schema={
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "The name of the file to write to (within the base directory).",
                    },
                    "content": {
                        "type": "string",
                        "description": "The text content to write into the file.",
                    },
                    "file_write_mode": {
                        "type": "string",
                        "description": "The mode in which to open the file. Default is 'w' (write). Other options include 'a' (append).",
                        "enum": ["w", "a"],
                        "default": "w",
                    },
                },
                "required": ["file_name", "content"],
            },
        )

    def __call__(self, file_name: str, content: str, file_write_mode:str = 'w') -> None:
        file_path = os.path.join(self.base_dir, file_name)
        with open(file_path, file_write_mode, encoding="utf-8") as f:
            f.write(content)
        return ToolResult(output=f"File '{file_name}' written successfully.")


class FileReadTool(Tool):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

        super().__init__(
            name="file_read_tool",
            description="Reads content from a file in the base directory.",
            input_schema={
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "The name of the file to read from (within the base directory).",
                    },
                },
                "required": ["file_name"],
            },
        )

    def __call__(self, file_name: str) -> str:
        file_path = os.path.join(self.base_dir, file_name)
        print('3asba')
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_name}")
        with open(file_path, "r", encoding="utf-8") as f:
            return ToolResult(output=f.read())
