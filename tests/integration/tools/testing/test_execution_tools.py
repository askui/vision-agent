from pathlib import Path

import pytest

from askui.tools.testing.execution_models import (
    Execution,
    ExecutionCreateParams,
    ExecutionListQuery,
    ExecutionModifyParams,
    ExecutionStatus,
    ExecutionStep,
)
from askui.tools.testing.execution_tools import (
    CreateExecutionTool,
    DeleteExecutionTool,
    ListExecutionTool,
    ModifyExecutionTool,
    RetrieveExecutionTool,
)
from askui.tools.testing.feature_models import Feature
from askui.tools.testing.scenario_models import Scenario
from askui.utils.api_utils import NotFoundError


@pytest.fixture
def create_tool(tmp_path: Path) -> CreateExecutionTool:
    return CreateExecutionTool(tmp_path)


@pytest.fixture
def retrieve_tool(tmp_path: Path) -> RetrieveExecutionTool:
    return RetrieveExecutionTool(tmp_path)


@pytest.fixture
def list_tool(tmp_path: Path) -> ListExecutionTool:
    return ListExecutionTool(tmp_path)


@pytest.fixture
def modify_tool(tmp_path: Path) -> ModifyExecutionTool:
    return ModifyExecutionTool(tmp_path)


@pytest.fixture
def delete_tool(tmp_path: Path) -> DeleteExecutionTool:
    return DeleteExecutionTool(tmp_path)


def _create_execution(
    scenario: Scenario,
    feature_id: str,
    status: ExecutionStatus = "pending",
    steps: list[ExecutionStep] | None = None,
) -> Execution:
    if steps is None:
        _steps = [ExecutionStep(keyword="Given", text="foo", status="pending")]
    else:
        _steps = steps
    return Execution.create(
        params=ExecutionCreateParams(
            feature=feature_id,
            scenario=scenario.id,
            status=status,
            steps=_steps,
        )
    )


def test_create_execution_minimal(
    create_tool: CreateExecutionTool, scenario: Scenario, feature: Feature
) -> None:
    execution_obj = _create_execution(scenario, feature.id, steps=[])
    execution = create_tool(execution_obj)
    assert execution.status == "pending"
    assert execution.steps == []


def test_create_execution_unicode(
    create_tool: CreateExecutionTool, scenario: Scenario, feature: Feature
) -> None:
    step = ExecutionStep(keyword="Given", text="测试✨", status="pending")
    execution_obj = _create_execution(scenario, feature.id, steps=[step])
    execution = create_tool(execution_obj)
    assert execution.steps[0].text == "测试✨"


def test_create_execution_long_text(
    create_tool: CreateExecutionTool, scenario: Scenario, feature: Feature
) -> None:
    long_text = "A" * 300
    step = ExecutionStep(keyword="Given", text=long_text, status="pending")
    execution_obj = _create_execution(scenario, feature.id, steps=[step])
    execution = create_tool(execution_obj)
    assert execution.steps[0].text == long_text


def test_retrieve_execution(
    create_tool: CreateExecutionTool,
    retrieve_tool: RetrieveExecutionTool,
    scenario: Scenario,
    feature: Feature,
) -> None:
    execution_obj = _create_execution(scenario, feature.id)
    execution = create_tool(execution_obj)
    retrieved = retrieve_tool(execution.id)
    assert retrieved.model_dump() == execution.model_dump()


@pytest.mark.parametrize(
    "invalid_id", ["", "notanexecid", "exec_", "123", "exec-123", "exec_!@#"]
)
def test_retrieve_invalid_id(
    retrieve_tool: RetrieveExecutionTool, invalid_id: str
) -> None:
    with pytest.raises(ValueError):
        retrieve_tool(invalid_id)


