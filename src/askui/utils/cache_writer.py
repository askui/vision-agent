import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from askui.models.shared.agent_message_param import MessageParam, ToolUseBlockParam
from askui.models.shared.agent_on_message_cb import OnMessageCbParam

logger = logging.getLogger(__name__)


class CacheWriter:
    def __init__(self, cache_dir: str = ".cache", file_name: str = "") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.messages: list[ToolUseBlockParam] = []
        if file_name and not file_name.endswith(".json"):
            file_name += ".json"
        self.file_name = file_name
        self.was_cached_execution = False

    def add_message_cb(self, param: OnMessageCbParam) -> MessageParam:
        """Add a message to cache."""
        if param.message.role == "assistant":
            contents = param.message.content
            if isinstance(contents, list):
                for content in contents:
                    if isinstance(content, ToolUseBlockParam):
                        self.messages.append(content)
                        if content.name == "execute_cached_executions_tool":
                            self.was_cached_execution = True
        if param.message.stop_reason == "end_turn":
            self.generate()

        return param.message

    def set_file_name(self, file_name: str) -> None:
        if not file_name.endswith(".json"):
            file_name += ".json"
        self.file_name = file_name

    def reset(self, file_name: str = "") -> None:
        self.messages = []
        if file_name and not file_name.endswith(".json"):
            file_name += ".json"
        self.file_name = file_name
        self.was_cached_execution = False

    def generate(self) -> None:
        if self.was_cached_execution:
            logger.info("Will not write cache file as this was a cached execution")
            return
        if not self.file_name:
            self.file_name = (
                f"cached_trajectory_{datetime.now(tz=timezone.utc):%Y%m%d%H%M%S%f}.json"
            )
        cache_file_path = self.cache_dir / self.file_name

        messages_json = [m.model_dump() for m in self.messages]
        with cache_file_path.open("w", encoding="utf-8") as f:
            json.dump(messages_json, f, indent=4)
        info_msg = f"Cache File written at {str(cache_file_path)}"
        logger.info(info_msg)
        self.reset()

    @staticmethod
    def read_cache_file(cache_file_path: Path) -> list[ToolUseBlockParam]:
        with cache_file_path.open("r", encoding="utf-8") as f:
            raw_trajectory = json.load(f)
        return [ToolUseBlockParam(**step) for step in raw_trajectory]
