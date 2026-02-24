"""Integration tests for custom model usage."""

import pathlib
from typing import Any, Optional, Type, Union

import pytest

from askui import (
    GetModel,
    LocateModel,
    Point,
    PointList,
    ResponseSchema,
    ResponseSchemaBase,
    VisionAgent,
)
from askui.locators.locators import Locator
from askui.tools.toolbox import AgentToolbox
from askui.utils.image_utils import ImageSource
from askui.utils.source_utils import Source


class SimpleGetModel(GetModel):
    """Simple get model that returns a fixed response."""

    model_name: str = "simple-get-model"

    def __init__(self, response: str | ResponseSchemaBase = "test response") -> None:
        self.queries: list[str] = []
        self.sources: list[Source] = []
        self.schemas: list[Any] = []
        self.response = response

    def get(
        self,
        query: str,
        source: Source,
        response_schema: Optional[Type[ResponseSchema]],
    ) -> Union[ResponseSchema, str]:
        self.queries.append(query)
        self.sources.append(source)
        self.schemas.append(response_schema)
        if (
            response_schema is not None
            and isinstance(self.response, response_schema)
            or isinstance(self.response, str)
        ):
            return self.response
        err_msg = (
            "Response schema does not match the response type. "
            "Please use a response schema that matches the response type."
        )
        raise ValueError(err_msg)


class SimpleLocateModel(LocateModel):
    """Simple locate model that returns fixed coordinates."""

    model_name: str = "simple-locate-model"

    def __init__(self, point: Point = (100, 100)) -> None:
        self.locators: list[str | Locator] = []
        self.images: list[ImageSource] = []
        self._point = point

    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
    ) -> PointList:
        self.locators.append(locator)
        self.images.append(image)
        return [self._point]


class SimpleResponseSchema(ResponseSchemaBase):
    """Simple response schema for testing."""

    value: str


class TestCustomModels:
    """Test suite for custom model usage."""

    @pytest.fixture
    def get_model(self) -> SimpleGetModel:
        return SimpleGetModel()

    @pytest.fixture
    def locate_model(self) -> SimpleLocateModel:
        return SimpleLocateModel()

    def test_use_custom_get_model(
        self,
        get_model: SimpleGetModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test using a custom get model by passing it directly."""
        with VisionAgent(tools=agent_toolbox_mock) as agent:
            result = agent.get("test query", get_model=get_model)

        assert result == "test response"
        assert get_model.queries == ["test query"]

    def test_use_custom_get_model_with_pdf(
        self,
        get_model: SimpleGetModel,
        agent_toolbox_mock: AgentToolbox,
        path_fixtures_dummy_pdf: pathlib.Path,
    ) -> None:
        """Test using a custom get model with a PDF."""
        with VisionAgent(tools=agent_toolbox_mock) as agent:
            result = agent.get(
                "test query", get_model=get_model, source=path_fixtures_dummy_pdf
            )

        assert result == "test response"
        assert get_model.queries == ["test query"]

    def test_use_custom_locate_model(
        self,
        locate_model: SimpleLocateModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test using a custom locate model by passing it directly."""
        with VisionAgent(tools=agent_toolbox_mock) as agent:
            agent.locate("test element", locate_model=locate_model)

        assert locate_model.locators == ["test element"]

    def test_use_response_schema_with_custom_get_model(
        self,
        get_model: SimpleGetModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test using a response schema with a custom get model."""
        response = SimpleResponseSchema(value="test value")
        get_model.response = response

        with VisionAgent(tools=agent_toolbox_mock) as agent:
            result = agent.get(
                "test query",
                response_schema=SimpleResponseSchema,
                get_model=get_model,
            )

        assert isinstance(result, SimpleResponseSchema)
        assert result.value == "test value"
        assert get_model.schemas == [SimpleResponseSchema]
