import pathlib
import subprocess
import sys
import time
import types
import uuid
from typing import Literal, Type

import grpc
from google.protobuf.json_format import MessageToDict
from PIL import Image
from typing_extensions import Self, override

from askui.container import telemetry
from askui.logger import logger
from askui.reporting import NULL_REPORTER, Reporter
from askui.tools.agent_os import (
    AgentOs,
    Coordinate,
    Display,
    DisplaysListResponse,
    ModifierKey,
    PcKey,
)
from askui.tools.askui.askui_controller_settings import AskUiControllerSettings
from askui.tools.askui.askui_ui_controller_grpc.generated import (
    Controller_V1_pb2 as controller_v1_pbs,
)
from askui.tools.askui.askui_ui_controller_grpc.generated import (
    Controller_V1_pb2_grpc as controller_v1,
)
from askui.tools.askui.askui_ui_controller_grpc.generated.AgentOS_Send_Request_2501 import (  # noqa: E501
    RenderObjectStyle,
)
from askui.tools.askui.askui_ui_controller_grpc.generated.AgentOS_Send_Response_2501 import (  # noqa: E501
    AskuiAgentosSendResponseSchema,
)
from askui.tools.askui.command_helpers import (
    create_clear_render_objects_command,
    create_delete_render_object_command,
    create_get_mouse_position_command,
    create_image_command,
    create_line_command,
    create_quad_command,
    create_set_mouse_position_command,
    create_text_command,
    create_update_render_object_command,
)
from askui.utils.image_utils import draw_point_on_image

from ..utils import process_exists, wait_for_port
from .exceptions import (
    AskUiControllerOperationFailedError,
    AskUiControllerOperationTimeoutError,
)


class AskUiControllerServer:
    """
    Concrete implementation of `ControllerServer` for managing the AskUI Remote Device
    Controller process.
    Handles process discovery, startup, and shutdown for the native controller binary.

    Args:
        settings (AskUiControllerSettings | None, optional): Settings for the AskUI.
    """

    def __init__(self, settings: AskUiControllerSettings | None = None) -> None:
        self._process: subprocess.Popen[bytes] | None = None
        self._settings = settings or AskUiControllerSettings()

    def _start_process(
        self,
        path: pathlib.Path,
        args: str | None = None,
    ) -> None:
        commands = [str(path)]
        if args:
            commands.extend(args.split())
        self._process = subprocess.Popen(commands)
        wait_for_port(23000)

    def start(self, clean_up: bool = False) -> None:
        """
        Start the controller process.

        Args:
            clean_up (bool, optional): Whether to clean up existing processes
                (only on Windows) before starting. Defaults to `False`.
        """
        if (
            sys.platform == "win32"
            and clean_up
            and process_exists("AskuiRemoteDeviceController.exe")
        ):
            self.clean_up()
        logger.debug(
            "Starting AskUI Remote Device Controller: %s",
            self._settings.controller_path,
        )
        self._start_process(
            self._settings.controller_path, self._settings.controller_args
        )
        time.sleep(0.5)

    def clean_up(self) -> None:
        subprocess.run("taskkill.exe /IM AskUI*")
        time.sleep(0.1)

    def stop(self, force: bool = False) -> None:
        """
        Stop the controller process.

        Args:
            force (bool, optional): Whether to forcefully terminate the process.
                Defaults to `False`.
        """
        if self._process is None:
            return  # Nothing to stop

        try:
            if force:
                self._process.kill()
                if sys.platform == "win32":
                    self.clean_up()
            else:
                self._process.terminate()
        except Exception as e:  # noqa: BLE001 - We want to catch all other exceptions here
            error = AskUiControllerOperationFailedError(
                "stop AskUI Remote Device Controller",
                e,
            )
            logger.error(str(error))
        finally:
            self._process = None


