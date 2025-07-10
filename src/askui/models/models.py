import abc
import re
from collections.abc import Iterator
from enum import Enum
from typing import Annotated, Callable, Type

from pydantic import BaseModel, ConfigDict, Field, RootModel
from typing_extensions import Literal, TypedDict

from askui.locators.locators import Locator
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCb
from askui.models.shared.settings import ActSettings
from askui.models.shared.tools import Tool
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.image_utils import ImageSource


class ModelName(str, Enum):
    """Enumeration of all available model names in AskUI.

    This enum provides type-safe access to model identifiers used throughout the
    library. Each model name corresponds to a specific AI model or model composition
    that can be used for different tasks like acting, getting information, or locating
    elements.
    """

    ANTHROPIC__CLAUDE__3_5__SONNET__20241022 = "anthropic-claude-3-5-sonnet-20241022"
    ASKUI = "askui"
    ASKUI__AI_ELEMENT = "askui-ai-element"
    ASKUI__COMBO = "askui-combo"
    ASKUI__OCR = "askui-ocr"
    ASKUI__PTA = "askui-pta"
    CLAUDE__SONNET__4__20250514 = "claude-sonnet-4-20250514"
    HF__SPACES__ASKUI__PTA_1 = "AskUI/PTA-1"
    HF__SPACES__OS_COPILOT__OS_ATLAS_BASE_7B = "OS-Copilot/OS-Atlas-Base-7B"
    HF__SPACES__QWEN__QWEN2_VL_2B_INSTRUCT = "Qwen/Qwen2-VL-2B-Instruct"
    HF__SPACES__QWEN__QWEN2_VL_7B_INSTRUCT = "Qwen/Qwen2-VL-7B-Instruct"
    HF__SPACES__SHOWUI__2B = "showlab/ShowUI-2B"
    TARS = "tars"


MODEL_DEFINITION_PROPERTY_REGEX_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


ModelDefinitionProperty = Annotated[
    str, Field(pattern=MODEL_DEFINITION_PROPERTY_REGEX_PATTERN)
]


class ModelDefinition(BaseModel):
    """
    A definition of a model.

    Args:
        task (str): The task the model is trained for, e.g., end-to-end OCR
            (`"e2e_ocr"`) or object detection (`"od"`)
        architecture (str): The architecture of the model, e.g., `"easy_ocr"` or
            `"yolo"`
        version (str): The version of the model
        interface (str): The interface the model is trained for, e.g.,
            `"online_learning"`
        use_case (str, optional): The use case the model is trained for. In the case
            of workspace specific AskUI models, this is often the workspace id but
            with "-" replaced by "_". Defaults to
            `"00000000_0000_0000_0000_000000000000"` (custom null value).
        tags (list[str], optional): Tags for identifying the model that cannot be
            represented by other properties, e.g., `["trained", "word_level"]`
    """

    model_config = ConfigDict(
        validate_by_name=True,
    )
    task: ModelDefinitionProperty = Field(
        description=(
            "The task the model is trained for, e.g., end-to-end OCR (e2e_ocr) or "
            "object detection (od)"
        ),
        examples=["e2e_ocr", "od"],
    )
    architecture: ModelDefinitionProperty = Field(
        description="The architecture of the model", examples=["easy_ocr", "yolo"]
    )
    version: str = Field(pattern=r"^[0-9]{1,6}$")
    interface: ModelDefinitionProperty = Field(
        description="The interface the model is trained for",
        examples=["online_learning"],
    )
    use_case: ModelDefinitionProperty = Field(
        description=(
            "The use case the model is trained for. In the case of workspace specific "
            'AskUI models, this is often the workspace id but with "-" replaced by "_"'
        ),
        examples=[
            "fb3b9a7b_3aea_41f7_ba02_e55fd66d1c1e",
            "00000000_0000_0000_0000_000000000000",
        ],
        default="00000000_0000_0000_0000_000000000000",
        serialization_alias="useCase",
    )
    tags: list[ModelDefinitionProperty] = Field(
        default_factory=list,
        description=(
            "Tags for identifying the model that cannot be represented by other "
            "properties"
        ),
        examples=["trained", "word_level"],
    )

    @property
    def model_name(self) -> str:
        """
        The name of the model.
        """
        return "-".join(
            [
                self.task,
                self.architecture,
                self.interface,
                self.use_case,
                self.version,
                *self.tags,
            ]
        )


