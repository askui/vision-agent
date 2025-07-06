"""Integration tests for custom model registration and selection."""

from typing import Any, Optional, Type, Union

import pytest
from typing_extensions import override

from askui import (
    ActModel,
    GetModel,
    LocateModel,
    ModelRegistry,
    Point,
    ResponseSchema,
    ResponseSchemaBase,
    VisionAgent,
)
from askui.locators.locators import Locator
from askui.models import ModelComposition, ModelDefinition, ModelName
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCb
from askui.models.shared.settings import ActSettings
from askui.models.shared.tools import Tool
from askui.tools.toolbox import AgentToolbox
from askui.utils.image_utils import ImageSource


class SimpleActModel(ActModel):
    """Simple act model that records goals."""

    def __init__(self) -> None:
        self.goals: list[list[dict[str, Any]]] = []
        self.model_choices: list[str] = []

    @override
    def act(
        self,
        messages: list[MessageParam],
        model_choice: str,
        on_message: OnMessageCb | None = None,
        tools: list[Tool] | None = None,
        settings: ActSettings | None = None,
    ) -> None:
        self.goals.append([message.model_dump(mode="json") for message in messages])
        self.model_choices.append(model_choice)


class SimpleGetModel(GetModel):
    """Simple get model that returns a fixed response."""

    def __init__(self, response: str | ResponseSchemaBase = "test response") -> None:
        self.queries: list[str] = []
        self.images: list[ImageSource] = []
        self.schemas: list[Any] = []
        self.model_choices: list[str] = []
        self.response = response

    def get(
        self,
        query: str,
        image: ImageSource,
        response_schema: Optional[Type[ResponseSchema]],
        model_choice: str,
    ) -> Union[ResponseSchema, str]:
        self.queries.append(query)
        self.images.append(image)
        self.schemas.append(response_schema)
        self.model_choices.append(model_choice)
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
        self.model_choices: list[ModelComposition | str] = []
        self._point = point

    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model_choice: ModelComposition | str,
    ) -> Point:
        self.locators.append(locator)
        self.images.append(image)
        self.model_choices.append(model_choice)
        return self._point


class SimpleResponseSchema(ResponseSchemaBase):
    """Simple response schema for testing."""

    value: str


