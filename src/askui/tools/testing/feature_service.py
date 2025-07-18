from pathlib import Path

from pydantic import ValidationError

from askui.utils.api_utils import (
    ConflictError,
    ListResponse,
    NotFoundError,
    list_resource_paths,
)
from askui.utils.not_given import NOT_GIVEN

from .feature_models import (
    Feature,
    FeatureCreateParams,
    FeatureId,
    FeatureListQuery,
    FeatureModifyParams,
)


class FeatureService:
    """
    Service for managing Feature resources with filesystem persistence.

    Args:
        base_dir (Path): Base directory for storing feature data.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._features_dir = base_dir / "features"
        self._features_dir.mkdir(parents=True, exist_ok=True)

    def list_(
        self,
        query: FeatureListQuery,
    ) -> ListResponse[Feature]:
        feature_paths = list_resource_paths(self._features_dir, query)
        features: list[Feature] = []
        for f in feature_paths:
            try:
                feature = Feature.model_validate_json(f.read_text())
                if query.tags == NOT_GIVEN or any(
                    tag in feature.tags for tag in query.tags
                ):
                    features.append(feature)
            except ValidationError:  # noqa: PERF203
                continue
        has_more = len(features) > query.limit
        features = features[: query.limit]
        return ListResponse(
            data=features,
            first_id=features[0].id if features else None,
            last_id=features[-1].id if features else None,
            has_more=has_more,
        )

    def retrieve(self, feature_id: FeatureId) -> Feature:
        feature_file = self._features_dir / f"{feature_id}.json"
        if not feature_file.exists():
            error_msg = f"Feature {feature_id} not found"
            raise NotFoundError(error_msg)
        return Feature.model_validate_json(feature_file.read_text())

    def create(self, params: FeatureCreateParams) -> Feature:
        feature = Feature.create(params)
        feature_file = self._features_dir / f"{feature.id}.json"
        if feature_file.exists():
            error_msg = f"Feature {feature.id} already exists"
            raise ConflictError(error_msg)
        feature_file.write_text(feature.model_dump_json())
        return feature

    def modify(self, feature_id: FeatureId, params: FeatureModifyParams) -> Feature:
        feature = self.retrieve(feature_id)
        modified = feature.modify(params)
        feature_file = self._features_dir / f"{feature_id}.json"
        feature_file.write_text(modified.model_dump_json())
        return modified

    def delete(self, feature_id: FeatureId) -> None:
        feature_file = self._features_dir / f"{feature_id}.json"
        if not feature_file.exists():
            error_msg = f"Feature {feature_id} not found"
            raise NotFoundError(error_msg)
        feature_file.unlink()
