import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from askui.locators.serializers import VlmLocatorSerializer
from askui.models.anthropic.messages_api import AnthropicMessagesApi
from askui.models.model_router import create_api_client
from askui.models.shared.agent_message_param import (
    MessageParam,
    ToolUseBlockParam,
    UsageParam,
)
from askui.models.shared.agent_on_message_cb import OnMessageCbParam
from askui.models.shared.settings import (
    CacheFile,
    CacheMetadata,
    CacheWriterSettings,
)
from askui.models.shared.tools import ToolCollection
from askui.utils.placeholder_handler import PlaceholderHandler
from askui.utils.placeholder_identifier import identify_placeholders

logger = logging.getLogger(__name__)


class CacheWriter:
    def __init__(
        self,
        cache_dir: str = ".cache",
        file_name: str = "",
        cache_writer_settings: CacheWriterSettings | None = None,
        toolbox: ToolCollection | None = None,
        goal: str | None = None,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.messages: list[ToolUseBlockParam] = []
        if file_name and not file_name.endswith(".json"):
            file_name += ".json"
        self.file_name = file_name
        self.was_cached_execution = False
        self._cache_writer_settings = cache_writer_settings or CacheWriterSettings()
        self._goal = goal
        self._toolbox: ToolCollection | None = None
        self._accumulated_usage = UsageParam()

        # Set toolbox for cache writer so it can check which tools are cacheable
        self._toolbox = toolbox

    def add_message_cb(self, param: OnMessageCbParam) -> MessageParam:
        """Add a message to cache and accumulate usage statistics."""
        if param.message.role == "assistant":
            contents = param.message.content
            if isinstance(contents, list):
                for content in contents:
                    if isinstance(content, ToolUseBlockParam):
                        self.messages.append(content)
                        if content.name == "execute_cached_executions_tool":
                            self.was_cached_execution = True

            # Accumulate usage from assistant messages
            if param.message.usage:
                self._accumulate_usage(param.message.usage)

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
        self._accumulated_usage = UsageParam()

    def generate(self) -> None:
        if self.was_cached_execution:
            logger.info("Will not write cache file as this was a cached execution")
            return

        if not self.file_name:
            self.file_name = (
                f"cached_trajectory_{datetime.now(tz=timezone.utc):%Y%m%d%H%M%S%f}.json"
            )

        cache_file_path = self.cache_dir / self.file_name

        goal_to_save, trajectory_to_save, placeholders_dict = (
            self._replace_placeholders()
        )

        if self._toolbox is not None:
            trajectory_to_save = self._blank_non_cacheable_tool_inputs(
                trajectory_to_save
            )
        else:
            logger.info("No toolbox set, skipping non-cacheable tool input blanking")

        self._generate_cache_file(
            goal_to_save, trajectory_to_save, placeholders_dict, cache_file_path
        )
        self.reset()

    def _replace_placeholders(
        self,
    ) -> tuple[str | None, list[ToolUseBlockParam], dict[str, str]]:
        # Determine which trajectory and placeholders to use
        trajectory_to_save = self.messages
        goal_to_save = self._goal
        placeholders_dict: dict[str, str] = {}

        if (
            self._cache_writer_settings.placeholder_identification_strategy == "llm"
            and self.messages
        ):
            # Get messages_api for placeholder identification
            messages_api = AnthropicMessagesApi(
                client=create_api_client(
                    self._cache_writer_settings.llm_placeholder_id_api_provider
                ),
                locator_serializer=VlmLocatorSerializer(),
            )
            placeholders_dict, placeholder_definitions = identify_placeholders(
                trajectory=self.messages,
                messages_api=messages_api,
            )
            n_placeholders = len(placeholder_definitions)
            # Replace actual values with {{placeholder_name}} syntax in trajectory
            if placeholder_definitions:
                trajectory_to_save = (
                    PlaceholderHandler.replace_values_with_placeholders(
                        trajectory=self.messages,
                        placeholder_definitions=placeholder_definitions,
                    )
                )

                # Also apply placeholder replacement to the goal
                if self._goal:
                    goal_to_save = self._goal
                    # Build replacement map: value -> placeholder syntax
                    replacements = {
                        str(p.value): f"{{{{{p.name}}}}}"
                        for p in placeholder_definitions
                    }
                    # Sort by length descending to replace longer matches first
                    for actual_value in sorted(
                        replacements.keys(), key=len, reverse=True
                    ):
                        if actual_value in goal_to_save:
                            goal_to_save = goal_to_save.replace(
                                actual_value, replacements[actual_value]
                            )
        else:
            # Manual placeholder extraction
            placeholder_names = PlaceholderHandler.extract_placeholders(self.messages)
            placeholders_dict = {
                name: f"Placeholder for {name}"  # Generic description
                for name in placeholder_names
            }
            n_placeholders = len(placeholder_names)
        logger.info(f"Replaced {n_placeholders} placeholder values in trajectory")
        return goal_to_save, trajectory_to_save, placeholders_dict

    def _blank_non_cacheable_tool_inputs(
        self, trajectory: list[ToolUseBlockParam]
    ) -> list[ToolUseBlockParam]:
        """Blank out input fields for non-cacheable tools to save space.

        For tools marked as is_cacheable=False, we replace their input with an
        empty dict since we won't be executing them from cache anyway.

        Args:
            trajectory: The trajectory to process

        Returns:
            New trajectory with non-cacheable tool inputs blanked out
        """
        if self._toolbox is None:
            return trajectory

        blanked_count = 0
        result: list[ToolUseBlockParam] = []
        for tool_block in trajectory:
            # Check if this tool is cacheable
            tool = self._toolbox.get_tools().get(tool_block.name)

            # If tool is not cacheable, blank out its input
            if tool is not None and not tool.is_cacheable:
                logger.debug(
                    f"Blanking input for non-cacheable tool: {tool_block.name}"
                )
                blanked_count += 1
                result.append(
                    ToolUseBlockParam(
                        id=tool_block.id,
                        name=tool_block.name,
                        input={},  # Blank out the input
                        type=tool_block.type,
                        cache_control=tool_block.cache_control,
                    )
                )
            else:
                # Keep the tool block as-is
                result.append(tool_block)

        if blanked_count > 0:
            logger.info(
                f"Blanked inputs for {blanked_count} non-cacheable tool(s) to save space"
            )

        return result

    def _generate_cache_file(
        self,
        goal_to_save: str | None,
        trajectory_to_save: list[ToolUseBlockParam],
        placeholders_dict: dict[str, str],
        cache_file_path: Path,
    ) -> None:
        cache_file = CacheFile(
            metadata=CacheMetadata(
                version="0.1",
                created_at=datetime.now(tz=timezone.utc),
                goal=goal_to_save,
                token_usage=self._accumulated_usage,
            ),
            trajectory=trajectory_to_save,
            placeholders=placeholders_dict,
        )

        with cache_file_path.open("w", encoding="utf-8") as f:
            json.dump(cache_file.model_dump(mode="json"), f, indent=4)
        logger.info(f"Cache file successfully written: {cache_file_path} ")

    def _accumulate_usage(self, step_usage: UsageParam) -> None:
        """Accumulate usage statistics from a single API call.

        Args:
            step_usage: Usage from a single message
        """
        self._accumulated_usage.input_tokens = (
            self._accumulated_usage.input_tokens or 0
        ) + (step_usage.input_tokens or 0)
        self._accumulated_usage.output_tokens = (
            self._accumulated_usage.output_tokens or 0
        ) + (step_usage.output_tokens or 0)
        self._accumulated_usage.cache_creation_input_tokens = (
            self._accumulated_usage.cache_creation_input_tokens or 0
        ) + (step_usage.cache_creation_input_tokens or 0)
        self._accumulated_usage.cache_read_input_tokens = (
            self._accumulated_usage.cache_read_input_tokens or 0
        ) + (step_usage.cache_read_input_tokens or 0)

    @staticmethod
    def read_cache_file(cache_file_path: Path) -> CacheFile:
        """Read cache file with backward compatibility for v0.0 format.

        Returns:
            CacheFile object with metadata and trajectory
        """
        logger.debug(f"Reading cache file: {cache_file_path}")
        with cache_file_path.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Detect format version
        if isinstance(raw_data, list):
            # v0.0 format: just a list of tool use blocks
            logger.info(
                f"Detected v0.0 cache format in {cache_file_path.name}, migrating to v0.1"
            )
            trajectory = [ToolUseBlockParam(**step) for step in raw_data]
            # Create default metadata for v0.0 files (migrated to v0.1 format)
            cache_file = CacheFile(
                metadata=CacheMetadata(
                    version="0.1",  # Migrated from v0.0 to v0.1 format
                    created_at=datetime.fromtimestamp(
                        cache_file_path.stat().st_ctime, tz=timezone.utc
                    ),
                ),
                trajectory=trajectory,
                placeholders={},
            )
            logger.info(
                f"Successfully loaded and migrated v0.0 cache: {len(trajectory)} steps, 0 placeholders"
            )
            return cache_file
        if isinstance(raw_data, dict) and "metadata" in raw_data:
            # v0.1 format: structured with metadata
            cache_file = CacheFile(**raw_data)
            logger.info(
                f"Successfully loaded v0.1 cache: {len(cache_file.trajectory)} steps, "
                f"{len(cache_file.placeholders)} placeholders"
            )
            if cache_file.metadata.goal:
                logger.debug(f"Cache goal: {cache_file.metadata.goal}")
            return cache_file
        logger.error(
            f"Unknown cache file format in {cache_file_path.name}. "
            "Expected either a list (v0.0) or dict with 'metadata' key (v0.1)."
        )
        raise ValueError(
            f"Unknown cache file format in {cache_file_path}. "
            "Expected either a list (v0.0) or dict with 'metadata' key (v0.1)."
        )