class TestCustomModels:
    """Test suite for custom model registration and selection."""

    @pytest.fixture
    def act_model(self) -> SimpleActModel:
        return SimpleActModel()

    @pytest.fixture
    def get_model(self) -> SimpleGetModel:
        return SimpleGetModel()

    @pytest.fixture
    def locate_model(self) -> SimpleLocateModel:
        return SimpleLocateModel()

    @pytest.fixture
    def model_registry(
        self,
        act_model: SimpleActModel,
        get_model: SimpleGetModel,
        locate_model: SimpleLocateModel,
    ) -> ModelRegistry:
        return {
            "custom-act": act_model,
            "custom-get": get_model,
            "custom-locate": locate_model,
        }

    def test_register_and_use_custom_act_model(
        self,
        model_registry: ModelRegistry,
        act_model: SimpleActModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test registering and using a custom act model."""
        with VisionAgent(models=model_registry, tools=agent_toolbox_mock) as agent:
            agent.act("test goal", model="custom-act")

        assert act_model.goals == [
            [{"role": "user", "content": "test goal", "stop_reason": None}],
        ]
        assert act_model.model_choices == ["custom-act"]

    def test_register_and_use_custom_get_model(
        self,
        model_registry: ModelRegistry,
        get_model: SimpleGetModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test registering and using a custom get model."""
        with VisionAgent(models=model_registry, tools=agent_toolbox_mock) as agent:
            result = agent.get("test query", model="custom-get")

        assert result == "test response"
        assert get_model.queries == ["test query"]
        assert get_model.model_choices == ["custom-get"]

    def test_register_and_use_custom_locate_model(
        self,
        model_registry: ModelRegistry,
        locate_model: SimpleLocateModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test registering and using a custom locate model."""
        with VisionAgent(models=model_registry, tools=agent_toolbox_mock) as agent:
            agent.click("test element", model="custom-locate")

        assert locate_model.locators == ["test element"]
        assert locate_model.model_choices == ["custom-locate"]

    def test_register_and_use_model_factory(
        self,
        act_model: SimpleActModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test registering and using a model factory."""

        def create_model() -> ActModel:
            return act_model

        registry: ModelRegistry = {"factory-model": create_model}

        with VisionAgent(models=registry, tools=agent_toolbox_mock) as agent:
            agent.act("test goal", model="factory-model")

        assert act_model.goals == [
            [{"role": "user", "content": "test goal", "stop_reason": None}],
        ]
        assert act_model.model_choices == ["factory-model"]

    def test_register_multiple_models_for_same_task(
        self,
        act_model: SimpleActModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test registering multiple models for the same task."""

        class AnotherActModel(ActModel):
            @override
            def act(
                self,
                messages: list[MessageParam],
                model_choice: str,
                on_message: OnMessageCb | None = None,
                tools: list[Tool] | None = None,
                settings: ActSettings | None = None,
            ) -> None:
                pass

        registry: ModelRegistry = {
            "act-1": act_model,
            "act-2": AnotherActModel(),
        }

        with VisionAgent(models=registry, tools=agent_toolbox_mock) as agent:
            agent.act("test goal", model="act-1")
            agent.act("another goal", model="act-2")

        assert act_model.goals == [
            [{"role": "user", "content": "test goal", "stop_reason": None}],
        ]
        assert act_model.model_choices == ["act-1"]

    def test_use_response_schema_with_custom_get_model(
        self,
        model_registry: ModelRegistry,
        get_model: SimpleGetModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test using a response schema with a custom get model."""
        response = SimpleResponseSchema(value="test value")
        get_model.response = response

        with VisionAgent(models=model_registry, tools=agent_toolbox_mock) as agent:
            result = agent.get(
                "test query",
                response_schema=SimpleResponseSchema,
                model="custom-get",
            )

        assert isinstance(result, SimpleResponseSchema)
        assert result.value == "test value"
        assert get_model.schemas == [SimpleResponseSchema]

    def test_override_default_model(
        self,
        act_model: SimpleActModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test overriding a default model with a custom one."""
        registry: ModelRegistry = {ModelName.ASKUI: act_model}

        with VisionAgent(models=registry, tools=agent_toolbox_mock) as agent:
            agent.act("test goal")  # Should use custom model since it overrides "askui"

        assert act_model.goals == [
            [{"role": "user", "content": "test goal", "stop_reason": None}],
        ]
        assert act_model.model_choices == [ModelName.ASKUI]

    def test_model_composition(
        self,
        locate_model: SimpleLocateModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test using model composition with a custom locate model."""
        registry: ModelRegistry = {"askui": locate_model}

        composition = ModelComposition(
            [
                ModelDefinition(
                    task="e2e_ocr",
                    architecture="easy_ocr",
                    version="1",
                    interface="test",
                )
            ]
        )

        with VisionAgent(models=registry, tools=agent_toolbox_mock) as agent:
            agent.click("test element", model=composition)

        assert locate_model.model_choices == [composition]

    @pytest.mark.parametrize(
        "model_name,expected_exception",
        [
            ("nonexistent-model", Exception),
            ("custom-act", Exception),
            ("custom-get", Exception),
        ],
    )
    def test_invalid_model_usage(
        self,
        model_registry: ModelRegistry,
        model_name: str,
        expected_exception: type[Exception],
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test error handling for invalid model usage."""
        with pytest.raises(expected_exception):
            with VisionAgent(models=model_registry, tools=agent_toolbox_mock) as agent:
                if model_name == "custom-act":
                    agent.get("test query", model=model_name)
                elif model_name == "custom-get":
                    agent.act("test goal", model=model_name)
                else:
                    agent.act("test goal", model=model_name)

    def test_dymamic_model_initialization(
        self,
        act_model: SimpleActModel,
        agent_toolbox_mock: AgentToolbox,
    ) -> None:
        """Test that model factories are called when needed."""
        init_count = 0

        def create_model() -> ActModel:
            nonlocal init_count
            init_count += 1
            return act_model

        registry: ModelRegistry = {"lazy-model": create_model}

        with VisionAgent(models=registry, tools=agent_toolbox_mock) as agent:
            # Model should not be initialized yet
            assert init_count == 0

            # First use should initialize the model
            agent.act("test goal", model="lazy-model")
            assert init_count == 1

            # Second use should reuse the same instance
            agent.act("another goal", model="lazy-model")
            assert init_count == 2

        assert act_model.goals == [
            [{"role": "user", "content": "test goal", "stop_reason": None}],
            [{"role": "user", "content": "another goal", "stop_reason": None}],
        ]
