import pathlib
from typing import List, Literal
import grpc
import os

import time
from PIL import Image

import subprocess
import uuid
import sys

from ..utils import process_exists, wait_for_port
from askui.container import telemetry
from askui.logger import logger
from askui.reporting.report import SimpleReportGenerator
from askui.utils import draw_point_on_image

import askui.tools.askui.askui_ui_controller_grpc.Controller_V1_pb2_grpc as controller_v1
import askui.tools.askui.askui_ui_controller_grpc.Controller_V1_pb2 as controller_v1_pbs

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class AgentOSBinaryNotFoundException(Exception):
    pass

class UnsupportedAskUISuiteError(Exception):
    pass

class AskUISuiteNotInstalledError(Exception):
    pass


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

MODIFIER_KEY = Literal['command', 'alt', 'control', 'shift', 'right_shift']
PC_KEY = Literal['backspace', 'delete', 'enter', 'tab', 'escape', 'up', 'down', 'right', 'left', 'home', 'end', 'pageup', 'pagedown', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'space', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~']
PC_AND_MODIFIER_KEY = Literal['command', 'alt', 'control', 'shift', 'right_shift', 'backspace', 'delete', 'enter', 'tab', 'escape', 'up', 'down', 'right', 'left', 'home', 'end', 'pageup', 'pagedown', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'space', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~']


class AskUiControllerServer:
    def __init__(self) -> None:
        self._process = None
        self._settings = AskUiControllerSettings()  # type: ignore

    def _find_remote_device_controller(self) -> pathlib.Path:
        if self._settings.installation_directory is not None and self._settings.component_registry_file is None:
            raise UnsupportedAskUISuiteError('Outdated AskUI Suite detected. Please update to the latest version.')
        return self._find_remote_device_controller_by_component_registry()
    
    def _find_remote_device_controller_by_component_registry(self) -> pathlib.Path:
        if self._settings.component_registry_file is None:
            raise AskUISuiteNotInstalledError('AskUI Suite not installed. Please install AskUI Suite to use AskUI Vision Agent.')
        component_registry = AskUiComponentRegistry.model_validate_json(self._settings.component_registry_file.read_text())
        askui_remote_device_controller_path = component_registry.installed_packages.remote_device_controller_uuid.executables.askui_remote_device_controller
        if not os.path.isfile(askui_remote_device_controller_path):
            raise FileNotFoundError(f"AskUIRemoteDeviceController executable does not exits under '{askui_remote_device_controller_path}'")
        return askui_remote_device_controller_path
                    
    def __start_process(self, path, verbose: bool = False) -> None:
        if verbose:
            self.process = subprocess.Popen(path)
        else:
            self.process = subprocess.Popen(
                path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        wait_for_port(23000)
        
    def start(self, clean_up=False, verbose: bool = False) -> None:
        if sys.platform == 'win32' and clean_up and process_exists("AskuiRemoteDeviceController.exe"):
            self.clean_up()
        remote_device_controller_path = self._find_remote_device_controller()
        logger.debug("Starting AskUI Remote Device Controller: %s", remote_device_controller_path)
        self.__start_process(remote_device_controller_path, verbose=verbose)
        
    def clean_up(self):
        if sys.platform == 'win32':
            subprocess.run("taskkill.exe /IM AskUI*")
            time.sleep(0.1)

    def stop(self, force=False):
        if force:
            self.process.terminate()
            self.clean_up()
            return
        self.process.kill()
        

class AskUiControllerClient:
    @telemetry.record_call(exclude={"report"})
    def __init__(self, display: int = 1, report: SimpleReportGenerator | None = None) -> None:
        self.stub = None
        self.channel = None
        self.session_info = None
        self.pre_action_wait = 0
        self.post_action_wait = 0.05
        self.max_retries = 10
        self.display = display
        self.report = report

    def _assert_stub_initialized(self):
        assert isinstance(self.stub, controller_v1.ControllerAPIStub), "Stub is not initialized"

    @telemetry.record_call()
    def connect(self) -> None:
        self.channel = grpc.insecure_channel('localhost:23000', options=[
                ('grpc.max_send_message_length', 2**30 ),
                ('grpc.max_receive_message_length', 2**30 ),
                ('grpc.default_deadline', 300000)])        
        self.stub = controller_v1.ControllerAPIStub(self.channel)        
        self._start_session()
        self._start_execution()

    def _run_recorder_action(self, acion_class_id: controller_v1_pbs.ActionClassID, action_parameters: controller_v1_pbs.ActionParameters):
        time.sleep(self.pre_action_wait)
        self._assert_stub_initialized()
        response: controller_v1_pbs.Response_RunRecordedAction = self.stub.RunRecordedAction(controller_v1_pbs.Request_RunRecordedAction(sessionInfo=self.session_info, actionClassID=acion_class_id, actionParameters=action_parameters))
        
        time.sleep((response.requiredMilliseconds / 1000))    
        for num_retries in range(self.max_retries):
            self._assert_stub_initialized()
            poll_response: controller_v1_pbs.Response_Poll = self.stub.Poll(controller_v1_pbs.Request_Poll(sessionInfo=self.session_info, pollEventID=controller_v1_pbs.PollEventID.PollEventID_ActionFinished))
            if poll_response.pollEventParameters.actionFinished.actionID == response.actionID:
                break
            time.sleep(self.post_action_wait)
        if num_retries == self.max_retries - 1:
            raise Exception("Action not yet done")
        return response
    
    @telemetry.record_call()
    def disconnect(self) -> None:
        self._stop_execution()
        self._stop_session()
        self.channel.close()

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
    def screenshot(self, report: bool = True) -> Image.Image:
        self._assert_stub_initialized()
        screenResponse = self.stub.CaptureScreen(controller_v1_pbs.Request_CaptureScreen(sessionInfo=self.session_info, captureParameters=controller_v1_pbs.CaptureParameters(displayID=self.display)))        
        r, g, b, _ = Image.frombytes('RGBA', (screenResponse.bitmap.width, screenResponse.bitmap.height), screenResponse.bitmap.data).split()
        image = Image.merge("RGB", (b, g, r))
        if self.report is not None and report: 
            self.report.add_message("AgentOS", "screenshot()", image)
        return image

    @telemetry.record_call()
    def mouse(self, x: int, y: int) -> None:
        if self.report is not None: 
            self.report.add_message("AgentOS", f"mouse({x}, {y})", draw_point_on_image(self.screenshot(report=False), x, y, size=5))
        self._run_recorder_action(acion_class_id=controller_v1_pbs.ActionClassID_MouseMove, action_parameters=controller_v1_pbs.ActionParameters(mouseMove=controller_v1_pbs.ActionParameters_MouseMove(position=controller_v1_pbs.Coordinate2(x=x, y=y))))


    @telemetry.record_call(exclude={"text"})
    def type(self, text: str, typing_speed: int = 50) -> None:
        if self.report is not None: 
            self.report.add_message("AgentOS", f"type(\"{text}\", {typing_speed})")
        self._run_recorder_action(acion_class_id=controller_v1_pbs.ActionClassID_KeyboardType_UnicodeText, action_parameters=controller_v1_pbs.ActionParameters(keyboardTypeUnicodeText=controller_v1_pbs.ActionParameters_KeyboardType_UnicodeText(text=text.encode('utf-16-le'), typingSpeed=typing_speed, typingSpeedValue=controller_v1_pbs.TypingSpeedValue.TypingSpeedValue_CharactersPerSecond)))
        
    @telemetry.record_call()
    def click(self, button: Literal['left', 'middle', 'right'] = 'left', count: int = 1) -> None:
        if self.report is not None: 
            self.report.add_message("AgentOS", f"click(\"{button}\", {count})")
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
    def mouse_down(self, button: Literal['left', 'middle', 'right'] = 'left') -> None:
        if self.report is not None: 
            self.report.add_message("AgentOS", f"mouse_down(\"{button}\")")
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
    def mouse_up(self, button: Literal['left', 'middle', 'right'] = 'left') -> None:      
        if self.report is not None: 
            self.report.add_message("AgentOS", f"mouse_up(\"{button}\")")  
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
    def mouse_scroll(self, x: int, y: int) -> None:
        if self.report is not None: 
            self.report.add_message("AgentOS", f"mouse_scroll({x}, {y})")
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
    def keyboard_pressed(self, key: PC_AND_MODIFIER_KEY,  modifier_keys: List[MODIFIER_KEY] | None = None) -> None:
        if self.report is not None: 
            self.report.add_message("AgentOS", f"keyboard_pressed(\"{key}\", {modifier_keys})")
        if modifier_keys is None:
            modifier_keys = []   
        self._run_recorder_action(acion_class_id=controller_v1_pbs.ActionClassID_KeyboardKey_Press, action_parameters=controller_v1_pbs.ActionParameters(keyboardKeyPress=controller_v1_pbs.ActionParameters_KeyboardKey_Press(keyName=key, modifierKeyNames=modifier_keys)))

    @telemetry.record_call()
    def keyboard_release(self, key: PC_AND_MODIFIER_KEY,  modifier_keys: List[MODIFIER_KEY] | None = None) -> None:
        if self.report is not None: 
            self.report.add_message("AgentOS", f"keyboard_release(\"{key}\", {modifier_keys})")
        if modifier_keys is None:
            modifier_keys = []   
        self._run_recorder_action(acion_class_id=controller_v1_pbs.ActionClassID_KeyboardKey_Release, action_parameters=controller_v1_pbs.ActionParameters(keyboardKeyRelease=controller_v1_pbs.ActionParameters_KeyboardKey_Release(keyName=key, modifierKeyNames=modifier_keys)))

    @telemetry.record_call()
    def keyboard_tap(self, key: PC_AND_MODIFIER_KEY,  modifier_keys: List[MODIFIER_KEY] | None = None) -> None:
        if self.report is not None: 
            self.report.add_message("AgentOS", f"keyboard_tap(\"{key}\", {modifier_keys})")
        if modifier_keys is None:
            modifier_keys = []   
        self._run_recorder_action(acion_class_id=controller_v1_pbs.ActionClassID_KeyboardKey_PressAndRelease, action_parameters=controller_v1_pbs.ActionParameters(keyboardKeyPressAndRelease=controller_v1_pbs.ActionParameters_KeyboardKey_PressAndRelease(keyName=key, modifierKeyNames=modifier_keys)))

    @telemetry.record_call()
    def set_display(self, displayNumber: int = 1) -> None:
        self._assert_stub_initialized()
        if self.report is not None: 
            self.report.add_message("AgentOS", f"set_display({displayNumber})")
        self.stub.SetActiveDisplay(controller_v1_pbs.Request_SetActiveDisplay(displayID=displayNumber))
        self.display = displayNumber

    @telemetry.record_call()
    def get_cursor_position(self) -> tuple[int, int]:
        """Get the current cursor position from the controller.
        Returns:
            tuple[int, int]: Tuple containing the x and y coordinates of the cursor.
        """
        self._assert_stub_initialized()
        if self.report is not None: 
            self.report.add_message("AgentOS", "get_cursor_position()")
        response = self.stub.GetMousePosition(controller_v1_pbs.Request_Void())
        return (response.x, response.y)
    
    @telemetry.record_call(exclude_response = True)
    def get_display_information(self) -> List[controller_v1_pbs.DisplayInformation]:
        """Get display information from the controller.
        Returns:
            List[controller_v1_pbs.DisplayInformation]: List of display information objects.
        """
        self._assert_stub_initialized()
        if self.report is not None: 
            self.report.add_message("AgentOS", "get_display_information()")
        response = self.stub.GetDisplayInformation(controller_v1_pbs.Request_Void())
        return response.displays
    
    @telemetry.record_call(exclude_response = True)
    def get_process_list(self, has_window:bool = False) -> List[controller_v1_pbs.ProcessInfo]:
        """Get process list from the controller.
        Args:
            has_window (bool, optional): If True, only processes with windows are returned. Defaults to False.
        Returns:
            List[controller_v1_pbs.ProcessInfo]: List of process information objects.
        """
        self._assert_stub_initialized()
        if self.report is not None: 
            self.report.add_message("AgentOS", "get_process_list()")
        response = self.stub.GetProcessList(controller_v1_pbs.Request_GetProcessList(getExtendedInfo=True))
        if has_window:
           return [process for process in response.processes if process.extendedInfo.hasWindow is True]
        return response.processes
    
    @telemetry.record_call(exclude_response = True)
    def get_windows_list(self, process_id: int) -> List[controller_v1_pbs.WindowInfo]:
        """"Get window list from the controller.
        Args:
            process_id (int): Process ID to get windows for.
        Returns:
            List[controller_v1_pbs.WindowInfo]: List of window information objects.
        """
        self._assert_stub_initialized()
        if self.report is not None: 
            self.report.add_message("AgentOS", "get_windows_list()")
        response = self.stub.GetWindowList(controller_v1_pbs.Request_GetWindowList(processID=process_id))
        return response.windows
    
    @telemetry.record_call(exclude_response = True)
    def get_all_window_names(self) -> List[str]:
        """Get all window names from the controller.
        Returns:
            List[str]: List of window names.
        """
        self._assert_stub_initialized()
        if self.report is not None: 
            self.report.add_message("AgentOS", "get_all_window_names()")
        process_list = self.get_process_list(has_window=True)
        window_names = []
        for process in process_list:
            window_list = self.get_windows_list(process.ID)
            for window in window_list:
                window_names.append(window.name)
        return window_names
    
    @telemetry.record_call(exclude_response = True)
    def set_active_window(self, window_id: int, process_id: int) -> None:
        """Set the active window by window ID and process ID.
        Args:
            window_id (int): Window ID to set as active.
            process_id (int): Process ID of the window.
        """
        self._assert_stub_initialized()
        if self.report is not None: 
            self.report.add_message("AgentOS", f"set_active_window({window_id})")
        self.stub.SetActiveWindow(controller_v1_pbs.Request_SetActiveWindow(windowID=window_id, processID=process_id))

    @telemetry.record_call(exclude_response = True)
    def set_active_window_by_name(self, window_name: str) -> None:
        """Set the active window by window name.
        Args:
            window_name (str): Window name to set as active.
        Raises:
            Exception: If no window is found with the specified name.
        """
        self._assert_stub_initialized()
        if self.report is not None: 
            self.report.add_message("AgentOS", f"set_active_window_by_name({window_name})")
        process_list = self.get_process_list(has_window=True)
        for process in process_list:
            window_list = self.get_windows_list(process.ID)
            for window in window_list:
                if window.name == window_name:
                    self.set_active_window(window.ID, process.ID)
                    return
        available_window_names = self.get_all_window_names()
        raise Exception(f"No window found with name '{window_name}'. Available window names: {available_window_names}")
    
    @telemetry.record_call(exclude_response = True)
    def set_window_as_display_by_name(self, window_name: str) -> None:
        """Set the active window by window name and set it as the display.
        Args:
            window_name (str): Window name to set as active and display.
        Raises:
            Exception: If no window is found with the specified name.
        """
        self._assert_stub_initialized()
        if self.report is not None: 
            self.report.add_message("AgentOS", f"set_window_as_display_by_name({window_name})")
        self.set_active_window_by_name(window_name)
        self.set_display(len(self.get_display_information()))
