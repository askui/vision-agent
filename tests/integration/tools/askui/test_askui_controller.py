from askui.tools.askui.askui_controller import AskUiControllerServer
from pathlib import Path


def test_find_remote_device_controller_by_component_registry():
    controller = AskUiControllerServer()
    remote_device_controller_path = Path(controller._find_remote_device_controller_by_component_registry())
    assert "AskuiRemoteDeviceController" == remote_device_controller_path.stem
