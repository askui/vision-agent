"""Integration tests for custom model usage with direct injection."""

import pathlib
from typing import Any

import pytest
from typing_extensions import override

from askui import (
    ActModel,
    GetModel,
    LocateModel,
    Point,
    PointList,
    ResponseSchema,
    ResponseSchemaBase,
    VisionAgent,
)
from askui.locators.locators import Locator
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCb
from askui.models.shared.settings import ActSettings, GetSettings, LocateSettings
from askui.models.shared.tools import ToolCollection
from askui.tools.toolbox import AgentToolbox
from askui.utils.image_utils import ImageSource
from askui.utils.source_utils import Source


class SimpleActModel(ActModel):
    """Simple act model that records goals."""

    def __init__(self) -> None:
        self.goals: list[list[dict[str, str]]] = []

    @override
    def act(
        self,
        messages: list[MessageParam],
        act_settings: ActSettings,
        on_message: OnMessageCb | None = None,
        tools: ToolCollection | None = None,
    ) -> None:
        self.goals.append([message.model_dump(mode="json") for message in messages])


class SimpleGetModel(GetModel):
    """Simple get model that returns a fixed response."""

    def __init__(self, response: str | ResponseSchemaBase = "test response") -> None:
        self.queries: list[str] = []
        self.sources: list[Source] = []
        self.schemas: list[Any] = []
        self.response = response

    @override
    def get(
        self,
        query: str,
        source: Source,
        response_schema: type[ResponseSchema] | None,
        get_settings: GetSettings,
    ) -> ResponseSchema | str:
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

    def __init__(self, point: Point = (100, 100)) -> None:
        self.locators: list[str | Locator] = []
        self.images: list[ImageSource] = []
        self._point = point

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> PointList:
        self.locators.append(locator)
        self.images.append(image)
        return [self._point]


class SimpleResponseSchema(ResponseSchemaBase):
    """Simple response schema for testing."""

    value: str