class ModelComposition(RootModel[list[ModelDefinition]]):
    """
    A composition of models (list of `ModelDefinition`) to be used for a task, e.g.,
    locating an element on the screen to be able to click on it or extracting text from
    an image.
    """

    def __iter__(self) -> Iterator[ModelDefinition]:  # type: ignore
        return iter(self.root)

    def __getitem__(self, index: int) -> ModelDefinition:
        return self.root[index]


Point = tuple[int, int]
"""
A tuple of two integers representing the coordinates of a point on the screen.
"""


class ActModel(abc.ABC):
    """Abstract base class for models that can execute autonomous actions.

    Models implementing this interface can be used with the `VisionAgent.act()`.

    Example:
        ```python
        from askui import (
            ActModel,
            MessageParam,
            OnMessageCb,
            VisionAgent,
        )
        from typing_extensions import override

        class MyActModel(ActModel):
            @override
            def act(
                self,
                messages: list[MessageParam],
                model_choice: str,
                on_message: OnMessageCb | None = None,
                tools: list[Tool] | None = None,
                settings: AgentSettings | None = None,
            ) -> None:
                pass  # implement action logic here

        with VisionAgent(models={"my-act": MyActModel()}) as agent:
            agent.act("search for flights", model="my-act")
    """

    @abc.abstractmethod
    def act(
        self,
        messages: list[MessageParam],
        model_choice: str,
        on_message: OnMessageCb | None = None,
        tools: list[Tool] | None = None,
        settings: ActSettings | None = None,
    ) -> None:
        """
        Execute autonomous actions to achieve a goal, using a message history
        and optional callbacks, encoded in the messages. In the simplest case,
        it can be found in the first message `messages[0].content` as a `str`.

        The `messages` usually start with a `"user"` (role) message which is followed by
        alternating `"assistant"` (AI agent) and `"user"` messages (which can be
        automatic tool use, e.g., taking a screenshot) similar how you would
        expect it from a conversation whereby the `"assistant"` determines the next
        actions which are then automatically taking by the `"user"` programmatically
        until it eventually returns, usually with an `"assistant"` message that either
        says that the goal has been achieved or that it failed to achieve the goal.

        Args:
            messages (list[MessageParam]): The message history to start that
                determines the actions and following messages.
            model_choice (str): The name of the model being used, e.g., useful for
                models registered under multiple keys, e.g., `"my-act-1"` and
                `"my-act-2"` that depending on the key (passed as `model_choice`)
                behave differently.
            on_message (OnMessageCb | None, optional): Callback for new messages
                from either an assistant/agent or a user (including
                automatic/programmatic tool use, e.g., taking a screenshot).
                If it returns `None`, the acting is canceled and `act()` returns
                immediately. If it returns a `MessageParam`, this `MessageParma` is
                added to the message history and the acting continues based on the
                message. The message may be modified by the callback to allow for
                directing the assistant/agent or tool use.
            tools (list[Tool] | None, optional): The tools for the agent.
                Defaults to `None`.
            settings (AgentSettings | None, optional): The settings for the agent.
                Defaults to `None`.

        Returns:
            None

        Raises:
            NotImplementedError: If the method is not implemented.
        """  # noqa: E501
        raise NotImplementedError


