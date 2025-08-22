from pathlib import Path
from typing import Callable

from askui.utils.api_utils import (
    ConflictError,
    ListResponse,
    NotFoundError,
    list_resources,
)
from askui.utils.not_given import NOT_GIVEN

from .scenario_models import (
    Scenario,
    ScenarioCreateParams,
    ScenarioId,
    ScenarioListQuery,
    ScenarioModifyParams,
)


def _build_scenario_filter_fn(
    query: ScenarioListQuery,
) -> Callable[[Scenario], bool]:
    def filter_fn(scenario: Scenario) -> bool:
        tags_matched = query.tags == NOT_GIVEN or any(
            tag in scenario.tags for tag in query.tags
        )
        feature_matched = (
            query.feature is NOT_GIVEN or scenario.feature == query.feature
        )
        return tags_matched and feature_matched

    return filter_fn


class ScenarioService:
    """Service for managing Scenario resources with filesystem persistence."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._scenarios_dir = base_dir / "scenarios"

    def _get_scenario_path(self, scenario_id: ScenarioId, new: bool = False) -> Path:
        scenario_path = self._scenarios_dir / f"{scenario_id}.json"
        exists = scenario_path.exists()
        if new and exists:
            error_msg = f"Scenario {scenario_id} already exists"
            raise ConflictError(error_msg)
        if not new and not exists:
            error_msg = f"Scenario {scenario_id} not found"
            raise NotFoundError(error_msg)
        return scenario_path

    def list_(self, query: ScenarioListQuery) -> ListResponse[Scenario]:
        return list_resources(
            base_dir=self._scenarios_dir,
            query=query,
            resource_type=Scenario,
            filter_fn=_build_scenario_filter_fn(query),
        )

    def retrieve(self, scenario_id: ScenarioId) -> Scenario:
        try:
            scenario_path = self._get_scenario_path(scenario_id)
            return Scenario.model_validate_json(scenario_path.read_text())
        except FileNotFoundError as e:
            error_msg = f"Scenario {scenario_id} not found"
            raise NotFoundError(error_msg) from e

    def create(self, params: ScenarioCreateParams) -> Scenario:
        scenario = Scenario.create(params)
        self._save(scenario, new=True)
        return scenario

    def modify(self, scenario_id: ScenarioId, params: ScenarioModifyParams) -> Scenario:
        scenario = self.retrieve(scenario_id)
        modified = scenario.modify(params)
        return self._save(modified)

    def delete(self, scenario_id: ScenarioId) -> None:
        try:
            self._get_scenario_path(scenario_id).unlink()
        except FileNotFoundError as e:
            error_msg = f"Scenario {scenario_id} not found"
            raise NotFoundError(error_msg) from e

    def _save(self, scenario: Scenario, new: bool = False) -> Scenario:
        self._scenarios_dir.mkdir(parents=True, exist_ok=True)
        scenario_file = self._get_scenario_path(scenario.id, new=new)
        scenario_file.write_text(scenario.model_dump_json(), encoding="utf-8")
        return scenario
