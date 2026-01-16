import logging
import time
import types
from abc import ABC
from typing import Annotated, Literal, Optional, Type, overload

from dotenv import load_dotenv
from pydantic import ConfigDict, Field, field_validator, validate_call
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

from askui.container import telemetry
from askui.data_extractor import DataExtractor
from askui.locators.locators import Locator
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCb
from askui.models.shared.settings import ActSettings, CachingSettings
from askui.models.shared.tools import Tool, ToolCollection
from askui.prompts.act_prompts import create_default_prompt
from askui.prompts.caching import CACHE_USE_PROMPT
from askui.tools.agent_os import AgentOs
from askui.tools.android.agent_os import AndroidAgentOs
from askui.tools.caching_tools import (
    ExecuteCachedTrajectory,
    RetrieveCachedTestExecutions,
)
from askui.utils.annotation_writer import AnnotationWriter
from askui.utils.cache_writer import CacheWriter
from askui.utils.image_utils import ImageSource
from askui.utils.source_utils import InputSource, load_image_source

from .models import ModelComposition
from .models.exceptions import ElementNotFoundError, WaitUntilError
from .models.model_router import ModelRouter, initialize_default_model_registry
from .models.models import (
    DetectedElement,
    ModelChoice,
    ModelName,
    ModelRegistry,
    TotalModelChoice,
)
from .models.types.geometry import Point, PointList
from .models.types.response_schemas import ResponseSchema
from .reporting import Reporter
from .retry import ConfigurableRetry, Retry

logger = logging.getLogger(__name__)


class AgentBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ASKUI__VA__",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",
    )
    model: ModelChoice | ModelComposition | str | None = Field(default=None)
    model_provider: str | None = Field(default=None)

    @field_validator("model_provider")
    @classmethod
    def validate_model_provider(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v if v.endswith("/") else f"{v}/"


class AgentBase(ABC):  # noqa: B024
    def __init__(
        self,
        reporter: Reporter,
        model: ModelChoice | ModelComposition | str | None,
        retry: Retry | None,
        models: ModelRegistry | None,
        tools: list[Tool] | None,
        agent_os: AgentOs | AndroidAgentOs,
        model_provider: str | None,
    ) -> None:
        load_dotenv()
        self._reporter = reporter
        self._agent_os = agent_os

        self._tools = tools or []
        settings = AgentBaseSettings()
        _model_provider = model_provider or settings.model_provider or ""
        self.model_name_selected_by_user: str | None = None
        model = model or settings.model
        if model and isinstance(model, str):
            self.model_name_selected_by_user = f"{_model_provider}{model}"

        self._model_router = self._init_model_router(
            reporter=self._reporter,
            models=models or {},
        )
        self._retry = retry or ConfigurableRetry(
            strategy="Exponential",
            base_delay=1000,
            retry_count=3,
            on_exception_types=(ElementNotFoundError,),
        )
        self._model = self._init_model(model)
        self._data_extractor = DataExtractor(
            reporter=self._reporter, models=models or {}
        )

        self.act_tool_collection = ToolCollection(tools=tools)
        self.act_tool_collection.add_agent_os(agent_os)

        self.act_settings = ActSettings()
        self.caching_settings = CachingSettings()

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

    def _init_model(
        self,
        model: ModelComposition | ModelChoice | str | None,
    ) -> TotalModelChoice:
        """Initialize the model choice based on the provided model parameter.

        Args:
            model: ModelComposition | ModelChoice | str | None: The model to
                initialize from. Can be a `ModelComposition`, `ModelChoice` dict, `str`,
                or `None`.

        Returns:
            TotalModelChoice: A dict with keys "act", "get", and "locate" mapping to
                model names (or a ModelComposition for "locate").
        """
        default_act_model = f"askui/{ModelName.CLAUDE__SONNET__4__20250514}"
        default_get_model = ModelName.ASKUI
        default_locate_model = ModelName.ASKUI
        if isinstance(model, ModelComposition):
            return {
                "act": default_act_model,
                "get": default_get_model,
                "locate": model,
            }
        if isinstance(model, str) or model is None:
            return {
                "act": model or default_act_model,
                "get": model or default_get_model,
                "locate": model or default_locate_model,
            }
        return {
            "act": model.get(
                "act",
                default_act_model,
            ),
            "get": model.get("get", default_get_model),
            "locate": model.get("locate", default_locate_model),
        }

    @overload
    def _get_model(self, model: str | None, type_: Literal["act", "get"]) -> str: ...
    @overload
    def _get_model(
        self, model: ModelComposition | str | None, type_: Literal["locate"]
    ) -> str | ModelComposition: ...
    def _get_model(
        self,
        model: ModelComposition | str | None,
        type_: Literal["act", "get", "locate"],
    ) -> str | ModelComposition:
        if model is None and self.model_name_selected_by_user:
            return self.model_name_selected_by_user

        if isinstance(model, ModelComposition):
            return model

        return self._model[type_]

    @telemetry.record_call(exclude={"goal", "on_message", "settings", "tools"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def act(
        self,
        goal: Annotated[str | list[MessageParam], Field(min_length=1)],
        model: str | None = None,
        on_message: OnMessageCb | None = None,
        tools: list[Tool] | ToolCollection | None = None,
        settings: ActSettings | None = None,
        caching_settings: CachingSettings | None = None,
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
                it returns `None`, stops and does not add the message. Cannot be used
                with caching_settings strategy "write" or "both".
            tools (list[Tool] | ToolCollection | None, optional): The tools for the
                agent. Defaults to default tools depending on the selected model.
            settings (AgentSettings | None, optional): The settings for the agent.
                Defaults to a default settings depending on the selected model.
            caching_settings (CachingSettings | None, optional): The caching settings
                for the act execution. Controls recording and replaying of action
                sequences (trajectories). Available strategies: "no" (default, no
                caching), "write" (record actions to cache file), "read" (replay from
                cached trajectories), "both" (read and write). Defaults to no caching.

        Returns:
            None

        Raises:
            MaxTokensExceededError: If the model reaches the maximum token limit
                defined in the agent settings.
            ModelRefusalError: If the model refuses to process the request.
            ValueError: If on_message callback is provided with caching strategy
                "write" or "both".

        Example:
            Basic usage without caching:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                agent.act("Open the settings menu")
                agent.act("Search for 'printer' in the search box")
                agent.act("Log in with username 'admin' and password '1234'")
            ```

            Recording actions to a cache file:
            ```python
            from askui import VisionAgent
            from askui.models.shared.settings import CachingSettings

            with VisionAgent() as agent:
                agent.act(
                    goal=(
                        "Fill out the login form with "
                        "username 'admin' and password 'secret123'"
                    ),
                    caching_settings=CachingSettings(
                        strategy="write",
                        cache_dir=".cache",
                        filename="login_flow.json"
                    )
                )
            ```

            Replaying cached actions:
            ```python
            from askui import VisionAgent
            from askui.models.shared.settings import CachingSettings

            with VisionAgent() as agent:
                agent.act(
                    goal="Log in to the application",
                    caching_settings=CachingSettings(
                        strategy="read",
                        cache_dir=".cache"
                    )
                )
                # Agent will automatically find and use "login_flow.json"
            ```

            Using both read and write modes:
            ```python
            from askui import VisionAgent
            from askui.models.shared.settings import CachingSettings

            with VisionAgent() as agent:
                agent.act(
                    goal="Complete the checkout process",
                    caching_settings=CachingSettings(
                        strategy="both",
                        cache_dir=".cache",
                        filename="checkout.json"
                    )
                )
                # Agent can use existing caches and will record new actions
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
        _model = self._get_model(model, "act")
        _settings = settings or self.act_settings

        _caching_settings: CachingSettings = caching_settings or self.caching_settings

        tools, on_message, cached_execution_tool = self._patch_act_with_cache(
            _caching_settings, _settings, tools, on_message
        )
        _tools = self._build_tools(tools, _model)

        if cached_execution_tool:
            cached_execution_tool.set_toolbox(_tools)

        self._model_router.act(
            messages=messages,
            model=_model,
            on_message=on_message,
            settings=_settings,
            tools=_tools,
        )

    def _build_tools(
        self, tools: list[Tool] | ToolCollection | None, _model: str
    ) -> ToolCollection:
        tool_collection = self.act_tool_collection
        if isinstance(tools, list):
            tool_collection.append_tool(*tools)
        if isinstance(tools, ToolCollection):
            tool_collection += tools
        return tool_collection

    def _patch_act_with_cache(
        self,
        caching_settings: CachingSettings,
        settings: ActSettings,
        tools: list[Tool] | ToolCollection | None,
        on_message: OnMessageCb | None,
    ) -> tuple[
        list[Tool] | ToolCollection, OnMessageCb | None, ExecuteCachedTrajectory | None
    ]:
        """Patch act settings and tools with caching functionality.

        Args:
            caching_settings: The caching settings to apply
            settings: The act settings to modify
            tools: The tools list to extend with caching tools
            on_message: The message callback (may be replaced for write mode)

        Returns:
            A tuple of (modified_tools, modified_on_message, cached_execution_tool)
        """
        caching_tools: list[Tool] = []
        cached_execution_tool: ExecuteCachedTrajectory | None = None

        # Setup read mode: add caching tools and modify system prompt
        if caching_settings.strategy in ["read", "both"]:
            cached_execution_tool = ExecuteCachedTrajectory(
                caching_settings.execute_cached_trajectory_tool_settings
            )
            caching_tools.extend(
                [
                    RetrieveCachedTestExecutions(caching_settings.cache_dir),
                    cached_execution_tool,
                ]
            )
            if settings.messages.system is None:
                settings.messages.system = create_default_prompt()
            settings.messages.system.cache_use = CACHE_USE_PROMPT

        # Add caching tools to the tools list
        if isinstance(tools, list):
            tools = caching_tools + tools
        elif isinstance(tools, ToolCollection):
            tools.append_tool(*caching_tools)
        else:
            tools = caching_tools

        # Setup write mode: create cache writer and set message callback
        if caching_settings.strategy in ["write", "both"]:
            cache_writer = CacheWriter(
                caching_settings.cache_dir, caching_settings.filename
            )
            if on_message is None:
                on_message = cache_writer.add_message_cb
            else:
                error_message = "Cannot use on_message callback when writing Cache"
                raise ValueError(error_message)

        return tools, on_message, cached_execution_tool

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
        _model = self._get_model(model, "get")
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
        retry: Optional[Retry] = None,
        model: ModelComposition | str | None = None,
    ) -> PointList:
        def locate_with_screenshot() -> PointList:
            _screenshot = load_image_source(
                self._agent_os.screenshot() if screenshot is None else screenshot
            )
            return self._model_router.locate(
                screenshot=_screenshot,
                locator=locator,
                model=self._get_model(model, "locate"),
            )

        retry = retry or self._retry
        points = retry.attempt(locate_with_screenshot)
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
        return self._locate(locator=locator, screenshot=screenshot, model=model)[0]

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
        return self._locate(locator=locator, screenshot=screenshot, model=model)

    @telemetry.record_call(exclude={"screenshot"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def locate_all_elements(
        self,
        screenshot: Optional[InputSource] = None,
        model: ModelComposition | None = None,
    ) -> list[DetectedElement]:
        """Locate all elements in the current screen using AskUI Models.

        Args:
            screenshot (InputSource | None, optional): The screenshot to use for
                locating the elements. Can be a path to an image file, a PIL Image
                object or a data URL. If `None`, takes a screenshot of the currently
                selected display.
            model (ModelComposition | None, optional): The model composition
                 to be used for locating the elements.

        Returns:
            list[DetectedElement]: A list of detected elements

        Example:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                detected_elements = agent.locate_all_elements()
                print(f"Found {len(detected_elements)} elements: {detected_elements}")
            ```
        """
        _screenshot = load_image_source(
            self._agent_os.screenshot() if screenshot is None else screenshot
        )
        return self._model_router.locate_all_elements(
            image=_screenshot, model=model or ModelName.ASKUI
        )

    @telemetry.record_call(exclude={"screenshot", "annotation_dir"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def annotate(
        self,
        screenshot: InputSource | None = None,
        annotation_dir: str = "annotations",
        model: ModelComposition | None = None,
    ) -> None:
        """Annotate the screenshot with the detected elements.
        Creates an interactive HTML file with the detected elements
        and saves it to the annotation directory.
        The HTML file can be opened in a browser to see the annotated image.
        The user can hover over the elements to see their names and text value
        and click on the box to copy the text value to the clipboard.

        Args:
            screenshot (ImageSource | None, optional): The screenshot to annotate.
                If `None`, takes a screenshot of the currently selected display.
            annotation_dir (str): The directory to save the annotated
                image. Defaults to "annotations".
            model (ModelComposition | None, optional): The composition
                of the model(s) to be used for annotating the image.
                If `None`, uses the default model.

        Example Using VisionAgent:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                agent.annotate()
            ```

        Example Using AndroidVisionAgent:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.annotate()
            ```

        Example Using VisionAgent with custom screenshot and annotation directory:
            ```python
            from askui import VisionAgent

            with VisionAgent() as agent:
                agent.annotate(screenshot="screenshot.png", annotation_dir="htmls")
            ```
        """
        if screenshot is None:
            screenshot = self._agent_os.screenshot()

        self._reporter.add_message("User", "annotate screenshot with detected elements")
        detected_elements = self.locate_all_elements(
            screenshot=screenshot,
            model=model,
        )
        annotated_html = AnnotationWriter(
            image=screenshot,
            elements=detected_elements,
        ).save_to_dir(annotation_dir)
        self._reporter.add_message(
            "AnnotationWriter", f"annotated HTML file saved to '{annotated_html}'"
        )

    @telemetry.record_call(exclude={"until"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def wait(
        self,
        until: Annotated[float, Field(gt=0.0)] | str | Locator,
        retry_count: Optional[Annotated[int, Field(gt=0)]] = None,
        delay: Optional[Annotated[float, Field(gt=0.0)]] = None,
        until_condition: Literal["appear", "disappear"] = "appear",
        model: ModelComposition | str | None = None,
    ) -> None:
        """
        Pauses execution or waits until a UI element appears or disappears.

        Args:
            until (float | str | Locator): If a float, pauses execution for the
                specified number of seconds (must be greater than 0.0). If a string
                or Locator, waits until the specified UI element appears or
                disappears on screen.
            retry_count (int | None): Number of retries when waiting for a UI
                element. Defaults to 3 if None.
            delay (int | None): Sleep duration in seconds between retries when
                waiting for a UI element. Defaults to 1 second if None.
            until_condition (Literal["appear", "disappear"]): The condition to wait
                until the element satisfies. Defaults to "appear".
            model (ModelComposition | str | None, optional): The composition or name
                of the model(s) to be used for locating the element using the
                `until` locator.

        Raises:
            WaitUntilError: If the UI element is not found after all retries.

        Example:
            ```python
            from askui import VisionAgent
            from askui.locators import loc

            with VisionAgent() as agent:
                # Wait for a specific duration
                agent.wait(5)  # Pauses execution for 5 seconds
                agent.wait(0.5)  # Pauses execution for 500 milliseconds

                # Wait for a UI element to appear
                agent.wait("Submit button", retry_count=5, delay=2)
                agent.wait("Login form")  # Uses default retries and sleep time
                agent.wait(loc.Text("Password"))  # Uses default retries and sleep time

                # Wait for a UI element to disappear
                agent.wait("Loading spinner", until_condition="disappear")

                # Wait using a specific model
                agent.wait("Submit button", model="custom_model")
            ```
        """
        if isinstance(until, float) or isinstance(until, int):
            self._reporter.add_message("User", f"wait {until} seconds")
            time.sleep(until)
            return

        self._reporter.add_message(
            "User", f"wait for element '{until}' to {until_condition}"
        )
        retry_count = retry_count if retry_count is not None else 3
        delay = delay if delay is not None else 1

        if until_condition == "appear":
            self._wait_for_appear(until, model, retry_count, delay)
        else:
            self._wait_for_disappear(until, model, retry_count, delay)

    def _wait_for_appear(
        self,
        locator: str | Locator,
        model: ModelComposition | str | None,
        retry_count: int,
        delay: float,
    ) -> None:
        """Wait for an element to appear on screen."""
        try:
            self._locate(
                locator,
                model=model,
                retry=ConfigurableRetry(
                    strategy="Fixed",
                    base_delay=int(delay * 1000),
                    retry_count=retry_count,
                    on_exception_types=(ElementNotFoundError,),
                ),
            )
            self._reporter.add_message(
                "VisionAgent", f"element '{locator}' appeared successfully"
            )
        except ElementNotFoundError as e:
            self._reporter.add_message(
                "VisionAgent",
                f"element '{locator}' failed to appear after {retry_count} retries",
            )
            raise WaitUntilError(
                e.locator, e.locator_serialized, retry_count, delay, "appear"
            ) from e

    def _wait_for_disappear(
        self,
        locator: str | Locator,
        model: ModelComposition | str | None,
        retry_count: int,
        delay: float,
    ) -> None:
        """Wait for an element to disappear from screen."""
        for i in range(retry_count):
            try:
                self._locate(
                    locator,
                    model=model,
                    retry=ConfigurableRetry(
                        strategy="Fixed",
                        base_delay=int(delay * 1000),
                        retry_count=1,
                        on_exception_types=(),
                    ),
                )
                logger.debug(
                    "Element still present, retrying... %d/%d", i + 1, retry_count
                )
                time.sleep(delay)
            except ElementNotFoundError:  # noqa: PERF203
                self._reporter.add_message(
                    "VisionAgent", f"element '{locator}' disappeared successfully"
                )
                return

        self._reporter.add_message(
            "VisionAgent",
            f"element '{locator}' failed to disappear after {retry_count} retries",
        )
        raise WaitUntilError(locator, str(locator), retry_count, delay, "disappear")

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
