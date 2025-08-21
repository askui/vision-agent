from pathlib import Path

from askui.chat.api.assistants.models import (
    Assistant,
    AssistantCreateParams,
    AssistantModifyParams,
)
from askui.chat.api.assistants.seeds import SEEDS
from askui.chat.api.models import AssistantId
from askui.utils.api_utils import (
    ConflictError,
    ListQuery,
    ListResponse,
    NotFoundError,
    list_resources,
)


class AssistantService:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._assistants_dir = base_dir / "assistants"

    def _get_assistant_path(self, assistant_id: AssistantId, new: bool = False) -> Path:
        assistant_path = self._assistants_dir / f"{assistant_id}.json"
        exists = assistant_path.exists()
        if new and exists:
            error_msg = f"Assistant {assistant_id} already exists"
            raise ConflictError(error_msg)
        if not new and not exists:
            error_msg = f"Assistant {assistant_id} not found"
            raise NotFoundError(error_msg)
        return assistant_path

    def list_(self, query: ListQuery) -> ListResponse[Assistant]:
        return list_resources(self._assistants_dir, query, Assistant)

    def retrieve(self, assistant_id: AssistantId) -> Assistant:
        try:
            assistant_path = self._get_assistant_path(assistant_id)
            return Assistant.model_validate_json(assistant_path.read_text())
        except FileNotFoundError as e:
            error_msg = f"Assistant {assistant_id} not found"
            raise NotFoundError(error_msg) from e

    def create(self, params: AssistantCreateParams) -> Assistant:
        assistant = Assistant.create(params)
        self._save(assistant, new=True)
        return assistant

    def modify(
        self, assistant_id: AssistantId, params: AssistantModifyParams
    ) -> Assistant:
        assistant = self.retrieve(assistant_id)
        modified = assistant.modify(params)
        self._save(modified)
        return modified

    def delete(self, assistant_id: AssistantId) -> None:
        try:
            self._get_assistant_path(assistant_id).unlink()
        except FileNotFoundError as e:
            error_msg = f"Assistant {assistant_id} not found"
            raise NotFoundError(error_msg) from e

    def _save(self, assistant: Assistant, new: bool = False) -> None:
        self._assistants_dir.mkdir(parents=True, exist_ok=True)
        assistant_file = self._get_assistant_path(assistant.id, new=new)
        assistant_file.write_text(assistant.model_dump_json(), encoding="utf-8")

    def seed(self) -> None:
        """Seed the assistant service with default assistants."""
        for seed in SEEDS:
            try:
                self._save(seed, new=True)
            except ConflictError:  # noqa: PERF203
                self._save(seed)