def test_retrieve_deleted_id(
    create_tool: CreateExecutionTool,
    retrieve_tool: RetrieveExecutionTool,
    delete_tool: DeleteExecutionTool,
    scenario: Scenario,
    feature: Feature,
) -> None:
    execution_obj = _create_execution(scenario, feature.id)
    execution = create_tool(execution_obj)
    delete_tool(execution.id)
    with pytest.raises(NotFoundError):
        retrieve_tool(execution.id)


def test_list_executions_empty(list_tool: ListExecutionTool) -> None:
    result = list_tool(ExecutionListQuery())
    assert result.object == "list"
    assert len(result.data) == 0


def test_list_executions_multiple(
    create_tool: CreateExecutionTool,
    list_tool: ListExecutionTool,
    scenario: Scenario,
    feature: Feature,
) -> None:
    e1 = create_tool(_create_execution(scenario, feature.id, status="pending"))
    e2 = create_tool(_create_execution(scenario, feature.id, status="passed"))
    result = list_tool(ExecutionListQuery())
    ids = [e.id for e in result.data]
    assert e1.id in ids and e2.id in ids


def test_list_executions_filter_by_feature(
    create_tool: CreateExecutionTool,
    list_tool: ListExecutionTool,
    scenario: Scenario,
    feature: Feature,
) -> None:
    e1 = create_tool(_create_execution(scenario, feature.id, status="pending"))
    # Create an execution for a different feature
    other_feature_id = "feat_other"
    create_tool(_create_execution(scenario, other_feature_id, status="pending"))
    result = list_tool(ExecutionListQuery(feature=feature.id))
    assert all(e.feature == feature.id for e in result.data)
    assert any(e.id == e1.id for e in result.data)


def test_modify_execution_partial(
    create_tool: CreateExecutionTool,
    modify_tool: ModifyExecutionTool,
    scenario: Scenario,
    feature: Feature,
) -> None:
    execution = create_tool(_create_execution(scenario, feature.id))
    modified = modify_tool(execution.id, ExecutionModifyParams(status="passed"))
    assert modified.status == "passed"
    # Only steps
    new_steps = [ExecutionStep(keyword="Then", text="done", status="passed")]
    modified2 = modify_tool(execution.id, ExecutionModifyParams(steps=new_steps))
    assert len(modified2.steps) == len(new_steps)
    assert all(
        s.keyword == n.keyword for s, n in zip(modified2.steps, new_steps, strict=False)
    )
    assert all(
        s.text == n.text for s, n in zip(modified2.steps, new_steps, strict=False)
    )


def test_modify_execution_invalid_id(modify_tool: ModifyExecutionTool) -> None:
    with pytest.raises(ValueError):
        modify_tool("notanexecid", ExecutionModifyParams(status="passed"))


def test_modify_execution_noop(
    create_tool: CreateExecutionTool,
    modify_tool: ModifyExecutionTool,
    scenario: Scenario,
    feature: Feature,
) -> None:
    execution = create_tool(_create_execution(scenario, feature.id))
    modified = modify_tool(execution.id, ExecutionModifyParams())
    assert modified.model_dump() == execution.model_dump()


def test_delete_execution(
    create_tool: CreateExecutionTool,
    delete_tool: DeleteExecutionTool,
    retrieve_tool: RetrieveExecutionTool,
    scenario: Scenario,
    feature: Feature,
) -> None:
    execution = create_tool(_create_execution(scenario, feature.id))
    delete_tool(execution.id)
    with pytest.raises(NotFoundError):
        retrieve_tool(execution.id)


def test_delete_execution_nonexistent(delete_tool: DeleteExecutionTool) -> None:
    with pytest.raises(NotFoundError):
        delete_tool("exec_nonexistent")


def test_delete_execution_double(
    create_tool: CreateExecutionTool,
    delete_tool: DeleteExecutionTool,
    scenario: Scenario,
    feature: Feature,
) -> None:
    execution = create_tool(_create_execution(scenario, feature.id))
    delete_tool(execution.id)
    with pytest.raises(NotFoundError):
        delete_tool(execution.id)
