import time
import types
from abc import ABC
from typing import Annotated, Optional, Type, overload

from dotenv import load_dotenv
from pydantic import ConfigDict, Field, validate_call
from typing_extensions import Self

from askui.container import telemetry
from askui.data_extractor import DataExtractor
from askui.locators.locators import Locator
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCb
from askui.models.shared.settings import ActSettings
from askui.models.shared.tools import Tool, ToolCollection
from askui.tools.agent_os import AgentOs
from askui.tools.android.agent_os import AndroidAgentOs
from askui.utils.image_utils import ImageSource
from askui.utils.source_utils import InputSource, load_image_source

from .logger import configure_logging, logger
from .models import ModelComposition
from .models.exceptions import ElementNotFoundError
from .models.model_router import ModelRouter, initialize_default_model_registry
from .models.models import (
    ModelChoice,
    ModelName,
    ModelRegistry,
    Point,
    PointList,
    TotalModelChoice,
)
from .models.types.response_schemas import ResponseSchema
from .reporting import Reporter
from .retry import ConfigurableRetry, Retry


class AgentBase(ABC):  # noqa: B024
    def __init__(
        self,
        log_level: int | str,
        reporter: Reporter,
        model: ModelChoice | ModelComposition | str | None,
        retry: Retry | None,
        models: ModelRegistry | None,
        tools: list[Tool] | None,
        agent_os: AgentOs | AndroidAgentOs,
    ) -> None:
        load_dotenv()
        configure_logging(level=log_level)
        self._reporter = reporter
        self._agent_os = agent_os

        self._tools = tools or []
        self._model_router = self._init_model_router(
            reporter=self._reporter,
            models=models or {},
        )
        self.model = model
        self._retry = retry or ConfigurableRetry(
            strategy="Exponential",
            base_delay=1000,
            retry_count=3,
            on_exception_types=(ElementNotFoundError,),
        )
        self._model_choice = self._init_model_choice(model)
        self._data_extractor = DataExtractor(
            reporter=self._reporter, models=models or {}
        )

    def _init_model_router(
        self,
        reporter: Reporter,
        models: ModelRegistry,
    ) -> ModelRouter:
        _models = initialize_default_model_registry(
            reporter=reporter,
        )
        _models.update(models)
        return ModelRouter(
            reporter=reporter,
            models=_models,
        )

    def _init_model_choice(
        self, model_choice: ModelComposition | ModelChoice | str | None
    ) -> TotalModelChoice:
        """Initialize the model choice based on the provided model parameter.

        Args:
            model (ModelComposition | ModelChoice | str | None): The model to initialize
                from. Can be a ModelComposition, ModelChoice dict, string, or None.

        Returns:
            TotalModelChoice: A dict with keys "act", "get", and "locate" mapping to
                model names (or a ModelComposition for "locate").
        """
        if isinstance(model_choice, ModelComposition):
            return {
                "act": ModelName.ASKUI,
                "get": ModelName.ASKUI,
                "locate": model_choice,
            }
        if isinstance(model_choice, str) or model_choice is None:
            return {
                "act": model_choice or ModelName.ASKUI,
                "get": model_choice or ModelName.ASKUI,
                "locate": model_choice or ModelName.ASKUI,
            }
        return {
            "act": model_choice.get("act", ModelName.ASKUI),
            "get": model_choice.get("get", ModelName.ASKUI),
            "locate": model_choice.get("locate", ModelName.ASKUI),
        }

    @telemetry.record_call(exclude={"goal", "on_message", "settings", "tools"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def act(
        self,
        goal: Annotated[str | list[MessageParam], Field(min_length=1)],
        model: str | None = None,
        on_message: OnMessageCb | None = None,
        tools: list[Tool] | ToolCollection | None = None,
        settings: ActSettings | None = None,
    ) -> None:
        """
        Instructs the agent to achieve a specified goal through autonomous actions.

        The agent will analyze the screen, determine necessary steps, and perform
        actions to accomplish the goal. This may include clicking, typing, scrolling,
        and other interface interactions.

        Args:
            goal (str | list[MessageParam]): A description of what the agent should
                achieve.
            model (str | None, optional): The composition or name of the model(s) to
                be used for achieving the `goal`.
            on_message (OnMessageCb | None, optional): Callback for new messages. If
                it returns `None`, stops and does not add the message.
            tools (list[Tool] | ToolCollection | None, optional): The tools for the
                agent. Defaults to default tools depending on the selected model.
            settings (AgentSettings | None, optional): The settings for the agent.
                Defaults to a default settings depending on the selected model.

        Returns:
            None

        Raises:
            MaxTokensExceededError: If the model reaches the maximum token limit
                defined in the agent settings.
            ModelRefusalError: If the model refuses to process the request.

        Example:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                agent.act("Open the settings menu")
                agent.act("Search for 'printer' in the search box")
                agent.act("Log in with username 'admin' and password '1234'")
            ```
        """
        goal_str = (
            goal
            if isinstance(goal, str)
            else "\n".join(msg.model_dump_json() for msg in goal)
        )
        self._reporter.add_message("User", f'act: "{goal_str}"')
        logger.debug(
            "VisionAgent received instruction to act towards the goal '%s'", goal_str
        )
        messages: list[MessageParam] = (
            [MessageParam(role="user", content=goal)] if isinstance(goal, str) else goal
        )
        model_choice = model or self._model_choice["act"]
        _settings = settings or self._get_default_settings_for_act(model_choice)
        _tools = self._build_tools(tools, model_choice)
        self._model_router.act(
            messages=messages,
            model_choice=model_choice,
            on_message=on_message,
            settings=_settings,
            tools=_tools,
        )

    def _build_tools(
        self, tools: list[Tool] | ToolCollection | None, model_choice: str
    ) -> ToolCollection:
        default_tools = self._get_default_tools_for_act(model_choice)
        if isinstance(tools, list):
            return ToolCollection(tools=default_tools + tools)
        if isinstance(tools, ToolCollection):
            return ToolCollection(default_tools) + tools
        return ToolCollection(tools=default_tools)

    def _get_default_settings_for_act(self, model_choice: str) -> ActSettings:  # noqa: ARG002
        return ActSettings()

    def _get_default_tools_for_act(self, model_choice: str) -> list[Tool]:  # noqa: ARG002
        return self._tools

    @overload
    def get(
        self,
        query: Annotated[str, Field(min_length=1)],
        response_schema: None = None,
        model: str | None = None,
        source: Optional[InputSource] = None,
    ) -> str: ...
    @overload
    def get(
        self,
        query: Annotated[str, Field(min_length=1)],
        response_schema: Type[ResponseSchema],
        model: str | None = None,
        source: Optional[InputSource] = None,
    ) -> ResponseSchema: ...

    @telemetry.record_call(exclude={"query", "source", "response_schema"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def get(
        self,
        query: Annotated[str, Field(min_length=1)],
        response_schema: Type[ResponseSchema] | None = None,
        model: str | None = None,
        source: Optional[InputSource] = None,
    ) -> ResponseSchema | str:
        """
        Retrieves information from an image or PDF based on the provided `query`.

        If no `source` is provided, a screenshot of the current screen is taken.

        Args:
            query (str): The query describing what information to retrieve.
            source (InputSource | None, optional): The source to extract information
                from. Can be a path to an image, PDF, or office document file,
                a PIL Image object or a data URL. Defaults to a screenshot of the
                current screen.
            response_schema (Type[ResponseSchema] | None, optional): A Pydantic model
                class that defines the response schema. If not provided, returns a
                string.
            model (str | None, optional): The composition or name of the model(s) to
                be used for retrieving information from the screen or image using the
                `query`. Note: `response_schema` is not supported by all models.
                PDF processing is only supported for Gemini models hosted on AskUI.

        Returns:
            ResponseSchema | str: The extracted information, `str` if no
                `response_schema` is provided.

        Raises:
            NotImplementedError: If PDF processing is not supported for the selected
                model.
            ValueError: If the `source` is not a valid PDF or image.

        Example:
            ```python
            from askui import ResponseSchemaBase, VisionAgent
            from PIL import Image
            import json

            class UrlResponse(ResponseSchemaBase):
                url: str

            class NestedResponse(ResponseSchemaBase):
                nested: UrlResponse

            class LinkedListNode(ResponseSchemaBase):
                value: str
                next: "LinkedListNode | None"

            with VisionAgent() as agent:
                # Get URL as string
                url = agent.get("What is the current url shown in the url bar?")

                # Get URL as Pydantic model from image at (relative) path
                response = agent.get(
                    "What is the current url shown in the url bar?",
                    response_schema=UrlResponse,
                    source="screenshot.png",
                )
                # Dump whole model
                print(response.model_dump_json(indent=2))
                # or
                response_json_dict = response.model_dump(mode="json")
                print(json.dumps(response_json_dict, indent=2))
                # or for regular dict
                response_dict = response.model_dump()
                print(response_dict["url"])

                # Get boolean response from PIL Image
                is_login_page = agent.get(
                    "Is this a login page?",
                    response_schema=bool,
                    source=Image.open("screenshot.png"),
                )
                print(is_login_page)

                # Get integer response
                input_count = agent.get(
                    "How many input fields are visible on this page?",
                    response_schema=int,
                )
                print(input_count)

                # Get float response
                design_rating = agent.get(
                    "Rate the page design quality from 0 to 1",
                    response_schema=float,
                )
                print(design_rating)

                # Get nested response
                nested = agent.get(
                    "Extract the URL and its metadata from the page",
                    response_schema=NestedResponse,
                )
                print(nested.nested.url)

                # Get recursive response
                linked_list = agent.get(
                    "Extract the breadcrumb navigation as a linked list",
                    response_schema=LinkedListNode,
                )
                current = linked_list
                while current:
                    print(current.value)
                    current = current.next

                # Get text from PDF
                text = agent.get(
                    "Extract all text from the PDF",
                    source="document.pdf",
                )
                print(text)
            ```
        """
        _source = source or ImageSource(self._agent_os.screenshot())
        _model = model or self._model_choice["get"]
        return self._data_extractor.get(
            query=query,
            source=_source,
            model=_model,
            response_schema=response_schema,
        )

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def _locate(
        self,
        locator: str | Locator,
        screenshot: Optional[InputSource] = None,
        model: ModelComposition | str | None = None,
    ) -> PointList:
        def locate_with_screenshot() -> PointList:
            _screenshot = load_image_source(
                self._agent_os.screenshot() if screenshot is None else screenshot
            )
            return self._model_router.locate(
                screenshot=_screenshot,
                locator=locator,
                model_choice=model or self._model_choice["locate"],
            )

        points = self._retry.attempt(locate_with_screenshot)
        self._reporter.add_message("ModelRouter", f"locate {len(points)} elements")
        logger.debug("ModelRouter locate: %d elements", len(points))
        return points

    @telemetry.record_call(exclude={"locator", "screenshot"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def locate(
        self,
        locator: str | Locator,
        screenshot: Optional[InputSource] = None,
        model: ModelComposition | str | None = None,
    ) -> Point:
        """
        Locates the first matching UI element identified by the provided locator.

        Args:
            locator (str | Locator): The identifier or description of the element to
                locate.
            screenshot (InputSource | None, optional): The screenshot to use for
                locating the element. Can be a path to an image file, a PIL Image object
                or a data URL. If `None`, takes a screenshot of the currently
                selected display.
            model (ModelComposition | str | None, optional): The composition or name
                of the model(s) to be used for locating the element using the `locator`.

        Returns:
            Point: The coordinates of the element as a tuple (x, y).

        Example:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                point = agent.locate("Submit button")
                print(f"Element found at coordinates: {point}")
            ```
        """
        self._reporter.add_message("User", f"locate first matching element {locator}")
        logger.debug(
            "VisionAgent received instruction to locate first matching element %s",
            locator,
        )
        return self._locate(locator, screenshot, model)[0]

    @telemetry.record_call(exclude={"locator", "screenshot"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def locate_all(
        self,
        locator: str | Locator,
        screenshot: Optional[InputSource] = None,
        model: ModelComposition | str | None = None,
    ) -> PointList:
        """
        Locates all matching UI elements identified by the provided locator.

        Note: Some LocateModels can only locate a single element. In this case, the
        returned list will have a length of 1.

        Args:
            locator (str | Locator): The identifier or description of the element to
                locate.
            screenshot (InputSource | None, optional): The screenshot to use for
                locating the element. Can be a path to an image file, a PIL Image object
                or a data URL. If `None`, takes a screenshot of the currently
                selected display.
            model (ModelComposition | str | None, optional): The composition or name
                of the model(s) to be used for locating the element using the `locator`.

        Returns:
            PointList: The coordinates of the elements as a list of tuples (x, y).

        Example:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                points = agent.locate_all("Submit button")
                print(f"Found {len(points)} elements at coordinates: {points}")
            ```
        """
        self._reporter.add_message("User", f"locate all matching UI elements {locator}")
        logger.debug(
            "VisionAgent received instruction to locate all matching UI elements %s",
            locator,
        )
        return self._locate(locator, screenshot, model)

    @telemetry.record_call()
    @validate_call
    def wait(
        self,
        sec: Annotated[float, Field(gt=0.0)],
    ) -> None:
        """
        Pauses the execution of the program for the specified number of seconds.

        Args:
            sec (float): The number of seconds to wait. Must be greater than `0.0`.

        Example:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                agent.wait(5)  # Pauses execution for 5 seconds
                agent.wait(0.5)  # Pauses execution for 500 milliseconds
            ```
        """
        time.sleep(sec)

    @telemetry.record_call()
    def close(self) -> None:
        self._agent_os.disconnect()
        self._reporter.generate()

    @telemetry.record_call()
    def open(self) -> None:
        self._agent_os.connect()

    @telemetry.record_call()
    def __enter__(self) -> Self:
        self.open()
        return self

    @telemetry.record_call(exclude={"exc_value", "traceback"})
    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        self.close()