class GetModel(abc.ABC):
    """Abstract base class for models that can extract information from images.

    Models implementing this interface can be used with the `get()` method of
    `VisionAgent`
    to extract information from screenshots or other images. These models analyze visual
    content and return structured or unstructured information based on queries.

    Example:
        ```python
        from askui import GetModel, VisionAgent, ResponseSchema, ImageSource
        from typing import Type

        class MyGetModel(GetModel):
            def get(
                self,
                query: str,
                image: ImageSource,
                response_schema: Type[ResponseSchema] | None,
                model_choice: str,
            ) -> ResponseSchema | str:
                # Implement custom get logic
                return "Custom response"

        with VisionAgent(models={"my-get": MyGetModel()}) as agent:
            result = agent.get("what's on screen?", model="my-get")
        ```
    """

    @abc.abstractmethod
    def get(
        self,
        query: str,
        image: ImageSource,
        response_schema: Type[ResponseSchema] | None,
        model_choice: str,
    ) -> ResponseSchema | str:
        """Extract information from an image based on a query.

        Args:
            query (str): A description of what information to extract
            image (ImageSource): The image to analyze (screenshot or provided image)
            response_schema (Type[ResponseSchema] | None): Optional Pydantic model class
                defining the expected response structure
            model_choice (str): The name of the model being used (useful for models that
                support multiple configurations)

        Returns:
            Either a string response or a Pydantic model instance if response_schema is
            provided
        """
        raise NotImplementedError


class LocateModel(abc.ABC):
    """Abstract base class for models that can locate UI elements in images.

    Models implementing this interface can be used with the `click()`, `locate()`, and
    `mouse_move()` methods of `VisionAgent` to find UI elements on screen. These models
    analyze visual content to determine the coordinates of elements based on
    descriptions or locators.

    Example:
        ```python
        from askui import LocateModel, VisionAgent, Locator, ImageSource, Point
        from askui.models import ModelComposition

        class MyLocateModel(LocateModel):
            def locate(
                self,
                locator: str | Locator,
                image: ImageSource,
                model_choice: ModelComposition | str,
            ) -> Point:
                # Implement custom locate logic
                return (100, 100)

        with VisionAgent(models={"my-locate": MyLocateModel()}) as agent:
            agent.click("button", model="my-locate")
        ```
    """

    @abc.abstractmethod
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model_choice: ModelComposition | str,
    ) -> Point:
        """Find the coordinates of a UI element in an image.

        Args:
            locator (str | Locator): A description or locator object identifying the
                element to find
            image (ImageSource): The image to analyze (screenshot or provided image)
            model_choice (ModelComposition | str): Either a string model name or a
                `ModelComposition` for models that support composition

        Returns:
            A tuple of (x, y) coordinates where the element was found
        """
        raise NotImplementedError


Model = ActModel | GetModel | LocateModel
"""Union type of all abstract model classes.

This type represents any model that can be used with `VisionAgent`, whether it's an
`ActModel`, `GetModel`, or `LocateModel`. It's useful for type hints when you need to
work with models in a generic way.
"""


class ModelChoice(TypedDict, total=False):
    """Type definition for specifying different models for different tasks.

    This `TypedDict` allows you to specify different models for `act()`, `get()`, and
    `locate()` tasks when initializing `VisionAgent`. All fields are optional.

    Attributes:
        act: Model name to use for `act()` commands
        get: Model name to use for `get()` commands
        locate: Model name or composition to use for `locate()`, `click()`, and
            `mouse_move()` commands
    """

    act: str
    get: str
    locate: str | ModelComposition


class TotalModelChoice(TypedDict):
    act: str
    get: str
    locate: str | ModelComposition


ModelRegistry = dict[str, Model | Callable[[], Model]]
"""Type definition for model registry.

A dictionary mapping model names to either model instances or factory functions (for
lazy initialization on first use) that create model instances. Used to register custom
models with `VisionAgent`.

Example:
    ```python
    from askui import ModelRegistry, ActModel

    class MyModel(ActModel):
        def act(
            self,
            messages: list[MessageParam],
            model_choice: str,
            on_message: OnMessageCb | None = None,
            tools: list[Tool] | None = None,
            settings: AgentSettings | None = None,
        ) -> None:
            pass  # implement action logic here

    # Registry with model instance
    registry: ModelRegistry = {
        "my-model": MyModel()
    }

    # Registry with model factory
    def create_model() -> ActModel:
        return MyModel()

    registry_with_factory: ModelRegistry = {
        "my-model": create_model
    }
    ```
"""


MODEL_TYPES: dict[Literal["act", "get", "locate"], Type[Model]] = {
    "act": ActModel,
    "get": GetModel,
    "locate": LocateModel,
}
