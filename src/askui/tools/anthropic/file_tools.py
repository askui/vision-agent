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
                    }
                },
                "required": ["file_name", "content"],
            },
        )

    def __call__(self, file_name: str, content: str) -> None:
        file_path = os.path.join(self.base_dir, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'a', encoding="utf-8") as f:
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
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_name}")
        with open(file_path, "r", encoding="utf-8") as f:
            return ToolResult(output=f.read())
