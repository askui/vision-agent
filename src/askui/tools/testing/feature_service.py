from pathlib import Path
from typing import Callable

from askui.utils.api_utils import (
    ConflictError,
    ListResponse,
    NotFoundError,
    list_resources,
)
from askui.utils.not_given import NOT_GIVEN

from .feature_models import (
    Feature,
    FeatureCreateParams,
    FeatureId,
    FeatureListQuery,
    FeatureModifyParams,
)


def _build_feature_filter_fn(
    query: FeatureListQuery,
) -> Callable[[Feature], bool]:
    def filter_fn(feature: Feature) -> bool:
        return query.tags == NOT_GIVEN or any(tag in feature.tags for tag in query.tags)

    return filter_fn


class FeatureService:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._features_dir = base_dir / "features"

    def _get_feature_path(self, feature_id: FeatureId, new: bool = False) -> Path:
        feature_path = self._features_dir / f"{feature_id}.json"
        exists = feature_path.exists()
        if new and exists:
            error_msg = f"Feature {feature_id} already exists"
            raise ConflictError(error_msg)
        if not new and not exists:
            error_msg = f"Feature {feature_id} not found"
            raise NotFoundError(error_msg)
        return feature_path

    def list_(
        self,
        query: FeatureListQuery,
    ) -> ListResponse[Feature]:
        return list_resources(
            base_dir=self._features_dir,
            query=query,
            resource_type=Feature,
            filter_fn=_build_feature_filter_fn(query),
        )

    def retrieve(self, feature_id: FeatureId) -> Feature:
        try:
            feature_path = self._get_feature_path(feature_id)
            return Feature.model_validate_json(feature_path.read_text())
        except FileNotFoundError as e:
            error_msg = f"Feature {feature_id} not found"
            raise NotFoundError(error_msg) from e

    def create(self, params: FeatureCreateParams) -> Feature:
        feature = Feature.create(params)
        self._save(feature, new=True)
        return feature

    def modify(self, feature_id: FeatureId, params: FeatureModifyParams) -> Feature:
        feature = self.retrieve(feature_id)
        modified = feature.modify(params)
        self._save(modified)
        return modified

    def delete(self, feature_id: FeatureId) -> None:
        try:
            self._get_feature_path(feature_id).unlink()
        except FileNotFoundError as e:
            error_msg = f"Feature {feature_id} not found"
            raise NotFoundError(error_msg) from e

    def _save(self, feature: Feature, new: bool = False) -> None:
        self._features_dir.mkdir(parents=True, exist_ok=True)
        feature_file = self._get_feature_path(feature.id, new=new)
        feature_file.write_text(feature.model_dump_json(), encoding="utf-8")
