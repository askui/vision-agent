from pathlib import Path

import pytest

from askui.reporting import CompositeReporter
from askui.tools.askui.askui_controller import (
    AskUiControllerClient,
    AskUiControllerServer,
)


@pytest.fixture
def controller_server() -> AskUiControllerServer:
    return AskUiControllerServer()


@pytest.fixture
def controller_client(
    controller_server: AskUiControllerServer,
) -> AskUiControllerClient:
    return AskUiControllerClient(
        reporter=CompositeReporter(),
        display=1,
        controller_server=controller_server,
    )


def test_find_remote_device_controller_by_component_registry(
    controller_server: AskUiControllerServer,
) -> None:
    remote_device_controller_path = Path(
        controller_server._find_remote_device_controller_by_component_registry()
    )
    assert "AskuiRemoteDeviceController" == remote_device_controller_path.stem


def test_actions(controller_client: AskUiControllerClient) -> None:
    with controller_client:
        controller_client.screenshot()
        controller_client.mouse(0, 0)
        controller_client.click()
