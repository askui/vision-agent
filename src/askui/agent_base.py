import logging
import time
import types
from abc import ABC
from typing import Annotated, Literal, Optional, Type, overload

from dotenv import load_dotenv
from pydantic import ConfigDict, Field, validate_call
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

from askui.container import telemetry
from askui.data_extractor import DataExtractor
from askui.locators.locators import Locator
from askui.locators.serializers import AskUiLocatorSerializer, VlmLocatorSerializer
from askui.models.anthropic.factory import create_api_client
from askui.models.anthropic.messages_api import AnthropicMessagesApi
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCb
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.prompts import ActSystemPrompt
from askui.models.shared.settings import ActSettings, CachingSettings
from askui.models.shared.tools import Tool, ToolCollection
from askui.prompts.act_prompts import CACHE_USE_PROMPT
from askui.speaker.cache_executor import CacheExecutor
from askui.speaker.conversation import Conversation
from askui.speaker.speaker import Speakers
from askui.telemetry.otel import OtelSettings, setup_opentelemetry_tracing_for_askui_sdk
from askui.tools.agent_os import AgentOs
from askui.tools.android.agent_os import AndroidAgentOs
from askui.tools.caching_tools import (
    ExecuteCachedTrajectory,
    RetrieveCachedTestExecutions,
)
from askui.utils.annotation_writer import AnnotationWriter
from askui.utils.caching.cache_manager import CacheManager
from askui.utils.image_utils import ImageSource
from askui.utils.source_utils import InputSource, load_image_source

from .models.askui.ai_element_utils import AiElementCollection
from .models.askui.google_genai_api import AskUiGoogleGenAiApi
from .models.askui.inference_api import AskUiInferenceApi
from .models.askui.inference_api_settings import AskUiInferenceApiSettings
from .models.askui.models import AskUiGetModel, AskUiLocateModel
from .models.exceptions import ElementNotFoundError, WaitUntilError
from .models.models import (
    DetectedElement,
    GetModel,
    LocateModel,
    ModelName,
    Point,
    PointList,
)
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
    model: str | None = Field(default=None)


