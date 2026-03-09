import logging
from typing import Annotated

from pydantic import Field

from askui.agent_base import Agent
from askui.models.shared.tools import Tool
from askui.prompts.act_prompts import create_multidevice_agent_prompt
from askui.reporting import CompositeReporter, Reporter
from askui.retry import Retry
from askui.tools import AgentToolbox, ComputerAgentOsFacade
from askui.tools.android.agent_os_facade import AndroidAgentOsFacade
from askui.tools.android.ppadb_agent_os import PpadbAgentOs
from askui.tools.android.tools import (
    AndroidDragAndDropTool,
    AndroidGetConnectedDevicesSerialNumbersTool,
    AndroidGetConnectedDisplaysInfosTool,
    AndroidGetCurrentConnectedDeviceInfosTool,
    AndroidKeyCombinationTool,
    AndroidKeyTapEventTool,
    AndroidScreenshotTool,
    AndroidSelectDeviceBySerialNumberTool,
    AndroidSelectDisplayByUniqueIDTool,
    AndroidShellTool,
    AndroidSwipeTool,
    AndroidTapTool,
    AndroidTypeTool,
)
from askui.tools.askui import AskUiControllerClient
from askui.tools.computer import (
    ComputerGetMousePositionTool,
    ComputerGetSystemInfoTool,
    ComputerKeyboardPressedTool,
    ComputerKeyboardReleaseTool,
    ComputerKeyboardTapTool,
    ComputerListDisplaysTool,
    ComputerMouseClickTool,
    ComputerMouseHoldDownTool,
    ComputerMouseReleaseTool,
    ComputerMouseScrollTool,
    ComputerMoveMouseTool,
    ComputerRetrieveActiveDisplayTool,
    ComputerScreenshotTool,
    ComputerSetActiveDisplayTool,
    ComputerTypeTool,
)
from askui.tools.exception_tool import ExceptionTool

logger = logging.getLogger(__name__)


class MultiDeviceAgent(Agent):
    def __init__(
        self,
        display: Annotated[int, Field(ge=1)] = 1,
        reporters: list[Reporter] | None = None,
        tools: AgentToolbox | None = None,
        retry: Retry | None = None,
        act_tools: list[Tool] | None = None,
        android_device_sn: str | None = None,
    ):
        self.android_device_sn = android_device_sn
        self.android_os = PpadbAgentOs()
        reporter = CompositeReporter(reporters=reporters)
        self.android_agent_os_facade = AndroidAgentOsFacade(self.android_os)
        self.computer_agent_os_tool = AgentToolbox(
            AskUiControllerClient(
                display=display,
                reporter=reporter,
            )
        )

        self.android_tools: list[Tool] = [
            AndroidScreenshotTool(self.android_agent_os_facade),
            AndroidTapTool(self.android_agent_os_facade),
            AndroidTypeTool(self.android_agent_os_facade),
            AndroidDragAndDropTool(self.android_agent_os_facade),
            AndroidKeyTapEventTool(self.android_agent_os_facade),
            AndroidSwipeTool(self.android_agent_os_facade),
            AndroidKeyCombinationTool(self.android_agent_os_facade),
            AndroidShellTool(self.android_agent_os_facade),
            AndroidSelectDeviceBySerialNumberTool(self.android_agent_os_facade),
            AndroidSelectDisplayByUniqueIDTool(self.android_agent_os_facade),
            AndroidGetConnectedDevicesSerialNumbersTool(self.android_agent_os_facade),
            AndroidGetConnectedDisplaysInfosTool(self.android_agent_os_facade),
            AndroidGetCurrentConnectedDeviceInfosTool(self.android_agent_os_facade),
        ]
        self.computer_tools: list[Tool] = [
            ComputerGetSystemInfoTool(),
            ComputerGetMousePositionTool(),
            ComputerKeyboardPressedTool(),
            ComputerKeyboardReleaseTool(),
            ComputerKeyboardTapTool(),
            ComputerMouseClickTool(),
            ComputerMouseHoldDownTool(),
            ComputerMouseReleaseTool(),
            ComputerMouseScrollTool(),
            ComputerMoveMouseTool(),
            ComputerScreenshotTool(),
            ComputerTypeTool(),
            ComputerListDisplaysTool(),
            ComputerRetrieveActiveDisplayTool(),
            ComputerSetActiveDisplayTool(),
        ]

        act_tools = act_tools or []

        multi_device_tools: list[Tool] = (
            act_tools + self.android_tools + self.computer_tools + [ExceptionTool()]
        )

        if tools:
            msg = (
                "'tools' parameter is not supported for MultiDeviceAgent and will"
                " be ignored. Please set tools via the 'act_tools' parameter"
            )
            logger.warning(msg)

        super().__init__(
            reporter=reporter,
            tools=multi_device_tools,
            retry=retry,
            agent_os=self.computer_agent_os_tool.os,
        )

        self.computer_agent_os_facade: ComputerAgentOsFacade = ComputerAgentOsFacade(
            self.computer_agent_os_tool.os
        )
        self.act_tool_collection.add_agent_os(self.computer_agent_os_facade)

        self.act_settings.messages.system = create_multidevice_agent_prompt()

    def close(self) -> None:
        self.android_os.disconnect()
        super().close()

    def open(self) -> None:
        self.android_os.connect()
        if self.android_device_sn is not None:
            self.android_os.set_device_by_serial_number(self.android_device_sn)
        if self._agent_os is not None:
            self._agent_os.connect()
        super().open()
