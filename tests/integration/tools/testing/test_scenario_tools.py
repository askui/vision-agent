from pathlib import Path

import pytest

from askui.tools.testing.feature_models import Feature
from askui.tools.testing.scenario_models import (
    ScenarioCreateParams,
    ScenarioExample,
    ScenarioListQuery,
    ScenarioModifyParams,
    ScenarioStep,
)
from askui.tools.testing.scenario_tools import (
    CreateScenarioTool,
    DeleteScenarioTool,
    ListScenarioTool,
    ModifyScenarioTool,
    RetrieveScenarioTool,
)
from askui.utils.api_utils import NotFoundError


@pytest.fixture
def create_tool(tmp_path: Path) -> CreateScenarioTool:
    return CreateScenarioTool(tmp_path)


@pytest.fixture
def retrieve_tool(tmp_path: Path) -> RetrieveScenarioTool:
    return RetrieveScenarioTool(tmp_path)


@pytest.fixture
def list_tool(tmp_path: Path) -> ListScenarioTool:
    return ListScenarioTool(tmp_path)


@pytest.fixture
def modify_tool(tmp_path: Path) -> ModifyScenarioTool:
    return ModifyScenarioTool(tmp_path)


@pytest.fixture
def delete_tool(tmp_path: Path) -> DeleteScenarioTool:
    return DeleteScenarioTool(tmp_path)


def _create_params(
    feature_id: str,
    name: str = "Test Scenario",
    tags: list[str] | None = None,
    steps: list[ScenarioStep] | None = None,
    examples: list[ScenarioExample] | None = None,
) -> ScenarioCreateParams:
    if tags is None:
        tags = ["tag1"]
    if steps is None:
        steps = [ScenarioStep(keyword="Given", text="something")]
    if examples is None:
        examples = [ScenarioExample(name="ex1", parameters={"k": "v"})]
    return ScenarioCreateParams(
        feature=feature_id,
        name=name,
        tags=tags,
        steps=steps,
        examples=examples,
    )


def _modify_params(
    name: str = "Modified Scenario",
    tags: list[str] | None = None,
    steps: list[ScenarioStep] | None = None,
    examples: list[ScenarioExample] | None = None,
) -> ScenarioModifyParams:
    if tags is None:
        tags = ["tag2"]
    if steps is None:
        steps = [ScenarioStep(keyword="Then", text="changed")]
    if examples is None:
        examples = []
    return ScenarioModifyParams(name=name, tags=tags, steps=steps, examples=examples)


def test_create_scenario_minimal(
    create_tool: CreateScenarioTool, feature: Feature
) -> None:
    params = _create_params(
        feature.id,
        tags=[],
        examples=[],
        steps=[ScenarioStep(keyword="Given", text="foo")],
    )
    scenario = create_tool(params)
    assert scenario.name == params.name
    assert scenario.tags == []
    assert scenario.examples == []
    assert scenario.steps == params.steps


def test_create_scenario_unicode(
    create_tool: CreateScenarioTool, feature: Feature
) -> None:
    params = _create_params(
        feature.id, name="测试✨", steps=[ScenarioStep(keyword="Given", text="步骤")]
    )
    scenario = create_tool(params)
    assert scenario.name == "测试✨"
    assert scenario.steps[0].text == "步骤"


def test_create_scenario_long_name(
    create_tool: CreateScenarioTool, feature: Feature
) -> None:
    long_name = "S" * 300
    params = _create_params(feature.id, name=long_name)
    scenario = create_tool(params)
    assert scenario.name == long_name


def test_create_scenario_empty_steps(
    create_tool: CreateScenarioTool, feature: Feature
) -> None:
    params = _create_params(feature.id, steps=[])
    scenario = create_tool(params)
    assert scenario.steps == []


def test_create_scenario_multiple_steps(
    create_tool: CreateScenarioTool, feature: Feature
) -> None:
    steps = [
        ScenarioStep(keyword="Given", text="a"),
        ScenarioStep(keyword="When", text="b"),
    ]
    params = _create_params(feature.id, steps=steps)
    scenario = create_tool(params)
    assert scenario.steps == steps


def test_retrieve_scenario(
    create_tool: CreateScenarioTool,
    retrieve_tool: RetrieveScenarioTool,
    feature: Feature,
) -> None:
    scenario = create_tool(_create_params(feature.id))
    retrieved = retrieve_tool(scenario.id)
    assert retrieved.model_dump() == scenario.model_dump()


