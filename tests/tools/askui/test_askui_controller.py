from askui.tools.askui.askui_controller import AskUiControllerServer
from pathlib import Path


def test___find_remote_device_controller_qe_25_2_1():
    controller = AskUiControllerServer()

    remote_device_controller_path = Path(controller._AskUiControllerServer__find_remote_device_controller_qe_25_2_1())
    
    assert "AskuiRemoteDeviceController" == remote_device_controller_path.stem