class AskUiControllerClient(AgentOs):
    """
    Implementation of `AgentOs` that communicates with the AskUI Remote Device
    Controller via gRPC.

    Args:
        reporter (Reporter): Reporter used for reporting with the `"AgentOs"`.
        display (int, optional): Display number to use. Defaults to `1`.
        controller_server (AskUiControllerServer | None, optional): Custom controller
            server. Defaults to `ControllerServer`.
    """

    @telemetry.record_call(exclude={"reporter", "controller_server"})
    def __init__(
        self,
        reporter: Reporter = NULL_REPORTER,
        display: int = 1,
        controller_server: AskUiControllerServer | None = None,
    ) -> None:
        self._stub: controller_v1.ControllerAPIStub | None = None
        self._channel: grpc.Channel | None = None
        self._session_info: controller_v1_pbs.SessionInfo | None = None
        self._pre_action_wait = 0
        self._post_action_wait = 0.05
        self._max_retries = 10
        self._display = display
        self._reporter = reporter
        self._controller_server = controller_server or AskUiControllerServer()
        self._session_guid = "{" + str(uuid.uuid4()) + "}"

    @telemetry.record_call()
    @override
    def connect(self) -> None:
        """
        Establishes a connection to the AskUI Remote Device Controller.

        This method starts the controller server, establishes a gRPC channel,
        creates a session, and sets up the initial display.
        """
        self._controller_server.start()
        self._channel = grpc.insecure_channel(
            "localhost:23000",
            options=[
                ("grpc.max_send_message_length", 2**30),
                ("grpc.max_receive_message_length", 2**30),
                ("grpc.default_deadline", 300000),
            ],
        )
        self._stub = controller_v1.ControllerAPIStub(self._channel)
        self._start_session()
        self._start_execution()
        self.set_display(self._display)

    def _run_recorder_action(
        self,
        acion_class_id: controller_v1_pbs.ActionClassID,
        action_parameters: controller_v1_pbs.ActionParameters,
    ) -> controller_v1_pbs.Response_RunRecordedAction:
        time.sleep(self._pre_action_wait)
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        response: controller_v1_pbs.Response_RunRecordedAction = (
            self._stub.RunRecordedAction(
                controller_v1_pbs.Request_RunRecordedAction(
                    sessionInfo=self._session_info,
                    actionClassID=acion_class_id,
                    actionParameters=action_parameters,
                )
            )
        )

        time.sleep((response.requiredMilliseconds / 1000))
        num_retries = 0
        for _ in range(self._max_retries):
            assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
                "Stub is not initialized"
            )
            poll_response: controller_v1_pbs.Response_Poll = self._stub.Poll(
                controller_v1_pbs.Request_Poll(
                    sessionInfo=self._session_info,
                    pollEventID=controller_v1_pbs.PollEventID.PollEventID_ActionFinished,
                )
            )
            if (
                poll_response.pollEventParameters.actionFinished.actionID
                == response.actionID
            ):
                break
            time.sleep(self._post_action_wait)
            num_retries += 1
        if num_retries == self._max_retries - 1:
            raise AskUiControllerOperationTimeoutError
        return response

    @telemetry.record_call()
    @override
    def disconnect(self) -> None:
        """
        Terminates the connection to the AskUI Remote Device Controller.

        This method stops the execution, ends the session, closes the gRPC channel,
        and stops the controller server.
        """
        self._stop_execution()
        self._stop_session()
        if self._channel is not None:
            self._channel.close()
        self._controller_server.stop()

    @telemetry.record_call()
    def __enter__(self) -> Self:
        """
        Context manager entry point that establishes the connection.

        Returns:
            Self: The instance of AskUiControllerClient.
        """
        self.connect()
        return self

    @telemetry.record_call(exclude={"exc_value", "traceback"})
    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        """
        Context manager exit point that disconnects the client.

        Args:
            exc_type: The exception type if an exception was raised.
            exc_value: The exception value if an exception was raised.
            traceback: The traceback if an exception was raised.
        """
        self.disconnect()

    def _start_session(self) -> None:
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        response = self._stub.StartSession(
            controller_v1_pbs.Request_StartSession(
                sessionGUID=self._session_guid, immediateExecution=True
            )
        )
        self._session_info = response.sessionInfo

    def _stop_session(self) -> None:
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        self._stub.EndSession(
            controller_v1_pbs.Request_EndSession(sessionInfo=self._session_info)
        )

    def _start_execution(self) -> None:
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        self._stub.StartExecution(
            controller_v1_pbs.Request_StartExecution(sessionInfo=self._session_info)
        )

    def _stop_execution(self) -> None:
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        self._stub.StopExecution(
            controller_v1_pbs.Request_StopExecution(sessionInfo=self._session_info)
        )

    @telemetry.record_call()
    @override
    def screenshot(self, report: bool = True) -> Image.Image:
        """
        Take a screenshot of the current screen.

        Args:
            report (bool, optional): Whether to include the screenshot in reporting.
                Defaults to `True`.

        Returns:
            Image.Image: A PIL Image object containing the screenshot.

        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        screenResponse = self._stub.CaptureScreen(
            controller_v1_pbs.Request_CaptureScreen(
                sessionInfo=self._session_info,
                captureParameters=controller_v1_pbs.CaptureParameters(
                    displayID=self._display
                ),
            )
        )
        r, g, b, _ = Image.frombytes(
            "RGBA",
            (screenResponse.bitmap.width, screenResponse.bitmap.height),
            screenResponse.bitmap.data,
        ).split()
        image = Image.merge("RGB", (b, g, r))
        self._reporter.add_message("AgentOS", "screenshot()", image)
        return image

    @telemetry.record_call()
    @override
    def mouse_move(self, x: int, y: int) -> None:
        """
        Moves the mouse cursor to specified screen coordinates.

        Args:
            x (int): The horizontal coordinate (in pixels) to move to.
            y (int): The vertical coordinate (in pixels) to move to.
        """
        self._reporter.add_message(
            "AgentOS",
            f"mouse_move({x}, {y})",
            draw_point_on_image(self.screenshot(report=False), x, y, size=5),
        )
        self._run_recorder_action(
            acion_class_id=controller_v1_pbs.ActionClassID_MouseMove,
            action_parameters=controller_v1_pbs.ActionParameters(
                mouseMove=controller_v1_pbs.ActionParameters_MouseMove(
                    position=controller_v1_pbs.Coordinate2(x=x, y=y),
                    milliseconds=500,
                )
            ),
        )

    @telemetry.record_call(exclude={"text"})
    @override
    def type(self, text: str, typing_speed: int = 50) -> None:
        """
        Type text at current cursor position as if entered on a keyboard.

        Args:
            text (str): The text to type.
            typing_speed (int, optional): The speed of typing in characters per second.
                Defaults to `50`.
        """
        self._reporter.add_message("AgentOS", f'type("{text}", {typing_speed})')
        self._run_recorder_action(
            acion_class_id=controller_v1_pbs.ActionClassID_KeyboardType_UnicodeText,
            action_parameters=controller_v1_pbs.ActionParameters(
                keyboardTypeUnicodeText=controller_v1_pbs.ActionParameters_KeyboardType_UnicodeText(
                    text=text.encode("utf-16-le"),
                    typingSpeed=typing_speed,
                    typingSpeedValue=controller_v1_pbs.TypingSpeedValue.TypingSpeedValue_CharactersPerSecond,
                )
            ),
        )

    @telemetry.record_call()
    @override
    def click(
        self, button: Literal["left", "middle", "right"] = "left", count: int = 1
    ) -> None:
        """
        Click a mouse button.

        Args:
            button (Literal["left", "middle", "right"], optional): The mouse button to
                click. Defaults to `"left"`.
            count (int, optional): Number of times to click. Defaults to `1`.
        """
        self._reporter.add_message("AgentOS", f'click("{button}", {count})')
        mouse_button = None
        match button:
            case "left":
                mouse_button = controller_v1_pbs.MouseButton_Left
            case "middle":
                mouse_button = controller_v1_pbs.MouseButton_Middle
            case "right":
                mouse_button = controller_v1_pbs.MouseButton_Right
        self._run_recorder_action(
            acion_class_id=controller_v1_pbs.ActionClassID_MouseButton_PressAndRelease,
            action_parameters=controller_v1_pbs.ActionParameters(
                mouseButtonPressAndRelease=controller_v1_pbs.ActionParameters_MouseButton_PressAndRelease(
                    mouseButton=mouse_button, count=count
                )
            ),
        )

    @telemetry.record_call()
    @override
    def mouse_down(self, button: Literal["left", "middle", "right"] = "left") -> None:
        """
        Press and hold a mouse button.

        Args:
            button (Literal["left", "middle", "right"], optional): The mouse button to
                press. Defaults to `"left"`.
        """
        self._reporter.add_message("AgentOS", f'mouse_down("{button}")')
        mouse_button = None
        match button:
            case "left":
                mouse_button = controller_v1_pbs.MouseButton_Left
            case "middle":
                mouse_button = controller_v1_pbs.MouseButton_Middle
            case "right":
                mouse_button = controller_v1_pbs.MouseButton_Right
        self._run_recorder_action(
            acion_class_id=controller_v1_pbs.ActionClassID_MouseButton_Press,
            action_parameters=controller_v1_pbs.ActionParameters(
                mouseButtonPress=controller_v1_pbs.ActionParameters_MouseButton_Press(
                    mouseButton=mouse_button
                )
            ),
        )

    @telemetry.record_call()
    @override
    def mouse_up(self, button: Literal["left", "middle", "right"] = "left") -> None:
        """
        Release a mouse button.

        Args:
            button (Literal["left", "middle", "right"], optional): The mouse button to
                release. Defaults to `"left"`.
        """
        self._reporter.add_message("AgentOS", f'mouse_up("{button}")')
        mouse_button = None
        match button:
            case "left":
                mouse_button = controller_v1_pbs.MouseButton_Left
            case "middle":
                mouse_button = controller_v1_pbs.MouseButton_Middle
            case "right":
                mouse_button = controller_v1_pbs.MouseButton_Right
        self._run_recorder_action(
            acion_class_id=controller_v1_pbs.ActionClassID_MouseButton_Release,
            action_parameters=controller_v1_pbs.ActionParameters(
                mouseButtonRelease=controller_v1_pbs.ActionParameters_MouseButton_Release(
                    mouseButton=mouse_button
                )
            ),
        )

    @telemetry.record_call()
    @override
    def mouse_scroll(self, x: int, y: int) -> None:
        """
        Scroll the mouse wheel.

        Args:
            x (int): The horizontal scroll amount. Positive values scroll right,
                negative values scroll left.
            y (int): The vertical scroll amount. Positive values scroll down,
                negative values scroll up.
        """
        self._reporter.add_message("AgentOS", f"mouse_scroll({x}, {y})")
        if x != 0:
            self._run_recorder_action(
                acion_class_id=controller_v1_pbs.ActionClassID_MouseWheelScroll,
                action_parameters=controller_v1_pbs.ActionParameters(
                    mouseWheelScroll=controller_v1_pbs.ActionParameters_MouseWheelScroll(
                        direction=controller_v1_pbs.MouseWheelScrollDirection.MouseWheelScrollDirection_Horizontal,
                        deltaType=controller_v1_pbs.MouseWheelDeltaType.MouseWheelDelta_Raw,
                        delta=x,
                        milliseconds=50,
                    )
                ),
            )
        if y != 0:
            self._run_recorder_action(
                acion_class_id=controller_v1_pbs.ActionClassID_MouseWheelScroll,
                action_parameters=controller_v1_pbs.ActionParameters(
                    mouseWheelScroll=controller_v1_pbs.ActionParameters_MouseWheelScroll(
                        direction=controller_v1_pbs.MouseWheelScrollDirection.MouseWheelScrollDirection_Vertical,
                        deltaType=controller_v1_pbs.MouseWheelDeltaType.MouseWheelDelta_Raw,
                        delta=y,
                        milliseconds=50,
                    )
                ),
            )

    @telemetry.record_call()
    @override
    def keyboard_pressed(
        self, key: PcKey | ModifierKey, modifier_keys: list[ModifierKey] | None = None
    ) -> None:
        """
        Press and hold a keyboard key.

        Args:
            key (PcKey | ModifierKey): The key to press.
            modifier_keys (list[ModifierKey] | None, optional): List of modifier keys to
                press along with the main key. Defaults to `None`.
        """
        self._reporter.add_message(
            "AgentOS", f'keyboard_pressed("{key}", {modifier_keys})'
        )
        if modifier_keys is None:
            modifier_keys = []
        self._run_recorder_action(
            acion_class_id=controller_v1_pbs.ActionClassID_KeyboardKey_Press,
            action_parameters=controller_v1_pbs.ActionParameters(
                keyboardKeyPress=controller_v1_pbs.ActionParameters_KeyboardKey_Press(
                    keyName=key, modifierKeyNames=modifier_keys
                )
            ),
        )

    @telemetry.record_call()
    @override
    def keyboard_release(
        self, key: PcKey | ModifierKey, modifier_keys: list[ModifierKey] | None = None
    ) -> None:
        """
        Release a keyboard key.

        Args:
            key (PcKey | ModifierKey): The key to release.
            modifier_keys (list[ModifierKey] | None, optional): List of modifier keys to
                release along with the main key. Defaults to `None`.
        """
        self._reporter.add_message(
            "AgentOS", f'keyboard_release("{key}", {modifier_keys})'
        )
        if modifier_keys is None:
            modifier_keys = []
        self._run_recorder_action(
            acion_class_id=controller_v1_pbs.ActionClassID_KeyboardKey_Release,
            action_parameters=controller_v1_pbs.ActionParameters(
                keyboardKeyRelease=controller_v1_pbs.ActionParameters_KeyboardKey_Release(
                    keyName=key, modifierKeyNames=modifier_keys
                )
            ),
        )

    @telemetry.record_call()
    @override
    def keyboard_tap(
        self,
        key: PcKey | ModifierKey,
        modifier_keys: list[ModifierKey] | None = None,
        count: int = 1,
    ) -> None:
        """
        Press and immediately release a keyboard key.

        Args:
            key (PcKey | ModifierKey): The key to tap.
            modifier_keys (list[ModifierKey] | None, optional): List of modifier keys to
                press along with the main key. Defaults to `None`.
            count (int, optional): The number of times to tap the key. Defaults to `1`.
        """
        self._reporter.add_message(
            "AgentOS",
            f'keyboard_tap("{key}", {modifier_keys}, {count})',
        )
        if modifier_keys is None:
            modifier_keys = []
        for _ in range(count):
            self._run_recorder_action(
                acion_class_id=controller_v1_pbs.ActionClassID_KeyboardKey_PressAndRelease,
                action_parameters=controller_v1_pbs.ActionParameters(
                    keyboardKeyPressAndRelease=controller_v1_pbs.ActionParameters_KeyboardKey_PressAndRelease(
                        keyName=key, modifierKeyNames=modifier_keys
                    )
                ),
            )

    @telemetry.record_call()
    @override
    def set_display(self, display: int = 1) -> None:
        """
        Set the active display.

        Args:
            display (int, optional): The display ID to set as active.
                Defaults to `1`.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        self._reporter.add_message("AgentOS", f"set_display({display})")
        self._stub.SetActiveDisplay(
            controller_v1_pbs.Request_SetActiveDisplay(displayID=display)
        )
        self._display = display

    @telemetry.record_call(exclude={"command"})
    @override
    def run_command(self, command: str, timeout_ms: int = 30000) -> None:
        """
        Execute a shell command.

        Args:
            command (str): The command to execute.
            timeout_ms (int, optional): The timeout for command
                execution in milliseconds. Defaults to `30000` (30 seconds).
        """
        self._reporter.add_message("AgentOS", f'run_command("{command}", {timeout_ms})')
        self._run_recorder_action(
            acion_class_id=controller_v1_pbs.ActionClassID_RunCommand,
            action_parameters=controller_v1_pbs.ActionParameters(
                runcommand=controller_v1_pbs.ActionParameters_RunCommand(
                    command=command, timeoutInMilliseconds=timeout_ms
                )
            ),
        )

    @telemetry.record_call()
    @override
    def retrieve_active_display(self) -> Display:
        """
        Retrieve the currently active display/screen.

        Returns:
            Display: The currently active display/screen.
        """
        self._reporter.add_message("AgentOS", "retrieve_active_display()")
        displays_list_response = self.list_displays()
        for display in displays_list_response.data:
            if display.id == self._display:
                return display
        error_msg = f"Display {self._display} not found"
        raise ValueError(error_msg)

    @telemetry.record_call()
    @override
    def list_displays(
        self,
    ) -> DisplaysListResponse:
        """
        List all available displays including virtual screens.

        Returns:
            DisplaysListResponse
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message("AgentOS", "list_displays()")

        response: controller_v1_pbs.Response_GetDisplayInformation = (
            self._stub.GetDisplayInformation(controller_v1_pbs.Request_Void())
        )

        response_dict = MessageToDict(
            response,
            preserving_proto_field_name=True,
        )

        return DisplaysListResponse.model_validate(response_dict)

    @telemetry.record_call()
    def get_process_list(
        self, get_extended_info: bool = False
    ) -> controller_v1_pbs.Response_GetProcessList:
        """
        Get a list of running processes.

        Args:
            get_extended_info (bool, optional): Whether to include
                extended process information.
                Defaults to `False`.

        Returns:
            controller_v1_pbs.Response_GetProcessList: Process list response containing:
                - processes: List of ProcessInfo objects
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message("AgentOS", f"get_process_list({get_extended_info})")

        response: controller_v1_pbs.Response_GetProcessList = self._stub.GetProcessList(
            controller_v1_pbs.Request_GetProcessList(getExtendedInfo=get_extended_info)
        )

        return response

    @telemetry.record_call()
    def get_window_list(
        self, process_id: int
    ) -> controller_v1_pbs.Response_GetWindowList:
        """
        Get a list of windows for a specific process.

        Args:
            process_id (int): The ID of the process to get windows for.

        Returns:
            controller_v1_pbs.Response_GetWindowList: Window list response containing:
                - windows: List of WindowInfo objects with ID and name
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message("AgentOS", f"get_window_list({process_id})")

        response: controller_v1_pbs.Response_GetWindowList = self._stub.GetWindowList(
            controller_v1_pbs.Request_GetWindowList(processID=process_id)
        )

        return response

    @telemetry.record_call()
    def get_automation_target_list(
        self,
    ) -> controller_v1_pbs.Response_GetAutomationTargetList:
        """
        Get a list of available automation targets.

        Returns:
            controller_v1_pbs.Response_GetAutomationTargetList:
                Automation target list response:
                - targets: List of AutomationTarget objects
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message("AgentOS", "get_automation_target_list()")

        response: controller_v1_pbs.Response_GetAutomationTargetList = (
            self._stub.GetAutomationTargetList(controller_v1_pbs.Request_Void())
        )

        return response

    @telemetry.record_call()
    def set_mouse_delay(self, delay_ms: int) -> None:
        """
        Configure mouse action delay.

        Args:
            delay_ms (int): The delay in milliseconds to set for mouse actions.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message("AgentOS", f"set_mouse_delay({delay_ms})")

        self._stub.SetMouseDelay(
            controller_v1_pbs.Request_SetMouseDelay(
                sessionInfo=self._session_info, delayInMilliseconds=delay_ms
            )
        )

    @telemetry.record_call()
    def set_keyboard_delay(self, delay_ms: int) -> None:
        """
        Configure keyboard action delay.

        Args:
            delay_ms (int): The delay in milliseconds to set for keyboard actions.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message("AgentOS", f"set_keyboard_delay({delay_ms})")

        self._stub.SetKeyboardDelay(
            controller_v1_pbs.Request_SetKeyboardDelay(
                sessionInfo=self._session_info, delayInMilliseconds=delay_ms
            )
        )

    @telemetry.record_call()
    def set_active_window(self, process_id: int, window_id: int) -> None:
        """
        Set the active window for automation.

        Args:
            process_id (int): The ID of the process that owns the window.
            window_id (int): The ID of the window to set as active.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message(
            "AgentOS", f"set_active_window({process_id}, {window_id})"
        )

        self._stub.SetActiveWindow(
            controller_v1_pbs.Request_SetActiveWindow(
                processID=process_id, windowID=window_id
            )
        )

    @telemetry.record_call()
    def set_active_automation_target(self, target_id: int) -> None:
        """
        Set the active automation target.

        Args:
            target_id (int): The ID of the automation target to set as active.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message(
            "AgentOS", f"set_active_automation_target({target_id})"
        )

        self._stub.SetActiveAutomationTarget(
            controller_v1_pbs.Request_SetActiveAutomationTarget(ID=target_id)
        )

    @telemetry.record_call()
    def schedule_batched_action(
        self,
        action_class_id: controller_v1_pbs.ActionClassID,
        action_parameters: controller_v1_pbs.ActionParameters,
    ) -> controller_v1_pbs.Response_ScheduleBatchedAction:
        """
        Schedule an action for batch execution.

        Args:
            action_class_id (controller_v1_pbs.ActionClassID): The class ID
                of the action to schedule.
            action_parameters (controller_v1_pbs.ActionParameters):
                Parameters for the action.

        Returns:
            controller_v1_pbs.Response_ScheduleBatchedAction: Response containing
                the scheduled action ID.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message(
            "AgentOS",
            f"schedule_batched_action({action_class_id}, {action_parameters})",
        )

        response: controller_v1_pbs.Response_ScheduleBatchedAction = (
            self._stub.ScheduleBatchedAction(
                controller_v1_pbs.Request_ScheduleBatchedAction(
                    sessionInfo=self._session_info,
                    actionClassID=action_class_id,
                    actionParameters=action_parameters,
                )
            )
        )

        return response

    @telemetry.record_call()
    def start_batch_run(self) -> None:
        """
        Start executing batched actions.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message("AgentOS", "start_batch_run()")

        self._stub.StartBatchRun(
            controller_v1_pbs.Request_StartBatchRun(sessionInfo=self._session_info)
        )

    @telemetry.record_call()
    def stop_batch_run(self) -> None:
        """
        Stop executing batched actions.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message("AgentOS", "stop_batch_run()")

        self._stub.StopBatchRun(
            controller_v1_pbs.Request_StopBatchRun(sessionInfo=self._session_info)
        )

    @telemetry.record_call()
    def get_action_count(self) -> controller_v1_pbs.Response_GetActionCount:
        """
        Get the count of recorded or batched actions.

        Returns:
            controller_v1_pbs.Response_GetActionCount: Response
                containing the action count.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message("AgentOS", "get_action_count()")

        response: controller_v1_pbs.Response_GetActionCount = self._stub.GetActionCount(
            controller_v1_pbs.Request_GetActionCount(sessionInfo=self._session_info)
        )

        return response

    @telemetry.record_call()
    def get_action(self, action_index: int) -> controller_v1_pbs.Response_GetAction:
        """
        Get a specific action by its index.

        Args:
            action_index (int): The index of the action to retrieve.

        Returns:
            controller_v1_pbs.Response_GetAction: Action information containing:
                - actionID: The action ID
                - actionClassID: The action class ID
                - actionParameters: The action parameters
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message("AgentOS", f"get_action({action_index})")

        response: controller_v1_pbs.Response_GetAction = self._stub.GetAction(
            controller_v1_pbs.Request_GetAction(
                sessionInfo=self._session_info, actionIndex=action_index
            )
        )

        return response

    @telemetry.record_call()
    def remove_action(self, action_id: int) -> None:
        """
        Remove a specific action by its ID.

        Args:
            action_id (int): The ID of the action to remove.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message("AgentOS", f"remove_action({action_id})")

        self._stub.RemoveAction(
            controller_v1_pbs.Request_RemoveAction(
                sessionInfo=self._session_info, actionID=action_id
            )
        )

    @telemetry.record_call()
    def remove_all_actions(self) -> None:
        """
        Clear all recorded or batched actions.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message("AgentOS", "remove_all_actions()")

        self._stub.RemoveAllActions(
            controller_v1_pbs.Request_RemoveAllActions(sessionInfo=self._session_info)
        )

    def _send_message(self, message: str) -> controller_v1_pbs.Response_Send:
        """
        Send a general message to the controller.

        Args:
            message (str): The message to send to the controller.

        Returns:
            controller_v1_pbs.Response_Send: Response containing
                the message from the controller.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )

        self._reporter.add_message("AgentOS", f'send_message("{message}")')

        response: controller_v1_pbs.Response_Send = self._stub.Send(
            controller_v1_pbs.Request_Send(message=message)
        )

        return response

    @telemetry.record_call()
    def get_mouse_position(self) -> Coordinate:
        """
        Get the mouse cursor position

        Returns:
            Coordinate: Response containing the result of the mouse position change.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        req_json = create_get_mouse_position_command(
            self._session_guid
        ).model_dump_json(exclude_unset=True)
        self._reporter.add_message("AgentOS", "get_mouse_position()")
        res = self._send_message(req_json)
        parsed_res = AskuiAgentosSendResponseSchema.model_validate_json(res.message)
        return Coordinate(
            x=parsed_res.message.command.response.position.x.root,  # type: ignore[union-attr]
            y=parsed_res.message.command.response.position.y.root,  # type: ignore[union-attr]
        )

    @telemetry.record_call()
    def set_mouse_position(self, x: int, y: int) -> None:
        """
        Set the mouse cursor position to specific coordinates.

        Args:
            x (int): The horizontal coordinate (in pixels) to set the cursor to.
            y (int): The vertical coordinate (in pixels) to set the cursor to.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        req_json = create_set_mouse_position_command(
            x, y, self._session_guid
        ).model_dump_json(exclude_unset=True)
        self._reporter.add_message("AgentOS", f"set_mouse_position({x},{y})")
        self._send_message(req_json)

    @telemetry.record_call()
    def render_quad(self, style: RenderObjectStyle) -> int:
        """
        Render a quad object to the display.

        Args:
            style (RenderObjectStyle): The style properties for the quad.

        Returns:
            int: Object ID.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        self._reporter.add_message("AgentOS", f"render_quad({style})")
        req_json = create_quad_command(style, self._session_guid).model_dump_json(
            exclude_unset=True, by_alias=True
        )
        res = self._send_message(req_json)
        parsed_response = AskuiAgentosSendResponseSchema.model_validate_json(
            res.message
        )
        return int(parsed_response.message.command.response.id.root)  # type: ignore[union-attr]

    @telemetry.record_call()
    def render_line(self, style: RenderObjectStyle, points: list[Coordinate]) -> int:
        """
        Render a line object to the display.

        Args:
            style (RenderObjectStyle): The style properties for the line.
            points (list[Coordinates]): The points defining the line.

        Returns:
            int: Object ID.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        self._reporter.add_message("AgentOS", f"render_line({style}, {points})")
        req = create_line_command(style, points, self._session_guid).model_dump_json(
            exclude_unset=True, by_alias=True
        )
        res = self._send_message(req)
        parsed_response = AskuiAgentosSendResponseSchema.model_validate_json(
            res.message
        )
        return int(parsed_response.message.command.response.id.root)  # type: ignore[union-attr]

    @telemetry.record_call(exclude={"image_data"})
    def render_image(self, style: RenderObjectStyle, image_data: str) -> int:
        """
        Render an image object to the display.

        Args:
            style (RenderObjectStyle): The style properties for the image.
            image_data (str): The base64-encoded image data.

        Returns:
            int: Object ID.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        self._reporter.add_message("AgentOS", f"render_image({style}, [image_data])")
        req = create_image_command(
            style, image_data, self._session_guid
        ).model_dump_json(exclude_unset=True, by_alias=True)
        res = self._send_message(req)

        parsed_response = AskuiAgentosSendResponseSchema.model_validate_json(
            res.message
        )
        return int(parsed_response.message.command.response.id.root)  # type: ignore[union-attr]

    @telemetry.record_call()
    def render_text(self, style: RenderObjectStyle, content: str) -> int:
        """
        Render a text object to the display.

        Args:
            style (RenderObjectStyle): The style properties for the text.
            content (str): The text content to display.

        Returns:
            int: Object ID.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        self._reporter.add_message("AgentOS", f"render_text({style}, {content})")

        req = create_text_command(style, content, self._session_guid).model_dump_json(
            exclude_unset=True, by_alias=True
        )
        res = self._send_message(req)
        parsed_response = AskuiAgentosSendResponseSchema.model_validate_json(
            res.message
        )
        return int(parsed_response.message.command.response.id.root)  # type: ignore[union-attr]

    @telemetry.record_call()
    def update_render_object(self, object_id: int, style: RenderObjectStyle) -> None:
        """
        Update styling properties of an existing render object.

        Args:
            object_id (float): The ID of the render object to update.
            style (RenderObjectStyle): The new style properties.

        Returns:
            int: Object ID.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        self._reporter.add_message(
            "AgentOS", f"update_render_object({object_id}, {style})"
        )
        req = create_update_render_object_command(
            object_id, style, self._session_guid
        ).model_dump_json(exclude_unset=True, by_alias=True)
        self._send_message(req)

    @telemetry.record_call()
    def delete_render_object(self, object_id: int) -> None:
        """
        Delete an existing render object from the display.

        Args:
            object_id (RenderObjectId): The ID of the render object to delete.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        self._reporter.add_message("AgentOS", f"delete_render_object({object_id})")
        req = create_delete_render_object_command(
            object_id, self._session_guid
        ).model_dump_json(exclude_unset=True, by_alias=True)
        self._send_message(req)

    @telemetry.record_call()
    def clear_render_objects(self) -> None:
        """
        Clear all render objects from the display.
        """
        assert isinstance(self._stub, controller_v1.ControllerAPIStub), (
            "Stub is not initialized"
        )
        self._reporter.add_message("AgentOS", "clear_render_objects()")
        req = create_clear_render_objects_command(self._session_guid).model_dump_json(
            exclude_unset=True, by_alias=True
        )
        self._send_message(req)
