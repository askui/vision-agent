from pathlib import Path

from askui.utils.api_utils import ConflictError, ListResponse, NotFoundError

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

    def find(self, query: ScenarioListQuery) -> ListResponse[Scenario]:
        """List all available scenarios.

        Args:
            query (ScenarioListQuery): Query parameters for listing scenarios

        Returns:
            ListResponse[Scenario]: ListResponse containing scenarios sorted by
                creation date
        """
        if not self._scenarios_dir.exists():
            return ListResponse(data=[])

        scenario_files = list(self._scenarios_dir.glob("*.json"))
        scenarios: list[Scenario] = []
        for f in scenario_files:
            with f.open("r", encoding="utf-8") as file:
                scenarios.append(Scenario.model_validate_json(file.read()))

        # Sort by creation date
        scenarios = sorted(
            scenarios, key=lambda s: s.created_at, reverse=(query.order == "desc")
        )

        # Apply before/after filters
        if query.after:
            scenarios = [s for s in scenarios if s.id > query.after]
        if query.before:
            scenarios = [s for s in scenarios if s.id < query.before]

        # Apply limit
        scenarios = scenarios[: query.limit]

        return ListResponse(
            data=scenarios,
            first_id=scenarios[0].id if scenarios else None,
            last_id=scenarios[-1].id if scenarios else None,
            has_more=len(scenario_files) > query.limit,
        )

    def find_one(self, scenario_id: ScenarioId) -> Scenario:
        """Retrieve a scenario by ID.

        Args:
            scenario_id: ID of scenario to retrieve

        Returns:
            Scenario object

        Raises:
            FileNotFoundError: If scenario doesn't exist
        """
        scenario_file = self._scenarios_dir / f"{scenario_id}.json"
        if not scenario_file.exists():
            error_msg = f"Scenario {scenario_id} not found"
            raise FileNotFoundError(error_msg)

        with scenario_file.open("r", encoding="utf-8") as f:
            return Scenario.model_validate_json(f.read())

    def create(self, params: ScenarioCreateParams) -> Scenario:
        scenario = Scenario.create(params)
        scenario_file = self._scenarios_dir / f"{scenario.id}.json"
        if scenario_file.exists():
            error_msg = f"Scenario {scenario.id} already exists"
            raise ConflictError(error_msg)
        scenario_file.write_text(scenario.model_dump_json())
        return scenario

    def modify(self, scenario_id: ScenarioId, params: ScenarioModifyParams) -> Scenario:
        """Modify an existing scenario."""
        scenario = self.find_one(scenario_id)
        modified = scenario.modify(params)
        scenario_file = self._scenarios_dir / f"{scenario_id}.json"
        with scenario_file.open("w", encoding="utf-8") as f:
            f.write(modified.model_dump_json())
        return modified

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
