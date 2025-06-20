import platform
import sys
from datetime import datetime, timezone

from pydantic import Field
from typing_extensions import TypeVar

from askui.models.shared.base_agent import AgentSettingsBase, BaseAgent
from askui.models.shared.tools import ToolCollection
from askui.reporting import Reporter

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"

PC_KEY = [
    "backspace",
    "delete",
    "enter",
    "tab",
    "escape",
    "up",
    "down",
    "right",
    "left",
    "home",
    "end",
    "pageup",
    "pagedown",
    "f1",
    "f2",
    "f3",
    "f4",
    "f5",
    "f6",
    "f7",
    "f8",
    "f9",
    "f10",
    "f11",
    "f12",
    "space",
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "!",
    '"',
    "#",
    "$",
    "%",
    "&",
    "'",
    "(",
    ")",
    "*",
    "+",
    ",",
    "-",
    ".",
    "/",
    ":",
    ";",
    "<",
    "=",
    ">",
    "?",
    "@",
    "[",
    "\\",
    "]",
    "^",
    "_",
    "`",
    "{",
    "|",
    "}",
    "~",
]

SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilising a {sys.platform} machine using {platform.machine()} architecture with internet access.
* When asked to perform web tasks try to open the browser (firefox, chrome, safari, ...) if not already open. Often you can find the browser icons in the toolbars of the operating systems.
* When viewing a page it can be helpful to zoom out so that you can see everything on the page.  Either that, or make sure you scroll down to see everything before deciding something isn't available.
* When using your computer function calls, they take a while to run and send back to you.  Where possible/feasible, try to chain multiple of these calls all into one function calls request.
* Valid keyboard keys available are {", ".join(PC_KEY)}
* The current date is {datetime.now(timezone.utc).strftime("%A, %B %d, %Y").replace(" 0", " ")}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using Firefox, if a startup wizard appears, IGNORE IT.  Do not even click "skip this step".  Instead, click on the address bar where it says "Search or enter address", and enter the appropriate search term or URL there.
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to continue to read the pdf from your screenshots + navigation, determine the URL, use curl to download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your StrReplaceEditTool.
</IMPORTANT>"""  # noqa: DTZ002, E501


class ComputerAgentSettingsBase(AgentSettingsBase):
    """Settings for computer agents."""

    betas: list[str] = Field(default_factory=lambda: [COMPUTER_USE_BETA_FLAG])


ComputerAgentSettings = TypeVar(
    "ComputerAgentSettings", bound=ComputerAgentSettingsBase
)


class ComputerAgent(BaseAgent[ComputerAgentSettings]):
    """Base class for computer agents that can execute autonomous actions.

    This class provides common functionality for both AskUI and Anthropic
    computer agents,
    including tool handling, message processing, and image filtering.
    """

    def __init__(
        self,
        settings: ComputerAgentSettings,
        tool_collection: ToolCollection,
        reporter: Reporter,
    ) -> None:
        """Initialize the computer agent.

        Args:
            settings (ComputerAgentSettings): The settings for the computer agent.
            tool_collection (ToolCollection): Collection of tools to be used
            reporter (Reporter): The reporter for logging messages and actions.
        """
        super().__init__(
            settings=settings,
            tool_collection=tool_collection,
            system_prompt=SYSTEM_PROMPT,
            reporter=reporter,
        )
