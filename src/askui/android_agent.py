import logging
import time
import types
from typing import Annotated, Optional, Type, overload

from dotenv import load_dotenv
from pydantic import ConfigDict, Field, validate_call

from askui.container import telemetry
from askui.locators.locators import Locator
from askui.models.shared.computer_agent_cb_param import OnMessageCb
from askui.models.shared.computer_agent_message_param import MessageParam
from askui.models.shared.tools import ToolCollection
from askui.tools.android.agent_os import ANDROID_KEY
from askui.tools.android.agent_os_handler import AndroidAgentOsHandler
from askui.tools.android.ppadb_agent_os import PpadbAgentOs
from askui.tools.android.tools import (
    AndroidDragAndDropTool,
    AndroidKeyCombinationTool,
    AndroidKeyTapEventTool,
    AndroidScreenshotTool,
    AndroidShellTool,
    AndroidSwipeTool,
    AndroidTapTool,
    AndroidTypeTool,
)
from askui.tools.exception_tool import ExceptionTool
from askui.utils.image_utils import ImageSource, Img

from .logger import configure_logging, logger
from .models import ModelComposition
from .models.exceptions import ElementNotFoundError
from .models.model_router import ModelRouter, initialize_default_android_model_registry
from .models.models import (
    ModelChoice,
    ModelName,
    ModelRegistry,
    Point,
    TotalModelChoice,
)
from .models.types.response_schemas import ResponseSchema
from .reporting import CompositeReporter, Reporter
from .retry import ConfigurableRetry, Retry