class TestCustomModels:
    """Test suite for custom model direct injection."""

    @pytest.fixture
    def act_model(self) -> SimpleActModel:
        return SimpleActModel()

    @pytest.fixture
    def get_model(self) -> SimpleGetModel:
        return SimpleGetModel()

    @pytest.fixture
    def locate_model(self) -> SimpleLocateModel:
        return SimpleLocateModel()

    def test_inject_and_use_custom_act_model(
        self,
        act_model: SimpleActModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test injecting and using a custom act model."""
        with VisionAgent(act_model=act_model, tools=agent_toolbox_mock) as agent:
            agent.act("test goal")

        assert act_model.goals == [
            [{"role": "user", "content": "test goal", "stop_reason": None}],
        ]

    def test_inject_and_use_custom_get_model(
        self,
        get_model: SimpleGetModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test injecting and using a custom get model."""
        with VisionAgent(get_model=get_model, tools=agent_toolbox_mock) as agent:
            result = agent.get("test query")

        assert result == "test response"
        assert get_model.queries == ["test query"]

    def test_inject_and_use_custom_get_model_with_pdf(
        self,
        get_model: SimpleGetModel,
        agent_toolbox_mock: AgentToolbox,
        path_fixtures_dummy_pdf: pathlib.Path,
    ) -> None:
        """Test injecting and using a custom get model with a PDF."""
        with VisionAgent(get_model=get_model, tools=agent_toolbox_mock) as agent:
            result = agent.get("test query", source=path_fixtures_dummy_pdf)

        assert result == "test response"
        assert get_model.queries == ["test query"]

    def test_inject_and_use_custom_locate_model(
        self,
        locate_model: SimpleLocateModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test injecting and using a custom locate model."""
        with VisionAgent(locate_model=locate_model, tools=agent_toolbox_mock) as agent:
            agent.click("test element")

        assert locate_model.locators == ["test element"]

    def test_inject_all_custom_models(
        self,
        act_model: SimpleActModel,
        get_model: SimpleGetModel,
        locate_model: SimpleLocateModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test injecting all custom models at once."""
        with VisionAgent(
            act_model=act_model,
            get_model=get_model,
            locate_model=locate_model,
            tools=agent_toolbox_mock,
        ) as agent:
            agent.act("test goal")
            result = agent.get("test query")
            agent.click("test element")

        assert act_model.goals == [
            [{"role": "user", "content": "test goal", "stop_reason": None}],
        ]
        assert get_model.queries == ["test query"]
        assert result == "test response"
        assert locate_model.locators == ["test element"]

    def test_per_call_act_model_override(
        self,
        act_model: SimpleActModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test overriding the act model for a single call."""

        class AnotherActModel(ActModel):
            def __init__(self) -> None:
                self.goals: list[list[dict[str, str]]] = []

            @override
            def act(
                self,
                messages: list[MessageParam],
                act_settings: ActSettings,
                on_message: OnMessageCb | None = None,
                tools: ToolCollection | None = None,
            ) -> None:
                self.goals.append(
                    [message.model_dump(mode="json") for message in messages]
                )

        another_model = AnotherActModel()

        with VisionAgent(act_model=act_model, tools=agent_toolbox_mock) as agent:
            # Use default model
            agent.act("first goal")

            # Override for this call
            agent.act("second goal", act_model=another_model)

            # Use default model again
            agent.act("third goal")

        # Default model should have been called twice
        assert act_model.goals == [
            [{"role": "user", "content": "first goal", "stop_reason": None}],
            [{"role": "user", "content": "third goal", "stop_reason": None}],
        ]

        # Override model should have been called once
        assert another_model.goals == [
            [{"role": "user", "content": "second goal", "stop_reason": None}],
        ]

    def test_per_call_get_model_override(
        self,
        get_model: SimpleGetModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test overriding the get model for a single call."""
        another_model = SimpleGetModel(response="another response")

        with VisionAgent(get_model=get_model, tools=agent_toolbox_mock) as agent:
            # Use default model
            result1 = agent.get("first query")

            # Override for this call
            result2 = agent.get("second query", get_model=another_model)

            # Use default model again
            result3 = agent.get("third query")

        assert result1 == "test response"
        assert result2 == "another response"
        assert result3 == "test response"

        # Default model should have been called twice
        assert get_model.queries == ["first query", "third query"]

        # Override model should have been called once
        assert another_model.queries == ["second query"]

    def test_per_call_locate_model_override(
        self,
        locate_model: SimpleLocateModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test overriding the locate model for a single call."""
        another_model = SimpleLocateModel(point=(200, 200))

        with VisionAgent(locate_model=locate_model, tools=agent_toolbox_mock) as agent:
            # Use default model
            agent.locate("first element")

            # Override for this call
            agent.locate("second element", locate_model=another_model)

            # Use default model again
            agent.locate("third element")

        # Default model should have been called twice
        assert locate_model.locators == ["first element", "third element"]

        # Override model should have been called once
        assert another_model.locators == ["second element"]

    def test_use_response_schema_with_custom_get_model(
        self,
        get_model: SimpleGetModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test using a response schema with a custom get model."""
        response = SimpleResponseSchema(value="test value")
        get_model.response = response

        with VisionAgent(get_model=get_model, tools=agent_toolbox_mock) as agent:
            result = agent.get("test query", response_schema=SimpleResponseSchema)

        assert isinstance(result, SimpleResponseSchema)
        assert result.value == "test value"
        assert get_model.schemas == [SimpleResponseSchema]

    def test_defaults_to_built_in_models_when_not_provided(
        self,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test agent uses built-in defaults when custom ones not provided."""
        # This should not raise an error even though we're not providing custom
        # models - verifies the agent initializes correctly with defaults
        with VisionAgent(tools=agent_toolbox_mock) as agent:
            # Agent should initialize successfully without custom models
            assert agent is not None
