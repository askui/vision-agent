from datetime import datetime, timezone


def parse_retry_after_header(retry_after: str) -> float:
    """Parse the Retry-After header value.

    The Retry-After header value can be a number of seconds or a date in
    RFC 2822 format:
    - `<number>`
    - `<day-name>, <day> <month> <year> <hour>:<minute>:<second> GMT`

    The date must be in GMT timezone.

    Args:
        retry_after (str): The Retry-After header value.

    Returns:
        float: The number of seconds to wait.

    Raises:
        ValueError: If the header value cannot be parsed.
    """
    try:
        return float(retry_after)
    except (TypeError, ValueError):
        try:
            dt = datetime.strptime(  # noqa: DTZ007
                retry_after,
                "%a, %d %b %Y %H:%M:%S GMT",
            )
            dt = dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            return (dt - now).total_seconds()
        except (TypeError, ValueError) as e:
            error_msg = f"Could not parse Retry-After header: {retry_after}"
            raise ValueError(error_msg) from e