class AgentBase(ABC):  # noqa: B024
    def __init__(
        self,
        reporter: Reporter,
        retry: Retry | None,
        tools: list[Tool] | None,
        agent_os: AgentOs | AndroidAgentOs,
        act_model_name: str | None = None,
        get_model: GetModel | None = None,
        locate_model: LocateModel | None = None,
        messages_api: MessagesApi | None = None,
    ) -> None:
        load_dotenv()
        self._reporter = reporter
        self._agent_os: AgentOs | AndroidAgentOs = agent_os

        self._tools = tools or []

        # Store default model name (can be overridden in act() method)
        settings = AgentBaseSettings()
        self._act_default_model_name = (
            act_model_name or settings.model or ModelName.CLAUDE__SONNET__4_5__20250514
        )
        self._messages_api: MessagesApi | None = messages_api
        self._default_get_model: GetModel = get_model or self._get_default_get_model(
            reporter=self._reporter
        )
        self._default_locate_model: LocateModel = (
            locate_model or self._get_default_locate_model(reporter=self._reporter)
        )
        self._retry = retry or ConfigurableRetry(
            strategy="Exponential",
            base_delay=1000,
            retry_count=3,
            on_exception_types=(ElementNotFoundError,),
        )
        self._data_extractor = DataExtractor(reporter=self._reporter)
        self._locator_serializer = VlmLocatorSerializer()

    def _get_default_get_model(self, reporter: Reporter) -> GetModel:
        """Initialize default get model."""
        inference_api = AskUiInferenceApi(settings=AskUiInferenceApiSettings())
        google_genai_api = AskUiGoogleGenAiApi()
        get_model = AskUiGetModel(
            google_genai_api=google_genai_api,
            inference_api=inference_api,
        )

        return get_model

    def _get_default_locate_model(self, reporter: Reporter) -> LocateModel:
        """Initialize default locate model."""
        inference_api = AskUiInferenceApi(settings=AskUiInferenceApiSettings())
        locate_model = AskUiLocateModel(
            locator_serializer=AskUiLocatorSerializer(
                ai_element_collection=AiElementCollection(),
                reporter=reporter,
            ),
            inference_api=inference_api,
        )

        return locate_model

    def _get_default_messages_api(self) -> MessagesApi:
        """Get the default MessagesApi instance (AskUI provider).

        Returns:
            MessagesApi: Default AskUI MessagesApi instance
        """
        return AnthropicMessagesApi(
            client=create_api_client(api_provider="askui"),
            locator_serializer=self._locator_serializer,
        )

    @telemetry.record_call(exclude={"goal", "on_message", "settings", "tools"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def act(
        self,
        goal: Annotated[str | list[MessageParam], Field(min_length=1)],
        model_name: str | None = None,
        messages_api: MessagesApi | None = None,
        on_message: OnMessageCb | None = None,
        tools: list[Tool] | ToolCollection | None = None,
        speakers: Speakers | None = None,
        settings: ActSettings | None = None,
        caching_settings: CachingSettings | None = None,
        tracing_settings: OtelSettings | None = None,
    ) -> None:
        """
        Instructs the agent to achieve a specified goal through autonomous actions.

        The agent will analyze the screen, determine necessary steps, and perform
        actions to accomplish the goal. This may include clicking, typing, scrolling,
        and other interface interactions.

        Args:
            goal (str | list[MessageParam]): A description of what the agent should
                achieve.
            model_name (str | None, optional): The name of the model to use for
                achieving the goal. If not provided, uses the default model name from
                agent initialization or the default Claude model.
            messages_api (MessagesApi | None, optional): The MessagesApi instance to use
                for agent calls. If not provided, will use the default AskUI MessagesApi.
            on_message (OnMessageCb | None, optional): Callback for new messages. If
                it returns `None`, stops and does not add the message.
            tools (list[Tool] | ToolCollection | None, optional): The tools for the
                agent. Defaults to default tools.
            speakers (Speakers | None, optional): The speakers to use in the
                conversation. Defaults to the AskUIAgent and the CacheExecutor,
                depending on the caching settings.
            settings (ActSettings | None, optional): The settings for the agent.
                Defaults to default settings.
            caching_settings (CachingSettings | None, optional): The caching settings
                for the act execution. Controls recording and replaying of action
                sequences (trajectories). Available strategies: "no" (default, no
                caching), "write" (record actions to cache file), "read" (replay from
                cached trajectories), "both" (read and write). Defaults to no caching.
            tracing_settings (OtelSettings | None, optional): Settings for tracing.

        Returns:
            None

        Raises:
            MaxTokensExceededError: If the model reaches the maximum token limit
                defined in the agent settings.
            ModelRefusalError: If the model refuses to process the request.

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
            from askui.models.shared.settings import CachingSettings, CacheWritingSettings

            with VisionAgent() as agent:
                agent.act(
                    goal=(
                        "Fill out the login form with "
                        "username 'admin' and password 'secret123'"
                    ),
                    caching_settings=CachingSettings(
                        strategy="execute",
                        cache_dir=".askui_cache",
                        writing_settings=CacheWritingSettings(
                            filename="login_flow.json"
                        )

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
                        strategy="record",
                        cache_dir=".askui_cache"
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
                        writing_settings=CacheWritingSettings(
                            filename="checkout.json"
                        )
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

        # Resolve model_name: parameter > instance default
        _model_name = model_name or self._act_default_model_name

        # Resolve MessagesApi: parameter > instance default > default AskUI
        _messages_api = (
            messages_api or self._messages_api or self._get_default_messages_api()
        )

        _settings = settings or self._get_default_settings_for_act()

        _caching_settings: CachingSettings = (
            caching_settings or self._get_default_caching_settings_for_act()
        )

        _tracing_settings = tracing_settings
        if _tracing_settings is not None:
            setup_opentelemetry_tracing_for_askui_sdk(tracing_settings)

        _tools = self._build_tools(tools)

        _speakers = self._get_default_speakers(speakers)

        if _caching_settings.strategy is not None:
            # Extract execution settings for CacheExecutor
            skip_visual_validation = False
            if _caching_settings.execution_settings is not None:
                skip_visual_validation = (
                    _caching_settings.execution_settings.skip_visual_validation
                )

            _speakers.add_speaker(
                CacheExecutor(skip_visual_validation=skip_visual_validation)
            )
            _cache_manager = self._patch_act_with_cache(
                _caching_settings, _settings, _tools, goal_str, _messages_api
            )
        else:
            _cache_manager = None

        _conversation = Conversation(
            speakers=_speakers,
            reporter=self._reporter,
            cache_manager=_cache_manager,
        )

        _conversation.start(
            messages=messages,
            model_name=_model_name,
            messages_api=_messages_api,
            on_message=on_message,
            settings=_settings,
            tools=_tools,
            reporters=[self._reporter],
        )

    def _build_tools(self, tools: list[Tool] | ToolCollection | None) -> ToolCollection:
        default_tools = self._get_default_tools_for_act()
        if isinstance(tools, list):
            return ToolCollection(tools=default_tools + tools)
        if isinstance(tools, ToolCollection):
            return ToolCollection(default_tools) + tools
        return ToolCollection(tools=default_tools)

    def _patch_act_with_cache(
        self,
        caching_settings: CachingSettings,
        settings: ActSettings,
        toolbox: ToolCollection,
        goal: str | None = None,
        messages_api: MessagesApi | None = None,
    ) -> CacheManager | None:
        """Patch act settings and toolbox with caching functionality.

        Args:
            caching_settings: The caching settings to apply
            settings: The act settings to modify
            toolbox: The toolbox to extend with caching tools
            goal: The goal string (used for cache metadata)

        Returns:
            CacheManager instance if recording is active, None otherwise
        """
        logger.debug("Setting up caching")
        caching_tools: list[Tool] = []

        # Setup read mode: add caching tools and modify system prompt
        if caching_settings.strategy in ["execute", "both"]:
            from askui.tools.caching_tools import VerifyCacheExecution

            caching_tools.extend(
                [
                    RetrieveCachedTestExecutions(caching_settings.cache_dir),
                    ExecuteCachedTrajectory(),
                    VerifyCacheExecution(),
                ]
            )
            if settings.messages.system is None:
                settings.messages.system = ActSystemPrompt()
            settings.messages.system.cache_use = CACHE_USE_PROMPT
            logger.debug("Added cache usage instructions to system prompt")

        # Add caching tools to the toolbox
        if caching_tools:
            toolbox.append_tool(*caching_tools)

        # Setup write mode: start cache recording
        if caching_settings.strategy in ["read", "write", "both"]:
            cache_manager = CacheManager()
            cache_manager.start_recording(
                cache_dir=caching_settings.cache_dir,
                file_name=caching_settings.writing_settings.filename,
                goal=goal,
                toolbox=toolbox,
                cache_writer_settings=caching_settings.writing_settings,
                messages_api=messages_api,
            )
            return cache_manager

        return None

    def _get_default_settings_for_act(self) -> ActSettings:
        return ActSettings()

    def _get_default_caching_settings_for_act(self) -> CachingSettings:
        return CachingSettings()

    def _get_default_tools_for_act(self) -> list[Tool]:
        return self._tools

    def _get_default_speakers(self, speakers: Speakers | None) -> Speakers:
        if speakers:
            return Speakers() + speakers
        return Speakers()

    @overload
    def get(
        self,
        query: Annotated[str, Field(min_length=1)],
        response_schema: None = None,
        get_model: GetModel | None = None,
        source: Optional[InputSource] = None,
    ) -> str: ...
    @overload
    def get(
        self,
        query: Annotated[str, Field(min_length=1)],
        response_schema: Type[ResponseSchema],
        get_model: GetModel | None = None,
        source: Optional[InputSource] = None,
    ) -> ResponseSchema: ...

    @telemetry.record_call(exclude={"query", "source", "response_schema"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def get(
        self,
        query: Annotated[str, Field(min_length=1)],
        response_schema: Type[ResponseSchema] | None = None,
        get_model: GetModel | None = None,
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
            get_model (GetModel | None, optional): The GetModel instance to use directly.
                If provided, takes precedence over `model` string.

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
        if get_model is not None:
            # Use provided GetModel directly
            from askui.utils.source_utils import load_source

            # Extract PIL Image from ImageSource if needed
            _input_source = (
                _source.root if isinstance(_source, ImageSource) else _source
            )
            _loaded_source = load_source(_input_source)
            return get_model.get(
                query=query,
                source=_loaded_source,
                response_schema=response_schema,
            )
        # Use default get model
        return self._data_extractor.get(
            query=query,
            source=_source,
            response_schema=response_schema,
        )

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def _locate(
        self,
        locator: str | Locator,
        locate_model: LocateModel,
        screenshot: Optional[InputSource] = None,
        retry: Optional[Retry] = None,
    ) -> PointList:
        def locate_with_screenshot() -> PointList:
            _screenshot = load_image_source(
                self._agent_os.screenshot() if screenshot is None else screenshot
            )

            return locate_model.locate(
                locator=locator,
                image=_screenshot,
            )

        retry = retry or self._retry
        points = retry.attempt(locate_with_screenshot)
        self._reporter.add_message("Agent", f"locate {len(points)} elements")
        logger.debug("Agent locate: %d elements", len(points))
        return points

    @telemetry.record_call(exclude={"locator", "screenshot"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def locate(
        self,
        locator: str | Locator,
        screenshot: Optional[InputSource] = None,
        locate_model: LocateModel | None = None,
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
            locate_model (LocateModel | None, optional): The model instance to be used
                for locating the element using the `locator`.

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
        _locate_model = locate_model or self._default_locate_model
        return self._locate(
            locator=locator,
            screenshot=screenshot,
            locate_model=_locate_model,
        )[0]

    @telemetry.record_call(exclude={"locator", "screenshot"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def locate_all(
        self,
        locator: str | Locator,
        screenshot: Optional[InputSource] = None,
        locate_model: LocateModel | None = None,
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
            locate_model (LocateModel | None, optional): The model instance to be used
                for locating the element using the `locator`.

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
        _locate_model = locate_model or self._default_locate_model
        return self._locate(
            locator=locator,
            screenshot=screenshot,
            locate_model=_locate_model,
        )

    @telemetry.record_call(exclude={"screenshot"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def locate_all_elements(
        self,
        screenshot: Optional[InputSource] = None,
    ) -> list[DetectedElement]:
        """Locate all elements in the current screen using AskUI Models.

        Args:
            screenshot (InputSource | None, optional): The screenshot to use for
                locating the elements. Can be a path to an image file, a PIL Image
                object or a data URL. If `None`, takes a screenshot of the currently
                selected display.

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
        return self._default_locate_model.locate_all_elements(image=_screenshot)

    @telemetry.record_call(exclude={"screenshot", "annotation_dir"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def annotate(
        self,
        screenshot: InputSource | None = None,
        annotation_dir: str = "annotations",
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
        locate_model: LocateModel | None = None,
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
            locate_model (LocateModel | None, optional): The locate model to use
                for locating the element. If None, uses the default locate model.

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

                # Wait using a specific locate model
                custom_model = CustomLocateModel(...)
                agent.wait("Submit button", locate_model=custom_model)
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
            self._wait_for_appear(until, locate_model, retry_count, delay)
        else:
            self._wait_for_disappear(until, locate_model, retry_count, delay)

    def _wait_for_appear(
        self,
        locator: str | Locator,
        locate_model: LocateModel | None,
        retry_count: int,
        delay: float,
    ) -> None:
        """Wait for an element to appear on screen."""
        try:
            _locate_model = locate_model or self._default_locate_model
            self._locate(
                locator,
                locate_model=_locate_model,
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
        locate_model: LocateModel | None,
        retry_count: int,
        delay: float,
    ) -> None:
        """Wait for an element to disappear from screen."""
        for i in range(retry_count):
            try:
                _locate_model = locate_model or self._default_locate_model
                self._locate(
                    locator,
                    locate_model=_locate_model,
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
