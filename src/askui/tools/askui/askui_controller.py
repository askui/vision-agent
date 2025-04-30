import pathlib
from typing import Literal
from typing_extensions import Self, override
import grpc
import os

import time
from PIL import Image

import subprocess
import uuid
import sys

from askui.tools.agent_os import ModifierKey, PcKey, AgentOs

from ..utils import process_exists, wait_for_port
from askui.container import telemetry
from askui.logger import logger
from askui.reporting import Reporter
from askui.utils.image_utils import draw_point_on_image

import askui.tools.askui.askui_ui_controller_grpc.Controller_V1_pb2_grpc as controller_v1
import askui.tools.askui.askui_ui_controller_grpc.Controller_V1_pb2 as controller_v1_pbs

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RemoteDeviceController(BaseModel):
    askui_remote_device_controller: pathlib.Path = Field(alias="AskUIRemoteDeviceController")

class Executables(BaseModel):
     executables: RemoteDeviceController = Field(alias="Executables")

class InstalledPackages(BaseModel):
    remote_device_controller_uuid: Executables = Field(alias="{aed1b543-e856-43ad-b1bc-19365d35c33e}")
    
class AskUiComponentRegistry(BaseModel):
    definition_version: int = Field(alias="DefinitionVersion")
    installed_packages: InstalledPackages = Field(alias="InstalledPackages")


class AskUiControllerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ASKUI_",
    )
    
    component_registry_file: pathlib.Path | None = None
    installation_directory: pathlib.Path | None = None

    @model_validator(mode="after")
    def validate_either_component_registry_or_installation_directory_is_set(self) -> "AskUiControllerSettings":
        if self.component_registry_file is None and self.installation_directory is None:
            raise ValueError("Either ASKUI_COMPONENT_REGISTRY_FILE or ASKUI_INSTALLATION_DIRECTORY environment variable must be set")
        return self


class AskUiControllerServer:
    """
    Concrete implementation of `ControllerServer` for managing the AskUI Remote Device Controller process.
    Handles process discovery, startup, and shutdown for the native controller binary.
    """
    def __init__(self) -> None:
        self._process = None
        self._settings = AskUiControllerSettings()  # type: ignore

    def _find_remote_device_controller(self) -> pathlib.Path:
        if self._settings.installation_directory is not None and self._settings.component_registry_file is None:
            logger.warning("Outdated AskUI Suite detected. Please update to the latest version.")
            askui_remote_device_controller_path = self._find_remote_device_controller_by_legacy_path()
            if not os.path.isfile(askui_remote_device_controller_path):
                raise FileNotFoundError(f"AskUIRemoteDeviceController executable does not exits under '{askui_remote_device_controller_path}'")
            return askui_remote_device_controller_path
        return self._find_remote_device_controller_by_component_registry()
    
    def _find_remote_device_controller_by_component_registry(self) -> pathlib.Path:
        assert self._settings.component_registry_file is not None, "Component registry file is not set"
        component_registry = AskUiComponentRegistry.model_validate_json(self._settings.component_registry_file.read_text())
        askui_remote_device_controller_path = component_registry.installed_packages.remote_device_controller_uuid.executables.askui_remote_device_controller
        if not os.path.isfile(askui_remote_device_controller_path):
            raise FileNotFoundError(f"AskUIRemoteDeviceController executable does not exits under '{askui_remote_device_controller_path}'")
        return askui_remote_device_controller_path
        
    def _find_remote_device_controller_by_legacy_path(self) -> pathlib.Path:
        assert self._settings.installation_directory is not None, "Installation directory is not set"
        match sys.platform:
            case 'win32':
                return pathlib.Path(os.path.join(self._settings.installation_directory, "Binaries", "resources", "assets", "binaries", "AskuiRemoteDeviceController.exe"))
            case 'darwin':
                return pathlib.Path(os.path.join(self._settings.installation_directory, "Binaries", "askui-ui-controller.app", "Contents", "Resources", "assets", "binaries", "AskuiRemoteDeviceController"))
            case 'linux':
                return pathlib.Path(os.path.join(self._settings.installation_directory, "Binaries", "resources", "assets", "binaries", "AskuiRemoteDeviceController"))
            case _:
                raise NotImplementedError(f"Platform {sys.platform} not supported by AskUI Remote Device Controller")
            
    def __start_process(self, path):
        self.process = subprocess.Popen(path)
        wait_for_port(23000)

    def start(self, clean_up: bool = False) -> None:
        """
        Start the controller process.

        Args:
            clean_up (bool, optional): Whether to clean up existing processes (only on Windows) before starting. Defaults to `False`.
        """
        if sys.platform == 'win32' and clean_up and process_exists("AskuiRemoteDeviceController.exe"):
            self.clean_up()
        remote_device_controller_path = self._find_remote_device_controller()
        logger.debug("Starting AskUI Remote Device Controller: %s", remote_device_controller_path)
        self.__start_process(remote_device_controller_path)
        time.sleep(0.5) # TODO Find better way to do this, e.g., waiting for something to be logged or port to be opened

    def clean_up(self):
        subprocess.run("taskkill.exe /IM AskUI*")
        time.sleep(0.1)

    def stop(self, force: bool = False) -> None:
        """
        Stop the controller process.

        Args:
            force (bool, optional): Whether to forcefully terminate the process. Defaults to `False`.
        """
        if not hasattr(self, "process") or self.process is None:
            return  # Nothing to stop

        try:
            if force:
                self.process.kill()
                if sys.platform == "win32":
                    self.clean_up()
            else:
                self.process.terminate()
        except Exception as e:
            logger.error("Failed to stop AskUI Remote Device Controller: %s", e)
            pass
        finally:
            self.process = None


