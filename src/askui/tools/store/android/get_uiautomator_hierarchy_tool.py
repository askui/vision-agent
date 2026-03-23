from askui.models.shared import AndroidBaseTool, ToolTags
from askui.tools.android.agent_os_facade import AndroidAgentOsFacade


class AndroidGetUIAutomatorHierarchyTool(AndroidBaseTool):
    """
    Returns a flattened, text-friendly snapshot of the Android accessibility hierarchy
    for the connected device (via UIAutomator window dump).

    Each line describes one on-screen view: `clickable`, tap `center` computed from
    bounds, and when non-empty: quoted `text`, `resource-id`, `content-desc`, and a
    short view `class` name (last segment of the fully qualified class). Views without
    parseable bounds are omitted.

    Prefer this over screenshots when capture fails, is unavailable, or you want
    explicit structure (ids, descriptions, centers) instead of visual inference.
    Prefer using returned centers and labels over blind coordinate guesses.

    Lines use ` | ` between fields, for example:
    `clickable=True | center=(x=120, y=340) | text="OK" | class=Button`.

    Args:
        agent_os (AndroidAgentOsFacade | None, optional): The Android agent OS facade.
            If omitted, the agent supplies the connected device implementation at
            runtime.

    Examples:
        ```python
        from askui import AndroidAgent
        from askui.tools.store.android import AndroidGetUIAutomatorHierarchyTool

        with AndroidAgent() as agent:
            agent.act(
                "List tappable elements on the screen using the accessibility tree",
                tools=[AndroidGetUIAutomatorHierarchyTool()],
            )
        ```

        ```python
        from askui import AndroidAgent
        from askui.tools.store.android import AndroidGetUIAutomatorHierarchyTool

        with AndroidAgent(act_tools=[AndroidGetUIAutomatorHierarchyTool()]) as agent:
            agent.act("What buttons and links are visible on this screen?")
        ```
    """

    def __init__(self, agent_os: AndroidAgentOsFacade | None = None) -> None:
        super().__init__(
            name="get_uiautomator_hierarchy_tool",
            description=(
                "UIAutomator accessibility snapshot for the current Android screen"
                " (window dump). Returns one text line per view: clickable, tap center"
                " from bounds (`center=(x=..., y=...)`), and when set: text,"
                " resource-id,"
                " content-desc, short view class—fields joined by ` | `. Skips views"
                " without valid bounds. Use instead of screenshots when capture is"
                " unreliable or you need ids, descriptions, and tap centers for"
                " structured reasoning; avoid guessing raw coordinates."
            ),
            required_tags=[ToolTags.SCALED_AGENT_OS.value],
            agent_os=agent_os,
        )

    def __call__(self) -> str:
        """
        Build one string of the accessibility hierarchy for the model.

        Returns:
            str: Prefix `UIAutomator hierarchy was retrieved:` followed by newline-
                separated element lines (see class docstring for field format).
        """
        hierarchy = self.agent_os.get_ui_elements()
        return f"UIAutomator hierarchy was retrieved: {str(hierarchy)}"
