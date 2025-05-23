import abc
import re
from collections.abc import Iterator
from enum import Enum
from typing import Annotated, Type

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypedDict

from askui.locators.locators import Locator
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.image_utils import ImageSource


class ModelName(str, Enum):
    ANTHROPIC__CLAUDE__3_5__SONNET__20241022 = "anthropic-claude-3-5-sonnet-20241022"
    ASKUI = "askui"
    ASKUI__AI_ELEMENT = "askui-ai-element"
    ASKUI__COMBO = "askui-combo"
    ASKUI__OCR = "askui-ocr"
    ASKUI__PTA = "askui-pta"
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
        populate_by_name=True,
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


# TODO
class ModelComposition(BaseModel):
    """
    A composition of models (list of `ModelDefinition`) to be used for a task, e.g.,
    locating an element on the screen to be able to click on it or extracting text from
    an image.
    """

    def __init__(self, model_definitions: list[ModelDefinition], name: str) -> None:
        self.model_definitions = model_definitions
        self.name = name

    def __iter__(self) -> Iterator[ModelDefinition]:  # type: ignore
        return iter(self.root)

    def __getitem__(self, index: int) -> ModelDefinition:
        return self.root[index]


Point = tuple[int, int]
"""
A tuple of two integers representing the coordinates of a point on the screen.
"""


class ActModel(abc.ABC):
    """
    Abstract base class for models that perform actions based on natural language goals.

    ActModel implementations are responsible for executing high-level actions on user
    interfaces, such as clicking buttons, filling forms, or navigating through
    applications based on textual descriptions of the desired outcome.
    """

    @abc.abstractmethod
    def act(self, goal: str, model: str) -> None:
        """
        Executes actions to achieve the specified goal.

        Args:
            goal (str): A natural language description of what should be accomplished.
                This could be a high-level task like "log in to the application" or
                "find and click the submit button".
            model (str): The model to use for the act operation.

        Example:
            ```python
            model = MyActModel()
            model.act("Open the settings menu")
            model.act("Fill out the login form with provided credentials")
            model.act("Navigate to the reports section")
            ```
        """
        raise NotImplementedError


class GetModel(abc.ABC):
    """
    Abstract base class for models that extract information from images based on queries.

    GetModel implementations analyze images and extract structured or unstructured
    information based on natural language queries. They can optionally return data
    conforming to a specific response schema for structured outputs, or return
    plain text for unstructured responses.
    """

    @abc.abstractmethod
    def get(
        self,
        query: str,
        image: ImageSource,
        response_schema: Type[ResponseSchema] | None,
        model: str,
    ) -> ResponseSchema | str:
        """
        Extracts information from an image based on the provided query.

        Args:
            query (str): A natural language question or instruction describing
                what information to extract from the image.
            image (ImageSource): The image to analyze.
            response_schema (Type[ResponseSchema] | None, optional): A Pydantic model
                class that defines the expected structure of the response. If provided,
                the response will be validated against this schema. If `None`, returns
                a plain string response.
            model (str): The model to use for the get operation.

        Returns:
            ResponseSchema | str: The extracted information. Returns a structured
                `ResponseSchema` object if `response_schema` is provided, otherwise
                returns a string.

        Example:
            ```python
            from pydantic import BaseModel
            from askui import ImageSource, ResponseSchemaBase

            class UserInfo(ResponseSchemaBase):
                username: str
                email: str

            model = MyGetModel()
            image = ImageSource("profile_page.png")

            # Get unstructured response
            info = model.get("What is the user's name?", image)
            print(info)  # "John Doe"

            # Get structured response
            user_data = model.get(
                "Extract the username and email",
                image,
                response_schema=UserInfo
            )
            print(user_data.username)  # "john_doe"
            print(user_data.email)     # "john@example.com"
            ```
        """
        raise NotImplementedError


class LocateModel(abc.ABC):
    """
    Abstract base class for models that locate UI elements within images.

    LocateModel implementations take a locator (either a string description or
    structured Locator object) and an image, then return the coordinates of the
    matching element. This is typically used for UI automation tasks where
    specific elements need to be identified before interaction.
    """

    @abc.abstractmethod
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model: ModelComposition | str,
    ) -> Point:
        """
        Locates a UI element within the provided image.

        Args:
            locator (str | Locator): The identifier for the element to locate.
                Can be a natural language description (e.g., "Submit button")
                or a structured Locator object with specific criteria.
            image (ImageSource): The image to search within.
            model (ModelComposition | str): The model composition to use
                for the locate operation.

        Returns:
            Point: A tuple of (x, y) coordinates indicating the center point
                of the located element in pixel coordinates.

        Example:
            ```python
            from askui import ImageSource

            model = MyLocateModel()
            image = ImageSource("screenshot.png")

            # Using string locator
            point = model.locate("Login button", image)
            print(f"Element found at: {point}")  # (450, 320)

            # Using Locator object
            from askui.locators import Locator
            locator = Locator(text="Submit", role="button")
            point = model.locate(locator, image)
            ```
        """
        raise NotImplementedError


Model = ActModel | GetModel | LocateModel


class ModelSelection(TypedDict, total=False):
    act: str
    get: str
    locate: str | ModelComposition
