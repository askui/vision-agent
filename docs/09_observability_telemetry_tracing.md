# Observability, Telemetry, and Tracing

Understanding what your AI agents are doing, debugging issues, and monitoring performance is critical for production deployments. Telemetry collects usage data to help improve AskUI Vision Agent. This data is used to detect bugs, understand usage patterns, and improve the user experience.

### What Data Is Collected

**Enabled by default**, telemetry records:

- **Package Version**: `askui` package version in use
- **Environment Information**:
  - Operating system and version
  - System architecture (x86_64, arm64, etc.)
  - Python version
  - Device ID (hashed for privacy)
- **Session Information**:
  - Session ID (random UUID per run)
  - Workspace ID (if authenticated)
  - User ID (if authenticated)
- **Method Calls**:
  - Functions called (e.g., `click()`, `act()`, `get()`)
  - Non-sensitive parameters (e.g., click coordinates)
  - Execution duration
- **Exceptions**:
  - Exception types and messages
  - Stack traces (sanitized)

### What Data Is NOT Collected

- Screenshot content or image data
- Passwords or credentials
- User input text (what you type)
- Query text (what you ask the agent)
- Screen content or extracted data
- File paths or filenames
- Network traffic or API keys

### Privacy Considerations

- **Device ID Hashing**: Your machine's device ID is hashed with an AskUI-specific salt to prevent cross-application tracking
- **No PII**: No personally identifiable information is collected without explicit authentication
- **Workspace Linkage**: If `ASKUI_WORKSPACE_ID` and `ASKUI_TOKEN` are set, telemetry is linked to your workspace for better support
- **Open Source**: Telemetry code is open source and auditable in the repository

### Disabling Telemetry

To opt out of telemetry collection, set an environment variable:

#### Linux & MacOS
```bash
export ASKUI__VA__TELEMETRY__ENABLED=False
```

#### Windows PowerShell
```powershell
$env:ASKUI__VA__TELEMETRY__ENABLED="False"
```

#### Windows Command Prompt
```cmd
set ASKUI__VA__TELEMETRY__ENABLED=False
```

#### In Code
```python
from askui import ComputerAgent
# Telemetry is now disabled for this session
```

When disabled, no usage data is collected or transmitted.
