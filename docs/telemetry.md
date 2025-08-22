# Telemetry

By default, we record usage data to detect and fix bugs inside the package and improve the UX of the package including
- version of the `askui` package used
- information about the environment, e.g., operating system, architecture, device id (hashed to protect privacy), python version
- session id
- some of the methods called including (non-sensitive) method parameters and responses, e.g., the click coordinates in `click(x=100, y=100)`
- exceptions (types and messages)
- AskUI workspace and user id if `ASKUI_WORKSPACE_ID` and `ASKUI_TOKEN` are set

If you would like to disable the recording of usage data, set the `ASKUI__VA__TELEMETRY__ENABLED` environment variable to `False`.
