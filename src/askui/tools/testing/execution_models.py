from dataclasses import dataclass
from typing import Annotated, Literal

from fastapi import Query
from pydantic import BaseModel, Field

from askui.tools.testing.feature_models import FeatureId
from askui.tools.testing.scenario_models import ExampleIndex, ScenarioId
from askui.utils.api_utils import ListQuery, Resource
from askui.utils.datetime_utils import UnixDatetime, now
from askui.utils.id_utils import IdField, generate_time_ordered_id
from askui.utils.not_given import NOT_GIVEN, BaseModelWithNotGiven, NotGiven

ExecutionId = Annotated[str, IdField("exec")]

StepIndex = Annotated[int, Field(ge=0)]


ExecutionStatus = Literal[
    "passed", "failed", "pending", "error", "incomplete", "skipped"
]


class ExecutionStep(BaseModel):
    """
    A step executed within a scenario.

    Args:
        keyword (str): Gherkin step keyword such as Given, When, Then, And, or But.
        text (str): Step description with parameters replaced.
        status (ExecutionStatus): Status of the step. Default is "pending".
    """

    keyword: Literal["Given", "When", "Then", "And", "But"]
    text: str
    status: ExecutionStatus


class ExecutionCreateParams(BaseModel):
    """
    Parameters for creating an execution.
    """

    feature: FeatureId
    scenario: ScenarioId
    status: ExecutionStatus
    example: ExampleIndex | None = None
    steps: list[ExecutionStep]


class ExecutionModifyParams(BaseModelWithNotGiven):
    """
    Parameters for modifying an execution.
    """

    status: ExecutionStatus | NotGiven = NOT_GIVEN
    steps: list[ExecutionStep] | NotGiven = NOT_GIVEN


@dataclass(kw_only=True)
class ExecutionListQuery(ListQuery):
    feature: Annotated[FeatureId | NotGiven, Query()] = NOT_GIVEN
    scenario: Annotated[ScenarioId | NotGiven, Query()] = NOT_GIVEN
    example: Annotated[ExampleIndex | NotGiven, Query()] = NOT_GIVEN


class AppendExecutionStepParams(BaseModel):
    step: ExecutionStep


class ModifyExecutionStepParams(BaseModelWithNotGiven):
    status: ExecutionStatus | NotGiven = NOT_GIVEN


class Execution(Resource):
    """
    A structured representation of an execution result for a scenario or scenario
    outline example.

    Args:
        id (ExecutionId): The id of the execution. Must start with the 'exec_' prefix.
        object (Literal['execution']): The object type, always 'execution'.
        created_at (UnixDatetime): The creation time as a Unix timestamp.
        feature (str): Id of the feature.
        scenario (str): Id of the scenario.
        example (ExampleIndex | None, optional): Index of the example for scenario
            outline. Default is `None`.
        status (ExecutionStatus): Overall execution result.
        steps (list[ExecutionStep]): List of executed steps with results.
    """

    id: ExecutionId
    object: Literal["execution"] = "execution"
    created_at: UnixDatetime
    feature: str
    scenario: str
    example: ExampleIndex | None = None
    status: ExecutionStatus
    steps: list[ExecutionStep]

    @classmethod
    def create(
        cls,
        params: ExecutionCreateParams,
    ) -> "Execution":
        return cls(
            id=generate_time_ordered_id("exec"),
            created_at=now(),
            **params.model_dump(),
        )

    def modify(self, params: ExecutionModifyParams) -> "Execution":
        return Execution.model_validate(
            {
                **self.model_dump(),
                **params.model_dump(),
            }
        )