@pytest.mark.parametrize(
    "invalid_id", ["", "notascenid", "scen_", "123", "scen-123", "scen_!@#"]
)
def test_retrieve_invalid_id(
    retrieve_tool: RetrieveScenarioTool, invalid_id: str
) -> None:
    with pytest.raises(ValueError):
        retrieve_tool(invalid_id)


def test_retrieve_deleted_id(
    create_tool: CreateScenarioTool,
    retrieve_tool: RetrieveScenarioTool,
    delete_tool: DeleteScenarioTool,
    feature: Feature,
) -> None:
    scenario = create_tool(_create_params(feature.id))
    delete_tool(scenario.id)
    with pytest.raises(NotFoundError):
        retrieve_tool(scenario.id)


def test_list_scenarios_empty(list_tool: ListScenarioTool) -> None:
    result = list_tool(ScenarioListQuery())
    assert result.object == "list"
    assert len(result.data) == 0


def test_list_scenarios_multiple(
    create_tool: CreateScenarioTool, list_tool: ListScenarioTool, feature: Feature
) -> None:
    s1 = create_tool(_create_params(feature.id, name="A", tags=["x"]))
    s2 = create_tool(_create_params(feature.id, name="B", tags=["y"]))
    result = list_tool(ScenarioListQuery())
    ids = [s.id for s in result.data]
    assert s1.id in ids and s2.id in ids


def test_list_scenarios_filter_by_tag(
    create_tool: CreateScenarioTool, list_tool: ListScenarioTool, feature: Feature
) -> None:
    create_tool(_create_params(feature.id, name="A", tags=["x"]))
    s2 = create_tool(_create_params(feature.id, name="B", tags=["y"]))
    result = list_tool(ScenarioListQuery(tags=["y"]))
    assert all("y" in s.tags for s in result.data)
    assert any(s.id == s2.id for s in result.data)


def test_list_scenarios_filter_by_feature(
    create_tool: CreateScenarioTool, list_tool: ListScenarioTool, feature: Feature
) -> None:
    s1 = create_tool(_create_params(feature.id, name="A"))
    # Create a scenario for a different feature
    other_feature_id = "feat_other"
    create_tool(_create_params(other_feature_id, name="B"))
    result = list_tool(ScenarioListQuery(feature=feature.id))
    assert all(s.feature == feature.id for s in result.data)
    assert any(s.id == s1.id for s in result.data)


def test_modify_scenario_partial(
    create_tool: CreateScenarioTool,
    modify_tool: ModifyScenarioTool,
    feature: Feature,
) -> None:
    scenario = create_tool(_create_params(feature.id))
    modified = modify_tool(scenario.id, ScenarioModifyParams(name="OnlyName"))
    assert modified.name == "OnlyName"
    assert modified.tags == scenario.tags
    # Only tags
    modified2 = modify_tool(scenario.id, ScenarioModifyParams(tags=["new"]))
    assert modified2.tags == ["new"]
    # Only steps
    new_steps = [ScenarioStep(keyword="Then", text="done")]
    modified3 = modify_tool(scenario.id, ScenarioModifyParams(steps=new_steps))
    assert len(modified3.steps) == len(new_steps)
    assert all(
        s.keyword == n.keyword for s, n in zip(modified3.steps, new_steps, strict=False)
    )
    assert all(
        s.text == n.text for s, n in zip(modified3.steps, new_steps, strict=False)
    )


def test_modify_scenario_invalid_id(modify_tool: ModifyScenarioTool) -> None:
    with pytest.raises(ValueError):
        modify_tool("notascenid", _modify_params())


def test_modify_scenario_noop(
    create_tool: CreateScenarioTool, modify_tool: ModifyScenarioTool, feature: Feature
) -> None:
    scenario = create_tool(_create_params(feature.id))
    modified = modify_tool(scenario.id, ScenarioModifyParams())
    assert modified.model_dump() == scenario.model_dump()


def test_delete_scenario(
    create_tool: CreateScenarioTool,
    delete_tool: DeleteScenarioTool,
    retrieve_tool: RetrieveScenarioTool,
    feature: Feature,
) -> None:
    scenario = create_tool(_create_params(feature.id))
    delete_tool(scenario.id)
    with pytest.raises(NotFoundError):
        retrieve_tool(scenario.id)


def test_delete_scenario_nonexistent(delete_tool: DeleteScenarioTool) -> None:
    with pytest.raises(NotFoundError):
        delete_tool("scen_nonexistent")


def test_delete_scenario_double(
    create_tool: CreateScenarioTool, delete_tool: DeleteScenarioTool, feature: Feature
) -> None:
    scenario = create_tool(_create_params(feature.id))
    delete_tool(scenario.id)
    with pytest.raises(NotFoundError):
        delete_tool(scenario.id)
