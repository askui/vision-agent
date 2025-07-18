from pathlib import Path

import pytest

from askui.tools.testing.execution_models import (
    Execution,
    ExecutionCreateParams,
    ExecutionStep,
)
from askui.tools.testing.execution_tools import CreateExecutionTool
from askui.tools.testing.feature_models import Feature, FeatureCreateParams
from askui.tools.testing.feature_tools import CreateFeatureTool
from askui.tools.testing.scenario_models import (
    Scenario,
    ScenarioCreateParams,
    ScenarioExample,
    ScenarioStep,
)
from askui.tools.testing.scenario_tools import CreateScenarioTool


@pytest.fixture
def feature(tmp_path: Path) -> Feature:
    return CreateFeatureTool(tmp_path)(
        params=FeatureCreateParams(name="F", description="d", tags=[])
    )


@pytest.fixture
def scenario(tmp_path: Path, feature: Feature) -> Scenario:
    return CreateScenarioTool(tmp_path)(
        params=ScenarioCreateParams(
            feature=feature.id,
            name="S",
            tags=[],
            steps=[ScenarioStep(keyword="Given", text="foo")],
            examples=[ScenarioExample(name="ex1", parameters={"k": "v"})],
        )
    )


@pytest.fixture
def execution(tmp_path: Path, feature: Feature, scenario: Scenario) -> Execution:
    execution_obj = Execution.create(
        params=ExecutionCreateParams(
            feature=feature.id,
            scenario=scenario.id,
            status="pending",
            steps=[ExecutionStep(keyword="Given", text="foo", status="pending")],
        )
    )
    return CreateExecutionTool(tmp_path)(execution_obj)
