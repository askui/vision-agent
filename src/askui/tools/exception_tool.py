from askui.models.shared.tools import AgentException, Tool


class ExceptionTool(Tool):
    """
    Exception tool that can be used to raise an exception.
    """

    def __init__(self) -> None:
        super().__init__(
            name="exception_tool",
            description="""
            Exception tool that can be used to raise an exception.
            which will stop the execution of the agent.
        """,
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": """
                    The exception message to raise. this will be displayed to the user.
                    """,
                    },
                },
                "required": ["text"],
            },
        )

    def __call__(self, text: str) -> None:
        raise AgentException(text)
