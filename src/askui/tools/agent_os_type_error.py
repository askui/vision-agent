class AgentOsTypeError(TypeError):
    """Exception raised when the agent OS is not of the expected type."""

    def __init__(self, expected_type: type, actual_type: type):
        self.expected_type = expected_type
        self.actual_type = actual_type
        super().__init__(
            f"Agent OS must be an {expected_type.__name__} instance. "
            f"Got {actual_type.__name__} instead."
        )
