class AutomationError(Exception):
    """Exception raised when the automation step cannot complete."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def truncate_long_strings(json_data, max_length=100, truncate_length=20, tag="[shortened]"):
    """
    Traverse and truncate long strings in JSON data.

    :param json_data: The JSON data (dict, list, or str).
    :param max_length: The maximum length before truncation.
    :param truncate_length: The length to truncate the string to.
    :param tag: The tag to append to truncated strings.
    :return: JSON data with truncated long strings.
    """
    if isinstance(json_data, dict):
        return {k: truncate_long_strings(v, max_length, truncate_length, tag) for k, v in json_data.items()}
    elif isinstance(json_data, list):
        return [truncate_long_strings(item, max_length, truncate_length, tag) for item in json_data]
    elif isinstance(json_data, str) and len(json_data) > max_length:
        return f"{json_data[:truncate_length]}... {tag}"
    return json_data
