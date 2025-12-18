import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from askui.models.model_router import ModelRouter
from askui.models.shared.agent_message_param import (
    MessageParam,
    ToolUseBlockParam,
    UsageParam,
)
from askui.models.shared.agent_on_message_cb import OnMessageCbParam
from askui.models.shared.facade import ModelFacade
from askui.models.shared.settings import (
    CacheFile,
    CacheMetadata,
    CacheWriterSettings,
)
from askui.models.shared.tools import ToolCollection
from askui.utils.cache_parameter_handler import CacheParameterHandler

if TYPE_CHECKING:
    from askui.models.models import ActModel

logger = logging.getLogger(__name__)


class CacheWriter:
    def __init__(
        self,
        cache_dir: str = ".cache",
        file_name: str = "",
        cache_writer_settings: CacheWriterSettings | None = None,
        toolbox: ToolCollection | None = None,
        goal: str | None = None,
        model_router: ModelRouter | None = None,
        model: str | None = None,
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
        self._model_router = model_router
        self._model = model
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

        goal_to_save, trajectory_to_save, parameters_dict = (
            self._parameterize_trajectory()
        )

        if self._toolbox is not None:
            trajectory_to_save = self._blank_non_cacheable_tool_inputs(
                trajectory_to_save
            )
        else:
            logger.info("No toolbox set, skipping non-cacheable tool input blanking")

        self._generate_cache_file(
            goal_to_save, trajectory_to_save, parameters_dict, cache_file_path
        )
        self.reset()

    def _parameterize_trajectory(
        self,
    ) -> tuple[str | None, list[ToolUseBlockParam], dict[str, str]]:
        """Identify parameters and return parameterized trajectory + goal."""
        identification_strategy = "preset"
        messages_api = None
        model = None

        if self._cache_writer_settings.parameter_identification_strategy == "llm":
            if self._model_router and self._model:
                try:
                    _get_model: tuple[ActModel, str] = self._model_router._get_model(  # noqa: SLF001
                        self._model, "act"
                    )
                    if isinstance(_get_model[0], ModelFacade):
                        act_model: ActModel = _get_model[0]._act_model  # noqa: SLF001
                    else:
                        act_model = _get_model[0]
                    model_name: str = _get_model[1]
                    if hasattr(act_model, "_messages_api"):
                        messages_api = act_model._messages_api  # noqa: SLF001
                        identification_strategy = "llm"
                        model = model_name
                except Exception:
                    logger.exception(
                        "Using 'llm' for parameter identification caused an exception."
                        "Will use 'preset' strategy instead"
                    )

        return CacheParameterHandler.identify_and_parameterize(
            trajectory=self.messages,
            goal=self._goal,
            identification_strategy=identification_strategy,
            messages_api=messages_api,
            model=model,
        )

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
                    "Blanking input for non-cacheable tool: %s", tool_block.name
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
                "Blanked inputs for %s non-cacheable tool(s) to save space",
                blanked_count,
            )

        return result

    def _generate_cache_file(
        self,
        goal_to_save: str | None,
        trajectory_to_save: list[ToolUseBlockParam],
        parameters_dict: dict[str, str],
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
            cache_parameters=parameters_dict,
        )

        with cache_file_path.open("w", encoding="utf-8") as f:
            json.dump(cache_file.model_dump(mode="json"), f, indent=4)
        logger.info("Cache file successfully written: %s ", cache_file_path)

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
        logger.debug("Reading cache file: %s", cache_file_path)
        with cache_file_path.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Detect format version
        if isinstance(raw_data, list):
            # v0.0 format: just a list of tool use blocks
            logger.info(
                "Detected v0.0 cache format in %s, migrating to v0.1",
                cache_file_path.name,
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
                cache_parameters={},
            )
            logger.info(
                "Successfully loaded and migrated v0.0 cache: %s steps, 0 parameters",
                len(trajectory),
            )
            return cache_file
        if isinstance(raw_data, dict) and "metadata" in raw_data:
            # v0.1 format: structured with metadata
            cache_file = CacheFile(**raw_data)
            logger.info(
                "Successfully loaded v0.1 cache: %s steps, %s parameters",
                len(cache_file.trajectory),
                len(cache_file.cache_parameters),
            )
            if cache_file.metadata.goal:
                logger.debug("Cache goal: %s", cache_file.metadata.goal)
            return cache_file
        logger.error(
            "Unknown cache file format in %s. "
            "Expected either a list (v0.0) or dict with 'metadata' key (v0.1).",
            cache_file_path.name,
        )
        msg = (
            f"Unknown cache file format in {cache_file_path}. "
            "Expected either a list (v0.0) or dict with 'metadata' key (v0.1)."
        )
        raise ValueError(msg)
