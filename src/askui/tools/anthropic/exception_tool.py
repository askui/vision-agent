from .base import Tool

class ExceptionTool(Tool):
    def __init__(self):
        super().__init__(
            name="exception_tool",
            description="If the agent is stuck or not able to perform any action, this tool can be used to raise an exception and stop the execution.",
            input_schema={
                "type": "object",
                "properties": {
                    "error_message": {
                        "type": "string",
                        "description": "The error message to be raised.",
                    },
                },
                "required": [
                    "error_message",
                ],
            },
        )

    def __call__(
        self,
        error_message: str,
    ) -> None:
        raise Exception(error_message)
