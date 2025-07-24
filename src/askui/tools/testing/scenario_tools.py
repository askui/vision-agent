from pathlib import Path

import jsonref
from pydantic import BaseModel, validate_call
from typing_extensions import override

from askui.models.shared.tools import Tool
from askui.utils.api_utils import ListResponse

from .scenario_models import (
    Scenario,
    ScenarioCreateParams,
    ScenarioId,
    ScenarioListQuery,
    ScenarioModifyParams,
)
from .scenario_service import ScenarioService


class CreateScenarioToolInput(BaseModel):
    params: ScenarioCreateParams


class CreateScenarioTool(Tool):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(
            name="create_scenario",
            description="Create a new scenario",
            input_schema=jsonref.replace_refs(
                CreateScenarioToolInput.model_json_schema(),
                lazy_load=False,
                proxies=False,
            ),
        )
        self._service = ScenarioService(base_dir)

    @override
    @validate_call
    def __call__(self, params: ScenarioCreateParams) -> Scenario:
        return self._service.create(params=params)


class RetrieveScenarioToolInput(BaseModel):
    scenario_id: ScenarioId


class RetrieveScenarioTool(Tool):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(
            name="retrieve_scenario",
            description="Retrieve a scenario",
            input_schema=jsonref.replace_refs(
                RetrieveScenarioToolInput.model_json_schema(),
                lazy_load=False,
                proxies=False,
            ),
        )
        self._service = ScenarioService(base_dir)

    @override
    @validate_call
    def __call__(self, scenario_id: ScenarioId) -> Scenario:
        return self._service.retrieve(scenario_id=scenario_id)


class ListScenariosToolInput(BaseModel):
    query: ScenarioListQuery


class ListScenarioTool(Tool):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(
            name="list_scenarios",
            description="List scenarios with optional filtering",
            input_schema=jsonref.replace_refs(
                ListScenariosToolInput.model_json_schema(),
                lazy_load=False,
                proxies=False,
            ),
        )
        self._service = ScenarioService(base_dir)

    @override
    @validate_call
    def __call__(self, query: ScenarioListQuery) -> ListResponse[Scenario]:
        return self._service.list_(query=query)


class ModifyScenarioToolInput(BaseModel):
    scenario_id: ScenarioId
    params: ScenarioModifyParams


class ModifyScenarioTool(Tool):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(
            name="modify_scenario",
            description="Modify an existing scenario",
            input_schema=jsonref.replace_refs(
                ModifyScenarioToolInput.model_json_schema(),
                lazy_load=False,
                proxies=False,
            ),
        )
        self._service = ScenarioService(base_dir)

    @override
    @validate_call
    def __call__(
        self, scenario_id: ScenarioId, params: ScenarioModifyParams
    ) -> Scenario:
        return self._service.modify(scenario_id=scenario_id, params=params)


class DeleteScenarioToolInput(BaseModel):
    scenario_id: ScenarioId


class DeleteScenarioTool(Tool):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(
            name="delete_scenario",
            description="Delete a scenario",
            input_schema=jsonref.replace_refs(
                DeleteScenarioToolInput.model_json_schema(),
                lazy_load=False,
                proxies=False,
            ),
        )
        self._service = ScenarioService(base_dir)

    @override
    @validate_call
    def __call__(self, scenario_id: ScenarioId) -> None:
        self._service.delete(scenario_id=scenario_id)
