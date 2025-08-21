from pathlib import Path

from askui.utils.api_utils import ConflictError, ListResponse, NotFoundError

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

    def find(self, query: FeatureListQuery) -> ListResponse[Feature]:
        """List all available features.

        Args:
            query (FeatureListQuery): Query parameters for listing features

        Returns:
            ListResponse[Feature]: ListResponse containing features sorted by
                creation date
        """
        if not self._features_dir.exists():
            return ListResponse(data=[])

        feature_files = list(self._features_dir.glob("*.json"))
        features: list[Feature] = []
        for f in feature_files:
            with f.open("r", encoding="utf-8") as file:
                features.append(Feature.model_validate_json(file.read()))

        # Sort by creation date
        features = sorted(
            features, key=lambda f: f.created_at, reverse=(query.order == "desc")
        )

        # Apply before/after filters
        if query.after:
            features = [f for f in features if f.id > query.after]
        if query.before:
            features = [f for f in features if f.id < query.before]

        # Apply limit
        features = features[: query.limit]

        return ListResponse(
            data=features,
            first_id=features[0].id if features else None,
            last_id=features[-1].id if features else None,
            has_more=len(feature_files) > query.limit,
        )

    def find_one(self, feature_id: FeatureId) -> Feature:
        """Retrieve a feature by ID.

        Args:
            feature_id: ID of feature to retrieve

        Returns:
            Feature object

        Raises:
            FileNotFoundError: If feature doesn't exist
        """
        feature_file = self._features_dir / f"{feature_id}.json"
        if not feature_file.exists():
            error_msg = f"Feature {feature_id} not found"
            raise FileNotFoundError(error_msg)

        with feature_file.open("r", encoding="utf-8") as f:
            return Feature.model_validate_json(f.read())

    def create(self, params: FeatureCreateParams) -> Feature:
        feature = Feature.create(params)
        feature_file = self._features_dir / f"{feature.id}.json"
        if feature_file.exists():
            error_msg = f"Feature {feature.id} already exists"
            raise ConflictError(error_msg)
        feature_file.write_text(feature.model_dump_json())
        return feature

    def modify(self, feature_id: FeatureId, params: FeatureModifyParams) -> Feature:
        feature = self.find_one(feature_id)
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
