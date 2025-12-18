"""IO publisher for publishing events to stdout."""

import json
import sys
from typing import Any

from askui.chat.api.runs.events.events import Event
from askui.chat.api.settings import Settings


class IOPublisher:
    """Publisher that serializes events to JSON and writes to stdout."""

    def __init__(self, enabled: bool) -> None:
        """
        Initialize the IO publisher.

        Args:
            settings: The settings instance containing configuration for the IO publisher.
        """
        self._enabled = enabled

    def publish(self, event: Event) -> None:
        """
        Publish an event by serializing it to JSON and writing to stdout.

        If the publisher is disabled, this method does nothing.

        Args:
            event: The event to publish
        """
        if not self._enabled:
            return

        try:
            event_dict: dict[str, Any] = event.model_dump(mode="json")
            event_json = json.dumps(event_dict)

            sys.stdout.write(event_json + "\n")
            sys.stdout.flush()
        except (TypeError, ValueError, AttributeError, OSError) as e:
            sys.stderr.write(f"Error publishing event: {e}\n")
            sys.stderr.flush()
