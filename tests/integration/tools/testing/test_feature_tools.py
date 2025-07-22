from pathlib import Path

import pytest

from askui.tools.testing.feature_models import (
    FeatureCreateParams,
    FeatureListQuery,
    FeatureModifyParams,
)
from askui.tools.testing.feature_tools import (
    CreateFeatureTool,
    DeleteFeatureTool,
    ListFeatureTool,
    ModifyFeatureTool,
    RetrieveFeatureTool,
)
from askui.utils.api_utils import NotFoundError


@pytest.fixture
def create_tool(tmp_path: Path) -> CreateFeatureTool:
    return CreateFeatureTool(tmp_path)


@pytest.fixture
def retrieve_tool(tmp_path: Path) -> RetrieveFeatureTool:
    return RetrieveFeatureTool(tmp_path)


@pytest.fixture
def list_tool(tmp_path: Path) -> ListFeatureTool:
    return ListFeatureTool(tmp_path)


@pytest.fixture
def modify_tool(tmp_path: Path) -> ModifyFeatureTool:
    return ModifyFeatureTool(tmp_path)


@pytest.fixture
def delete_tool(tmp_path: Path) -> DeleteFeatureTool:
    return DeleteFeatureTool(tmp_path)


def _create_params(
    name: str = "Test Feature",
    description: str | None = "desc",
    tags: list[str] | None = None,
) -> FeatureCreateParams:
    if tags is None:
        tags = ["tag1", "tag2"]
    return FeatureCreateParams(name=name, description=description, tags=tags)


def _modify_params(
    name: str = "Modified Feature",
    description: str | None = "new desc",
    tags: list[str] | None = None,
) -> FeatureModifyParams:
    if tags is None:
        tags = ["tag3"]
    return FeatureModifyParams(name=name, description=description, tags=tags)


def test_create_feature_minimal(create_tool: CreateFeatureTool) -> None:
    params = _create_params(description=None, tags=[])
    feature = create_tool(params)
    assert feature.name == params.name
    assert feature.description is None
    assert feature.tags == []


def test_create_feature_unicode(create_tool: CreateFeatureTool) -> None:
    params = _create_params(name="测试✨", description="描述", tags=["标签"])
    feature = create_tool(params)
    assert feature.name == "测试✨"
    assert feature.description == "描述"
    assert feature.tags == ["标签"]


def test_create_feature_long_name(create_tool: CreateFeatureTool) -> None:
    long_name = "A" * 300
    params = _create_params(name=long_name)
    feature = create_tool(params)
    assert feature.name == long_name


def test_create_duplicate_names(create_tool: CreateFeatureTool) -> None:
    params = _create_params(name="dup")
    f1 = create_tool(params)
    f2 = create_tool(params)
    assert f1.name == f2.name
    assert f1.id != f2.id


def test_retrieve_feature(
    create_tool: CreateFeatureTool, retrieve_tool: RetrieveFeatureTool
) -> None:
    feature = create_tool(_create_params())
    retrieved = retrieve_tool(feature.id)
    assert retrieved.model_dump() == feature.model_dump()


@pytest.mark.parametrize(
    "invalid_id", ["", "notafeatid", "feat_", "123", "feat-123", "feat_!@#"]
)
def test_retrieve_invalid_id(
    retrieve_tool: RetrieveFeatureTool, invalid_id: str
) -> None:
    with pytest.raises(ValueError):
        retrieve_tool(invalid_id)


def test_retrieve_deleted_id(
    create_tool: CreateFeatureTool,
    retrieve_tool: RetrieveFeatureTool,
    delete_tool: DeleteFeatureTool,
) -> None:
    feature = create_tool(_create_params())
    delete_tool(feature.id)
    with pytest.raises(NotFoundError):
        retrieve_tool(feature.id)


def test_list_features_empty(list_tool: ListFeatureTool) -> None:
    result = list_tool(FeatureListQuery())
    assert result.object == "list"
    assert len(result.data) == 0


def test_list_features_multiple(
    create_tool: CreateFeatureTool, list_tool: ListFeatureTool
) -> None:
    f1 = create_tool(_create_params(name="A", tags=["x"]))
    f2 = create_tool(_create_params(name="B", tags=["y"]))
    result = list_tool(FeatureListQuery())
    ids = [f.id for f in result.data]
    assert f1.id in ids and f2.id in ids


def test_list_features_filter_by_tag(
    create_tool: CreateFeatureTool, list_tool: ListFeatureTool
) -> None:
    create_tool(_create_params(name="A", tags=["x"]))
    f2 = create_tool(_create_params(name="B", tags=["y"]))
    result = list_tool(FeatureListQuery(tags=["y"]))
    assert all("y" in f.tags for f in result.data)
    assert any(f.id == f2.id for f in result.data)


def test_modify_feature_partial(
    create_tool: CreateFeatureTool,
    modify_tool: ModifyFeatureTool,
) -> None:
    feature = create_tool(_create_params())
    modified = modify_tool(feature.id, FeatureModifyParams(name="OnlyName"))
    assert modified.name == "OnlyName"
    assert modified.description == feature.description
    assert modified.tags == feature.tags
    # Only tags
    modified2 = modify_tool(feature.id, FeatureModifyParams(tags=["new"]))
    assert modified2.tags == ["new"]
    # Only description
    modified3 = modify_tool(feature.id, FeatureModifyParams(description="desc2"))
    assert modified3.description == "desc2"


def test_modify_feature_invalid_id(modify_tool: ModifyFeatureTool) -> None:
    with pytest.raises(ValueError):
        modify_tool("notafeatid", _modify_params())


def test_modify_feature_noop(
    create_tool: CreateFeatureTool, modify_tool: ModifyFeatureTool
) -> None:
    feature = create_tool(_create_params())
    modified = modify_tool(feature.id, FeatureModifyParams())
    assert modified.model_dump() == feature.model_dump()


def test_delete_feature(
    create_tool: CreateFeatureTool,
    delete_tool: DeleteFeatureTool,
    retrieve_tool: RetrieveFeatureTool,
) -> None:
    feature = create_tool(_create_params())
    delete_tool(feature.id)
    with pytest.raises(NotFoundError):
        retrieve_tool(feature.id)


def test_delete_feature_nonexistent(delete_tool: DeleteFeatureTool) -> None:
    with pytest.raises(NotFoundError):
        delete_tool("feat_nonexistent")


def test_delete_feature_double(
    create_tool: CreateFeatureTool, delete_tool: DeleteFeatureTool
) -> None:
    feature = create_tool(_create_params())
    delete_tool(feature.id)
    with pytest.raises(NotFoundError):
        delete_tool(feature.id)
