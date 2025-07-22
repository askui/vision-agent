from pathlib import Path

from pydantic import ValidationError

from askui.utils.api_utils import (
    ConflictError,
    ListResponse,
    NotFoundError,
    list_resource_paths,
)
from askui.utils.not_given import NOT_GIVEN

from .scenario_models import (
    Scenario,
    ScenarioCreateParams,
    ScenarioId,
    ScenarioListQuery,
    ScenarioModifyParams,
)


class ScenarioService:
    """
    Service for managing Scenario resources with filesystem persistence.

    Args:
        base_dir (Path): Base directory for storing scenario data.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._scenarios_dir = base_dir / "scenarios"
        self._scenarios_dir.mkdir(parents=True, exist_ok=True)

    def list_(
        self,
        query: ScenarioListQuery,
    ) -> ListResponse[Scenario]:
        scenario_paths = list_resource_paths(self._scenarios_dir, query)
        scenarios: list[Scenario] = []
        for f in scenario_paths:
            try:
                scenario = Scenario.model_validate_json(f.read_text())
                tags_matched = query.tags == NOT_GIVEN or any(
                    tag in scenario.tags for tag in query.tags
                )
                feature_matched = (
                    query.feature is NOT_GIVEN or scenario.feature == query.feature
                )
                if tags_matched and feature_matched:
                    scenarios.append(scenario)
            except ValidationError:  # noqa: PERF203
                continue
        has_more = len(scenarios) > query.limit
        scenarios = scenarios[: query.limit]
        return ListResponse(
            data=scenarios,
            first_id=scenarios[0].id if scenarios else None,
            last_id=scenarios[-1].id if scenarios else None,
            has_more=has_more,
        )

    def retrieve(self, scenario_id: ScenarioId) -> Scenario:
        scenario_file = self._scenarios_dir / f"{scenario_id}.json"
        if not scenario_file.exists():
            error_msg = f"Scenario {scenario_id} not found"
            raise NotFoundError(error_msg)
        return Scenario.model_validate_json(scenario_file.read_text())

    def create(self, params: ScenarioCreateParams) -> Scenario:
        scenario = Scenario.create(params)
        scenario_file = self._scenarios_dir / f"{scenario.id}.json"
        if scenario_file.exists():
            error_msg = f"Scenario {scenario.id} already exists"
            raise ConflictError(error_msg)
        scenario_file.write_text(scenario.model_dump_json())
        return scenario

    def modify(self, scenario_id: ScenarioId, params: ScenarioModifyParams) -> Scenario:
        scenario = self.retrieve(scenario_id)
        updated = scenario.modify(params)
        return self._save(updated)

    def _save(self, scenario: Scenario) -> Scenario:
        scenario_file = self._scenarios_dir / f"{scenario.id}.json"
        scenario_file.write_text(scenario.model_dump_json())
        return scenario

    def delete(self, scenario_id: ScenarioId) -> None:
        scenario_file = self._scenarios_dir / f"{scenario_id}.json"
        if not scenario_file.exists():
            error_msg = f"Scenario {scenario_id} not found"
            raise NotFoundError(error_msg)
        scenario_file.unlink()
