import pytest

from askui.models.models import ModelComposition, ModelDefinition

MODEL_DEFINITIONS = {
    "e2e_ocr": ModelDefinition(
        task="e2e_ocr",
        architecture="easy_ocr",
        version="1",
        interface="online_learning",
        use_case="test_workspace",
        tags=["trained"],
    ),
    "od": ModelDefinition(
        task="od",
        architecture="yolo",
        version="789012",
        interface="offline_learning",
        use_case="test_workspace2",
    ),
}


def test_model_composition_initialization() -> None:
    composition = ModelComposition([MODEL_DEFINITIONS["e2e_ocr"]])
    assert len(composition.root) == 1
    assert (
        composition.root[0].model_name
        == "e2e_ocr-easy_ocr-online_learning-test_workspace-1-trained"
    )


def test_model_composition_initialization_with_multiple_models() -> None:
    composition = ModelComposition(
        [MODEL_DEFINITIONS["e2e_ocr"], MODEL_DEFINITIONS["od"]]
    )
    assert len(composition.root) == 2
    assert (
        composition.root[0].model_name
        == "e2e_ocr-easy_ocr-online_learning-test_workspace-1-trained"
    )
    assert (
        composition.root[1].model_name
        == "od-yolo-offline_learning-test_workspace2-789012"
    )


def test_model_composition_serialization() -> None:
    model_def = MODEL_DEFINITIONS["e2e_ocr"]
    composition = ModelComposition([model_def])
    serialized = composition.model_dump(by_alias=True)
    assert isinstance(serialized, list)
    assert len(serialized) == 1
    assert serialized[0]["task"] == "e2e_ocr"
    assert serialized[0]["architecture"] == "easy_ocr"
    assert serialized[0]["version"] == "1"
    assert serialized[0]["interface"] == "online_learning"
    assert serialized[0]["useCase"] == "test_workspace"
    assert serialized[0]["tags"] == ["trained"]


def test_model_composition_serialization_with_multiple_models() -> None:
    composition = ModelComposition(
        [MODEL_DEFINITIONS["e2e_ocr"], MODEL_DEFINITIONS["od"]]
    )
    serialized = composition.model_dump(by_alias=True)
    assert isinstance(serialized, list)
    assert len(serialized) == 2
    assert serialized[0]["task"] == "e2e_ocr"
    assert serialized[1]["task"] == "od"


def test_model_composition_validation_with_invalid_task() -> None:
    with pytest.raises(ValueError):
        ModelComposition(
            [
                {  # type: ignore
                    "task": "invalid task!",
                    "architecture": "easy_ocr",
                    "version": "123456",
                    "interface": "online_learning",
                    "useCase": "test_workspace",
                }
            ]
        )


def test_model_composition_validation_with_invalid_version() -> None:
    with pytest.raises(ValueError):
        ModelComposition(
            [
                {  # type: ignore
                    "task": "e2e_ocr",
                    "architecture": "easy_ocr",
                    "version": "invalid",
                    "interface": "online_learning",
                    "useCase": "test_workspace",
                }
            ]
        )


def test_model_composition_with_empty_tags_and_use_case() -> None:
    model_def = ModelDefinition(
        **{
            **MODEL_DEFINITIONS["e2e_ocr"].model_dump(exclude={"tags", "use_case"}),
            "tags": [],
        }
    )
    composition = ModelComposition([model_def])
    assert (
        composition.root[0].model_name
        == "e2e_ocr-easy_ocr-online_learning-00000000_0000_0000_0000_000000000000-1"
    )
