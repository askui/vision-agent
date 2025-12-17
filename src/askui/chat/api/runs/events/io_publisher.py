"""IO publisher for publishing events to stdout."""

import json
import sys
from typing import Any

from askui.chat.api.runs.events.events import Event


class IOPublisher:
    """Publisher that serializes events to JSON and writes to stdout."""

    def publish(self, event: Event) -> None:
        """
        Publish an event by serializing it to JSON and writing to stdout.

        Args:
            event: The event to publish
        """
        try:
            event_dict: dict[str, Any] = event.model_dump(mode="json")
            event_json = json.dumps(event_dict)

            sys.stdout.write(event_json + "\n")
            sys.stdout.flush()
        except (TypeError, ValueError, AttributeError, OSError) as e:
            sys.stderr.write(f"Error publishing event: {e}\n")
            sys.stderr.flush()