class AndroidVisionAgent:
    """ """

    @telemetry.record_call(exclude={"model_router", "reporters", "tools"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        log_level: int | str = logging.INFO,
        reporters: list[Reporter] | None = None,
        model: ModelChoice | ModelComposition | str | None = None,
        retry: Retry | None = None,
        models: ModelRegistry | None = None,
    ) -> None:
        load_dotenv()
        configure_logging(level=log_level)
        self.os = PpadbAgentOs()
        self._reporter = CompositeReporter(reporters=reporters)
        self._act_agent_os_handler = AndroidAgentOsHandler(self.os, self._reporter)
        self.act_tool_collection = ToolCollection(
            tools=[
                AndroidScreenshotTool(self._act_agent_os_handler),
                AndroidTapTool(self._act_agent_os_handler),
                AndroidTypeTool(self._act_agent_os_handler),
                AndroidDragAndDropTool(self._act_agent_os_handler),
                AndroidKeyTapEventTool(self._act_agent_os_handler),
                AndroidSwipeTool(self._act_agent_os_handler),
                AndroidKeyCombinationTool(self._act_agent_os_handler),
                AndroidShellTool(self._act_agent_os_handler),
                ExceptionTool(),
            ]
        )
        _models = initialize_default_android_model_registry(
            tool_collection=self.act_tool_collection,
            reporter=self._reporter,
        )
        _models.update(models or {})
        self._model_router = ModelRouter(
            reporter=self._reporter,
            models=_models,
        )
        self.model = model
        self._retry = retry or ConfigurableRetry(
            strategy="Exponential",
            base_delay=1000,
            retry_count=3,
            on_exception_types=(ElementNotFoundError,),
        )
        self._model_choice = self._initialize_model_choice(model)

    def _initialize_model_choice(
        self, model_choice: ModelComposition | ModelChoice | str | None
    ) -> TotalModelChoice:
        """Initialize the model choice based on the provided model parameter.

        Args:
            model (ModelComposition | ModelChoice | str | None):
            The model to initialize from. Can be a ModelComposition,
            ModelChoice dict, string, or None.

        Returns:
            TotalModelChoice: A dict with keys "act", "get", and "locate"
            mapping to model names (or a ModelComposition for "locate").
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

    @overload
    def tap(
        self,
        target: str | Locator,
        model: ModelComposition | str | None = None,
    ) -> None: ...

    @overload
    def tap(
        self,
        target: Point,
        model: ModelComposition | str | None = None,
    ) -> None: ...

    @telemetry.record_call(exclude={"locator"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def tap(
        self,
        target: str | Locator | tuple[int, int],
        model: ModelComposition | str | None = None,
    ) -> None:
        """
        Taps on the specified target.

        Args:
            target (str | Locator | Point): The target to tap on. Can be a locator, a point, or a string.
            model (ModelComposition | str | None, optional): The composition or name of the model(s) to be used for tapping on the target.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.tap("Submit button")
                agent.tap((100, 100))
        """
        msg = "tap"
        if isinstance(target, tuple):
            msg += f" at ({target[0]}, {target[1]})"
            self._reporter.add_message("User", msg)
            self.os.tap(target[0], target[1])
        else:
            msg += f" on {target}"
            self._reporter.add_message("User", msg)
            logger.debug("VisionAgent received instruction to click on %s", target)
            point = self._locate(locator=target, model=model)
            self.os.tap(point[0], point[1])

    def _locate(
        self,
        locator: str | Locator,
        screenshot: Optional[Img] = None,
        model: ModelComposition | str | None = None,
    ) -> Point:
        def locate_with_screenshot() -> Point:
            _screenshot = ImageSource(
                self.os.screenshot() if screenshot is None else screenshot
            )
            return self._model_router.locate(
                screenshot=_screenshot,
                locator=locator,
                model_choice=model or self._model_choice["locate"],
            )

        point = self._retry.attempt(locate_with_screenshot)
        self._reporter.add_message("ModelRouter", f"locate: ({point[0]}, {point[1]})")
        logger.debug("ModelRouter locate: (%d, %d)", point[0], point[1])
        return point

    @telemetry.record_call(exclude={"locator", "screenshot"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def locate(
        self,
        locator: str | Locator,
        screenshot: Optional[Img] = None,
        model: ModelComposition | str | None = None,
    ) -> Point:
        """
        Locates the UI element identified by the provided locator.

        Args:
            locator (str | Locator): The identifier or description of the element to locate.
            screenshot (Img | None, optional): The screenshot to use for locating the element. Can be a path to an image file, a PIL Image object or a data URL. If `None`, takes a screenshot of the currently selected display.
            model (ModelComposition | str | None, optional): The composition or name of the model(s) to be used for locating the element using the `locator`.

        Returns:
            Point: The coordinates of the element as a tuple (x, y).

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                point = agent.locate("Submit button")
                print(f"Element found at coordinates: {point}")
            ```
        """
        self._reporter.add_message("User", f"locate {locator}")
        logger.debug("VisionAgent received instruction to locate %s", locator)
        return self._locate(locator, screenshot, model)

    @telemetry.record_call(exclude={"text"})
    @validate_call
    def type(
        self,
        text: Annotated[str, Field(min_length=1)],
    ) -> None:
        """
        Types the specified text as if it were entered on a keyboard.

        Args:
            text (str): The text to be typed. Must be at least `1` character long.
            Only ASCII printable characters are supported. other characters will raise an error.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.type("Hello, world!")  # Types "Hello, world!"
                agent.type("user@example.com")  # Types an email address
                agent.type("password123")  # Types a password
            ```
        """
        self._reporter.add_message("User", f'type: "{text}"')
        logger.debug("VisionAgent received instruction to type '%s'", text)
        self.os.type(text)

    @overload
    def get(
        self,
        query: Annotated[str, Field(min_length=1)],
        response_schema: None = None,
        model: str | None = None,
        image: Optional[Img] = None,
    ) -> str: ...
    @overload
    def get(
        self,
        query: Annotated[str, Field(min_length=1)],
        response_schema: Type[ResponseSchema],
        model: str | None = None,
        image: Optional[Img] = None,
    ) -> ResponseSchema: ...

    @telemetry.record_call(exclude={"query", "image", "response_schema"})
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def get(
        self,
        query: Annotated[str, Field(min_length=1)],
        response_schema: Type[ResponseSchema] | None = None,
        model: str | None = None,
        image: Optional[Img] = None,
    ) -> ResponseSchema | str:
        """
        Retrieves information from an image (defaults to a screenshot of the current screen) based on the provided query.

        Args:
            query (str): The query describing what information to retrieve.
            image (Img | None, optional): The image to extract information from. Defaults to a screenshot of the current screen. Can be a path to an image file, a PIL Image object or a data URL.
            response_schema (Type[ResponseSchema] | None, optional): A Pydantic model class that defines the response schema. If not provided, returns a string.
            model (str | None, optional): The composition or name of the model(s) to be used for retrieving information from the screen or image using the `query`. Note: `response_schema` is not supported by all models.

        Returns:
            ResponseSchema | str: The extracted information, `str` if no `response_schema` is provided.

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

            with AndroidVisionAgent() as agent:
                # Get URL as string
                url = agent.get("What is the current url shown in the url bar?")

                # Get URL as Pydantic model from image at (relative) path
                response = agent.get(
                    "What is the current url shown in the url bar?",
                    response_schema=UrlResponse,
                    image="screenshot.png",
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
                    image=Image.open("screenshot.png"),
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
            ```
        """
        logger.debug("VisionAgent received instruction to get '%s'", query)
        _image = ImageSource(self.os.screenshot() if image is None else image)
        self._reporter.add_message("User", f'get: "{query}"', image=_image.root)
        response = self._model_router.get(
            image=_image,
            query=query,
            response_schema=response_schema,
            model_choice=model or self._model_choice["get"],
        )
        message_content = (
            str(response)
            if isinstance(response, (str, bool, int, float))
            else response.model_dump()
        )
        self._reporter.add_message("Agent", message_content)
        return response

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
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.wait(5)  # Pauses execution for 5 seconds
                agent.wait(0.5)  # Pauses execution for 500 milliseconds
            ```
        """
        time.sleep(sec)

    @telemetry.record_call()
    @validate_call
    def key_tap(
        self,
        key: ANDROID_KEY,
    ) -> None:
        """
        Taps the specified key on the Android device.

        Args:
            key (ANDROID_KEY): The key to tap.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.key_tap("HOME")  # Taps the home key
                agent.key_tap("BACK")  # Taps the back key
            ```
        """
        self.os.key_tap(key)

    @telemetry.record_call()
    @validate_call
    def key_combination(
        self,
        keys: Annotated[list[ANDROID_KEY], Field(min_length=2)],
        duration_in_ms: int = 100,
    ) -> None:
        """
        Taps the specified keys on the Android device.

        Args:
            keys (list[ANDROID_KEY]): The keys to tap.
            duration_in_ms (int, optional): The duration in milliseconds to hold the key combination. Default is 100ms.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.key_combination(["HOME", "BACK"])  # Taps the home key and then the back key
                agent.key_combination(["HOME", "BACK"], duration_in_ms=200)  # Taps the home key and then the back key for 200ms.
            ```
        """
        self.os.key_combination(keys, duration_in_ms)

    @telemetry.record_call()
    @validate_call
    def shell(
        self,
        command: str,
    ) -> str:
        """
        Executes a shell command on the Android device.

        Args:
            command (str): The shell command to execute.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.shell("pm list packages")  # Lists all installed packages
                agent.shell("dumpsys battery")  # Displays battery information
            ```
        """
        return self.os.shell(command)

    @telemetry.record_call()
    @validate_call
    def drag_and_drop(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_in_ms: int = 1000,
    ) -> None:
        """
        Drags and drops the specified target.

        Args:
            x1 (int): The x-coordinate of the starting point.
            y1 (int): The y-coordinate of the starting point.
            x2 (int): The x-coordinate of the ending point.
            y2 (int): The y-coordinate of the ending point.
            duration_in_ms (int, optional): The duration in milliseconds to hold the drag and drop. Default is 1000ms.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.drag_and_drop(100, 100, 200, 200)  # Drags and drops from (100, 100) to (200, 200)
                agent.drag_and_drop(100, 100, 200, 200, duration_in_ms=2000)  # Drags and drops from (100, 100) to (200, 200) with a 2000ms duration
        """
        self.os.drag_and_drop(x1, y1, x2, y2, duration_in_ms)

    @telemetry.record_call()
    @validate_call
    def swipe(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_in_ms: int = 1000,
    ) -> None:
        """
        Swipes the specified target.

        Args:
            x1 (int): The x-coordinate of the starting point.
            y1 (int): The y-coordinate of the starting point.
            x2 (int): The x-coordinate of the ending point.
            y2 (int): The y-coordinate of the ending point.
            duration_in_ms (int, optional): The duration in milliseconds to hold the swipe. Default is 1000ms.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.swipe(100, 100, 200, 200)  # Swipes from (100, 100) to (200, 200)
                agent.swipe(100, 100, 200, 200, duration_in_ms=2000)  # Swipes from (100, 100) to (200, 200) with a 2000ms duration
        """
        self.os.swipe(x1, y1, x2, y2, duration_in_ms)

    @telemetry.record_call(
        exclude={"device_sn"},
    )
    @validate_call
    def set_device_by_serial_number(
        self,
        device_sn: str,
    ) -> None:
        """
        Sets the active device for screen interactions by name.

        Args:
            device_sn (str): The serial number of the device to set as active.

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.set_device_by_serial_number("Pixel 6")  # Sets the active device to the Pixel 6
        """
        self.os.set_device_by_serial_number(device_sn)

    @telemetry.record_call(exclude={"goal", "on_message"})
    @validate_call
    def act(
        self,
        goal: Annotated[str | list[MessageParam], Field(min_length=1)],
        model: str | None = None,
        on_message: OnMessageCb | None = None,
    ) -> None:
        """
        Instructs the agent to achieve a specified goal through autonomous actions.

        The agent will analyze the screen, determine necessary steps, and perform actions
        to accomplish the goal. This may include clicking, typing, scrolling, and other
        interface interactions.

        Args:
            goal (str | list[MessageParam]): A description of what the agent should achieve.
            model (str | None, optional): The composition or name of the model(s) to be used for achieving the `goal`.
            on_message (OnMessageCb | None, optional): Callback for new messages. If it returns `None`, stops and does not add the message.

        Returns:
            None

        Example:
            ```python
            from askui import AndroidVisionAgent

            with AndroidVisionAgent() as agent:
                agent.act("Open the settings menu")
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
        self._model_router.act(messages, model or self._model_choice["act"], on_message)

    @telemetry.record_call(flush=True)
    def close(self) -> None:
        """Disconnects from the Android device."""
        self.os.disconnect()
        self._reporter.generate()

    @telemetry.record_call()
    def open(self) -> None:
        """Connects to the Android device."""
        self.os.connect()

    @telemetry.record_call()
    def __enter__(self) -> "AndroidVisionAgent":
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
