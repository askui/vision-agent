from dataclasses import dataclass
from typing import Annotated, Literal

from fastapi import Query
from pydantic import BaseModel, Field

from askui.tools.testing.feature_models import FeatureId
from askui.utils.api_utils import ListQuery, Resource
from askui.utils.datetime_utils import UnixDatetime, now
from askui.utils.id_utils import IdField, generate_time_ordered_id
from askui.utils.not_given import NOT_GIVEN, BaseModelWithNotGiven, NotGiven

ScenarioId = Annotated[str, IdField("scen")]
ExampleIndex = Annotated[int, Field(ge=0)]


class ScenarioStep(BaseModel):
    """
    A single step within a scenario or background, defined by a keyword and the step
    text.

    Args:
        keyword (str): Gherkin step keyword such as Given, When, Then, And, or But.
        text (str): The actual step content in natural language.
    """

    keyword: Literal["Given", "When", "Then", "And", "But"]
    text: str


class ScenarioExample(BaseModel):
    """
    Example data row for scenario outlines.

    Args:
        name (str | None, optional): Optional name of the example. Default is `None`.
        parameters (dict[str, str]): Mapping of placeholder keys to values.
    """

    name: str | None = None
    parameters: dict[str, str]


class ScenarioCreateParams(BaseModel):
    feature: FeatureId
    name: str
    tags: list[str] = Field(default_factory=list)
    steps: list[ScenarioStep]
    examples: list[ScenarioExample] = Field(default_factory=list)


class ScenarioModifyParams(BaseModelWithNotGiven):
    name: str | NotGiven = NOT_GIVEN
    tags: list[str] | NotGiven = NOT_GIVEN
    steps: list[ScenarioStep] | NotGiven = NOT_GIVEN
    examples: list[ScenarioExample] | NotGiven = NOT_GIVEN


@dataclass(kw_only=True)
class ScenarioListQuery(ListQuery):
    feature: Annotated[FeatureId | NotGiven, Query()] = NOT_GIVEN
    tags: Annotated[list[str] | NotGiven, Query()] = NOT_GIVEN


class Scenario(Resource):
    """
    A structured representation of a scenario or scenario outline for BDD test
    automation.

    Args:
        id (ScenarioId): The id of the scenario. Must start with the 'scen_' prefix and
            be followed by one or more alphanumerical characters.
        object (Literal['scenario']): The object type, always 'scenario'.
        created_at (UnixDatetime): The creation time as a Unix timestamp.
        feature (FeatureId): Id of the feature.
        name (str): The title of the scenario.
        tags (list[str], optional): Tags for filtering or categorizing the scenario.
            Default is an empty list.
        steps (list[ScenarioStep]): The ordered list of steps to execute in the
            scenario.
        examples (list[ScenarioExample], optional): Example data rows for scenario
            outlines. Default is an empty list.
    """

    id: ScenarioId
    object: Literal["scenario"] = "scenario"
    created_at: UnixDatetime
    feature: FeatureId
    name: str
    tags: list[str] = Field(default_factory=list)
    steps: list[ScenarioStep]
    examples: list[ScenarioExample] = Field(default_factory=list)

    @classmethod
    def create(cls, params: ScenarioCreateParams) -> "Scenario":
        return cls(
            id=generate_time_ordered_id("scen"),
            created_at=now(),
            **params.model_dump(),
        )

    def modify(self, params: ScenarioModifyParams) -> "Scenario":
        return Scenario.model_validate(
            {
                **self.model_dump(),
                **params.model_dump(),
            }
        )
