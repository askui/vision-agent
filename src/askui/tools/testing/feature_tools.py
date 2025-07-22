from pathlib import Path

import jsonref
from pydantic import BaseModel, validate_call
from typing_extensions import override

from askui.models.shared.tools import Tool
from askui.utils.api_utils import ListResponse

from .feature_models import (
    Feature,
    FeatureCreateParams,
    FeatureId,
    FeatureListQuery,
    FeatureModifyParams,
)
from .feature_service import FeatureService


class CreateFeatureToolInput(BaseModel):
    params: FeatureCreateParams


class CreateFeatureTool(Tool):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(
            name="create_feature",
            description="Create a new feature",
            input_schema=jsonref.replace_refs(
                CreateFeatureToolInput.model_json_schema(),
                lazy_load=False,
                proxies=False,
            ),
        )
        self._service = FeatureService(base_dir)

    @override
    @validate_call
    def __call__(self, params: FeatureCreateParams) -> Feature:
        return self._service.create(params=params)


class RetrieveFeatureToolInput(BaseModel):
    feature_id: FeatureId


class RetrieveFeatureTool(Tool):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(
            name="retrieve_feature",
            description="Retrieve a feature",
            input_schema=jsonref.replace_refs(
                RetrieveFeatureToolInput.model_json_schema(),
                lazy_load=False,
                proxies=False,
            ),
        )
        self._service = FeatureService(base_dir)

    @override
    @validate_call
    def __call__(self, feature_id: FeatureId) -> Feature:
        return self._service.retrieve(feature_id=feature_id)


class ListFeatureToolInput(BaseModel):
    query: FeatureListQuery


class ListFeatureTool(Tool):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(
            name="list_features",
            description="List features with optional filtering",
            input_schema=jsonref.replace_refs(
                ListFeatureToolInput.model_json_schema(),
                lazy_load=False,
                proxies=False,
            ),
        )
        self._service = FeatureService(base_dir)

    @override
    @validate_call
    def __call__(self, query: FeatureListQuery) -> ListResponse[Feature]:
        return self._service.list_(query=query)


class ModifyFeatureToolInput(BaseModel):
    feature_id: FeatureId
    params: FeatureModifyParams


class ModifyFeatureTool(Tool):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(
            name="modify_feature",
            description="Modify an existing feature",
            input_schema=jsonref.replace_refs(
                ModifyFeatureToolInput.model_json_schema(),
                lazy_load=False,
                proxies=False,
            ),
        )
        self._service = FeatureService(base_dir)

    @override
    @validate_call
    def __call__(self, feature_id: FeatureId, params: FeatureModifyParams) -> Feature:
        return self._service.modify(feature_id=feature_id, params=params)


class DeleteFeatureToolInput(BaseModel):
    feature_id: FeatureId


class DeleteFeatureTool(Tool):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(
            name="delete_feature",
            description="Delete a feature",
            input_schema=jsonref.replace_refs(
                DeleteFeatureToolInput.model_json_schema(),
                lazy_load=False,
                proxies=False,
            ),
        )
        self._service = FeatureService(base_dir)

    @override
    @validate_call
    def __call__(self, feature_id: FeatureId) -> None:
        self._service.delete(feature_id=feature_id)