class AskUiControllerClient(AgentOs):
    """
    Implementation of `AgentOs` that communicates with the AskUI Remote Device Controller via gRPC.

    Args:
        reporter (Reporter): Reporter used for reporting with the `"AgentOs"`.
        display (int, optional): Display number to use. Defaults to `1`.
        controller_server (AskUiControllerServer | None, optional): Custom controller server. Defaults to `ControllerServer`.
    """
    @telemetry.record_call(exclude={"reporter", "controller_server"})
    def __init__(self, reporter: Reporter, display: int = 1, controller_server: AskUiControllerServer | None = None) -> None:
        self.stub = None
        self.channel = None
        self.session_info = None
        self.pre_action_wait = 0
        self.post_action_wait = 0.05
        self.max_retries = 10
        self.display = display
        self._reporter = reporter
        self._controller_server = controller_server or AskUiControllerServer()

    @telemetry.record_call()
    @override
    def connect(self) -> None:
        """
        Establishes a connection to the AskUI Remote Device Controller.
        
        This method starts the controller server, establishes a gRPC channel,
        creates a session, and sets up the initial display.
        """
        self._controller_server.start()
        self.channel = grpc.insecure_channel('localhost:23000', options=[
                ('grpc.max_send_message_length', 2**30 ),
                ('grpc.max_receive_message_length', 2**30 ),
                ('grpc.default_deadline', 300000)])        
        self.stub = controller_v1.ControllerAPIStub(self.channel)        
        self._start_session()
        self._start_execution()
        self.set_display(self.display)

    def _run_recorder_action(self, acion_class_id: controller_v1_pbs.ActionClassID, action_parameters: controller_v1_pbs.ActionParameters):
        time.sleep(self.pre_action_wait)
        assert isinstance(self.stub, controller_v1.ControllerAPIStub), "Stub is not initialized"
        response: controller_v1_pbs.Response_RunRecordedAction = self.stub.RunRecordedAction(controller_v1_pbs.Request_RunRecordedAction(sessionInfo=self.session_info, actionClassID=acion_class_id, actionParameters=action_parameters))
        
        time.sleep((response.requiredMilliseconds / 1000))    
        for num_retries in range(self.max_retries):
            assert isinstance(self.stub, controller_v1.ControllerAPIStub), "Stub is not initialized"
            poll_response: controller_v1_pbs.Response_Poll = self.stub.Poll(controller_v1_pbs.Request_Poll(sessionInfo=self.session_info, pollEventID=controller_v1_pbs.PollEventID.PollEventID_ActionFinished))
            if poll_response.pollEventParameters.actionFinished.actionID == response.actionID:
                break
            time.sleep(self.post_action_wait)
        if num_retries == self.max_retries - 1:
            raise Exception("Action not yet done")
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
        self.channel.close()
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
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Context manager exit point that disconnects the client.
        
        Args:
            exc_type: The exception type if an exception was raised.
            exc_value: The exception value if an exception was raised.
            traceback: The traceback if an exception was raised.
        """
        self.disconnect()

    def _start_session(self):
        response = self.stub.StartSession(controller_v1_pbs.Request_StartSession(sessionGUID="{" + str(uuid.uuid4()) + "}", immediateExecution=True))
        self.session_info = response.sessionInfo

    def _stop_session(self):
        self.stub.EndSession(controller_v1_pbs.Request_EndSession(sessionInfo = self.session_info))

    def _start_execution(self):
        self.stub.StartExecution(controller_v1_pbs.Request_StartExecution(sessionInfo=self.session_info))        

    def _stop_execution(self):
        self.stub.StopExecution(controller_v1_pbs.Request_StopExecution(sessionInfo=self.session_info))        

    @telemetry.record_call()
    @override
    def screenshot(self, report: bool = True) -> Image.Image:
        """
        Captures a screenshot of the current display.

        Args:
            report (bool, optional): Whether to include the screenshot in reporting. Defaults to `True`.

        Returns:
            Image.Image: A PIL Image object containing the screenshot.
        """
        assert isinstance(self.stub, controller_v1.ControllerAPIStub), "Stub is not initialized"
        screenResponse = self.stub.CaptureScreen(controller_v1_pbs.Request_CaptureScreen(sessionInfo=self.session_info, captureParameters=controller_v1_pbs.CaptureParameters(displayID=self.display)))        
        r, g, b, _ = Image.frombytes('RGBA', (screenResponse.bitmap.width, screenResponse.bitmap.height), screenResponse.bitmap.data).split()
        image = Image.merge("RGB", (b, g, r))
        self._reporter.add_message("AgentOS", "screenshot()", image)
        return image

    @telemetry.record_call()
    @override
    def mouse(self, x: int, y: int) -> None:
        """
        Moves the mouse cursor to specified screen coordinates.

        Args:
            x (int): The horizontal coordinate (in pixels) to move to.
            y (int): The vertical coordinate (in pixels) to move to.
        """
        self._reporter.add_message("AgentOS", f"mouse({x}, {y})", draw_point_on_image(self.screenshot(report=False), x, y, size=5))
        self._run_recorder_action(acion_class_id=controller_v1_pbs.ActionClassID_MouseMove, action_parameters=controller_v1_pbs.ActionParameters(mouseMove=controller_v1_pbs.ActionParameters_MouseMove(position=controller_v1_pbs.Coordinate2(x=x, y=y))))

    @telemetry.record_call(exclude={"text"})
    @override
    def type(self, text: str, typing_speed: int = 50) -> None:
        """
        Simulates typing text as if entered on a keyboard.

        Args:
            text (str): The text to be typed.
            typing_speed (int, optional): The speed of typing in characters per second. Defaults to `50`.
        """
        self._reporter.add_message("AgentOS", f"type(\"{text}\", {typing_speed})")
        self._run_recorder_action(acion_class_id=controller_v1_pbs.ActionClassID_KeyboardType_UnicodeText, action_parameters=controller_v1_pbs.ActionParameters(keyboardTypeUnicodeText=controller_v1_pbs.ActionParameters_KeyboardType_UnicodeText(text=text.encode('utf-16-le'), typingSpeed=typing_speed, typingSpeedValue=controller_v1_pbs.TypingSpeedValue.TypingSpeedValue_CharactersPerSecond)))
        
    @telemetry.record_call()
    @override
    def click(self, button: Literal['left', 'middle', 'right'] = 'left', count: int = 1) -> None:
        """
        Simulates clicking a mouse button.

        Args:
            button (Literal["left", "middle", "right"], optional): The mouse button to click. Defaults to `"left"`.
            count (int, optional): Number of times to click. Defaults to `1`.
        """
        self._reporter.add_message("AgentOS", f"click(\"{button}\", {count})")
        mouse_button = None
        match button:
            case 'left':
                mouse_button = controller_v1_pbs.MouseButton_Left
            case 'middle':
                mouse_button = controller_v1_pbs.MouseButton_Middle
            case 'right':
                mouse_button = controller_v1_pbs.MouseButton_Right        
        self._run_recorder_action(acion_class_id=controller_v1_pbs.ActionClassID_MouseButton_PressAndRelease, action_parameters=controller_v1_pbs.ActionParameters(mouseButtonPressAndRelease=controller_v1_pbs.ActionParameters_MouseButton_PressAndRelease(mouseButton=mouse_button, count=count)))
        
    @telemetry.record_call()
    @override
    def mouse_down(self, button: Literal['left', 'middle', 'right'] = 'left') -> None:
        """
        Simulates pressing and holding a mouse button.

        Args:
            button (Literal["left", "middle", "right"], optional): The mouse button to press. Defaults to `"left"`.
        """
        self._reporter.add_message("AgentOS", f"mouse_down(\"{button}\")")
        mouse_button = None
        match button:
            case 'left':
                mouse_button = controller_v1_pbs.MouseButton_Left
            case 'middle':
                mouse_button = controller_v1_pbs.MouseButton_Middle
            case 'right':
                mouse_button = controller_v1_pbs.MouseButton_Right        
        self._run_recorder_action(acion_class_id=controller_v1_pbs.ActionClassID_MouseButton_Press, action_parameters=controller_v1_pbs.ActionParameters(mouseButtonPress=controller_v1_pbs.ActionParameters_MouseButton_Press(mouseButton=mouse_button)))

    @telemetry.record_call()
    @override
    def mouse_up(self, button: Literal['left', 'middle', 'right'] = 'left') -> None:       
        """
        Simulates releasing a mouse button.

        Args:
            button (Literal["left", "middle", "right"], optional): The mouse button to release. Defaults to `"left"`.
        """
        self._reporter.add_message("AgentOS", f"mouse_up(\"{button}\")")  
        mouse_button = None
        match button:
            case 'left':
                mouse_button = controller_v1_pbs.MouseButton_Left
            case 'middle':
                mouse_button = controller_v1_pbs.MouseButton_Middle
            case 'right':
                mouse_button = controller_v1_pbs.MouseButton_Right
        self._run_recorder_action(acion_class_id=controller_v1_pbs.ActionClassID_MouseButton_Release, action_parameters=controller_v1_pbs.ActionParameters(mouseButtonRelease=controller_v1_pbs.ActionParameters_MouseButton_Release(mouseButton=mouse_button)))

    @telemetry.record_call()
    @override
    def mouse_scroll(self, x: int, y: int) -> None:
        """
        Simulates scrolling the mouse wheel.

        Args:
            x (int): The horizontal scroll amount. Positive values scroll right, negative values scroll left.
            y (int): The vertical scroll amount. Positive values scroll down, negative values scroll up.
        """
        self._reporter.add_message("AgentOS", f"mouse_scroll({x}, {y})")
        if x != 0:
            self._run_recorder_action(acion_class_id=controller_v1_pbs.ActionClassID_MouseWheelScroll, action_parameters=controller_v1_pbs.ActionParameters(mouseWheelScroll=controller_v1_pbs.ActionParameters_MouseWheelScroll(
                direction = controller_v1_pbs.MouseWheelScrollDirection.MouseWheelScrollDirection_Horizontal,
                deltaType =  controller_v1_pbs.MouseWheelDeltaType.MouseWheelDelta_Raw,
                delta = x,
                milliseconds = 50
            )))
        if y != 0:
            self._run_recorder_action(acion_class_id=controller_v1_pbs.ActionClassID_MouseWheelScroll, action_parameters=controller_v1_pbs.ActionParameters(mouseWheelScroll=controller_v1_pbs.ActionParameters_MouseWheelScroll(
                direction =  controller_v1_pbs.MouseWheelScrollDirection.MouseWheelScrollDirection_Vertical,
                deltaType =  controller_v1_pbs.MouseWheelDeltaType.MouseWheelDelta_Raw,
                delta = y,
                milliseconds = 50
            )))

    @telemetry.record_call()
    @override
    def keyboard_pressed(self, key: PcKey | ModifierKey,  modifier_keys: list[ModifierKey] | None = None) -> None: 
        """
        Simulates pressing and holding a keyboard key.

        Args:
            key (PcKey | ModifierKey): The key to press.
            modifier_keys (list[ModifierKey] | None, optional): List of modifier keys to press along with the main key. Defaults to `None`.
        """
        self._reporter.add_message("AgentOS", f"keyboard_pressed(\"{key}\", {modifier_keys})")
        if modifier_keys is None:
            modifier_keys = []   
        self._run_recorder_action(acion_class_id=controller_v1_pbs.ActionClassID_KeyboardKey_Press, action_parameters=controller_v1_pbs.ActionParameters(keyboardKeyPress=controller_v1_pbs.ActionParameters_KeyboardKey_Press(keyName=key, modifierKeyNames=modifier_keys)))

    @telemetry.record_call()
    @override
    def keyboard_release(self, key: PcKey | ModifierKey,  modifier_keys: list[ModifierKey] | None = None) -> None:
        """
        Simulates releasing a keyboard key.

        Args:
            key (PcKey | ModifierKey): The key to release.
            modifier_keys (list[ModifierKey] | None, optional): List of modifier keys to release along with the main key. Defaults to `None`.
        """
        self._reporter.add_message("AgentOS", f"keyboard_release(\"{key}\", {modifier_keys})")
        if modifier_keys is None:
            modifier_keys = []   
        self._run_recorder_action(acion_class_id=controller_v1_pbs.ActionClassID_KeyboardKey_Release, action_parameters=controller_v1_pbs.ActionParameters(keyboardKeyRelease=controller_v1_pbs.ActionParameters_KeyboardKey_Release(keyName=key, modifierKeyNames=modifier_keys)))

    @telemetry.record_call()
    @override
    def keyboard_tap(self, key: PcKey | ModifierKey,  modifier_keys: list[ModifierKey] | None = None) -> None: 
        """
        Simulates pressing and immediately releasing a keyboard key.

        Args:
            key (PcKey | ModifierKey): The key to tap.
            modifier_keys (list[ModifierKey] | None, optional): List of modifier keys to press along with the main key. Defaults to `None`.
        """
        self._reporter.add_message("AgentOS", f"keyboard_tap(\"{key}\", {modifier_keys})")
        if modifier_keys is None:
            modifier_keys = []   
        self._run_recorder_action(acion_class_id=controller_v1_pbs.ActionClassID_KeyboardKey_PressAndRelease, action_parameters=controller_v1_pbs.ActionParameters(keyboardKeyPressAndRelease=controller_v1_pbs.ActionParameters_KeyboardKey_PressAndRelease(keyName=key, modifierKeyNames=modifier_keys)))

    @telemetry.record_call()
    @override
    def set_display(self, displayNumber: int = 1) -> None:
        """
        Sets the active display for screen interactions.

        Args:
            displayNumber (int, optional): The display number to set as active. Defaults to `1`.
        """
        assert isinstance(self.stub, controller_v1.ControllerAPIStub), "Stub is not initialized"
        self._reporter.add_message("AgentOS", f"set_display({displayNumber})")
        self.stub.SetActiveDisplay(controller_v1_pbs.Request_SetActiveDisplay(displayID=displayNumber))
        self.display = displayNumber
