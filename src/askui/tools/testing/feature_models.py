from dataclasses import dataclass
from typing import Annotated, Literal

from fastapi import Query
from pydantic import BaseModel, Field

from askui.utils.api_utils import ListQuery, Resource
from askui.utils.datetime_utils import UnixDatetime, now
from askui.utils.id_utils import IdField, generate_time_ordered_id
from askui.utils.not_given import NOT_GIVEN, BaseModelWithNotGiven, NotGiven

FeatureId = Annotated[str, IdField("feat")]


class FeatureCreateParams(BaseModel):
    """
    Parameters for creating a feature.
    """

    name: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)


class FeatureModifyParams(BaseModelWithNotGiven):
    """
    Parameters for modifying a feature.
    """

    name: str | NotGiven = NOT_GIVEN
    description: str | None | NotGiven = NOT_GIVEN
    tags: list[str] | NotGiven = NOT_GIVEN


@dataclass(kw_only=True)
class FeatureListQuery(ListQuery):
    tags: Annotated[list[str] | NotGiven, Query()] = NOT_GIVEN


class Feature(Resource):
    """
    A structured representation of a feature used for BDD test automation.

    Args:
        id (FeatureId): The id of the feature. Must start with the 'feat_' prefix and be
            followed by one or more alphanumerical characters.
        object (Literal['feature']): The object type, always 'feature'.
        created_at (UnixDatetime): The creation time as a Unix timestamp.
        name (str): The name or title of the feature.
        description (str | None, optional): An optional detailed description of the
            feature's purpose. Default is `None`.
        tags (list[str], optional): Tags associated with the feature for filtering or
            categorization. Default is an empty list.
    """

    id: FeatureId
    object: Literal["feature"] = "feature"
    created_at: UnixDatetime
    name: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)

    @classmethod
    def create(cls, params: FeatureCreateParams) -> "Feature":
        return cls(
            id=generate_time_ordered_id("feat"),
            created_at=now(),
            **params.model_dump(),
        )

    def modify(self, params: FeatureModifyParams) -> "Feature":
        return Feature.model_validate(
            {
                **self.model_dump(),
                **params.model_dump(),
            }
        )
