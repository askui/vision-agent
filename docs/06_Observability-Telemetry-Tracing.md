# Observability, Telemetry, and Tracing

Understanding what your AI agents are doing, debugging issues, and monitoring performance is critical for production deployments. AskUI Vision Agent provides three complementary observability mechanisms: reporting for human-readable execution logs, telemetry for usage analytics, and OpenTelemetry tracing for distributed system monitoring.

## Table of Contents

- [Reporting](#reporting)
  - [Built-in Reporters](#built-in-reporters)
  - [Custom Reporters](#custom-reporters)
  - [Multiple Reporters](#multiple-reporters)
- [Telemetry](#telemetry)
  - [What Data Is Collected](#what-data-is-collected)
  - [Privacy Considerations](#privacy-considerations)
  - [Disabling Telemetry](#disabling-telemetry)
- [OpenTelemetry Tracing](#opentelemetry-tracing)
  - [Core Concepts](#core-concepts)
  - [Components](#components)
  - [Configuration](#configuration)
  - [Creating Custom Spans](#creating-custom-spans)

## Reporting

Reporting provides human-readable logs of agent actions, perfect for debugging, auditing, and understanding agent behavior during development and testing.

### Built-in Reporters

AskUI Vision Agent includes `SimpleHtmlReporter`, which generates an HTML report of all agent actions with screenshots:

```python
from askui import VisionAgent
from askui.reporting import SimpleHtmlReporter

with VisionAgent(reporters=[SimpleHtmlReporter()]) as agent:
    agent.act("Search for flights from New York to London")
    agent.click("Filter by direct flights")
    result = agent.get("What's the cheapest option?")
```

This generates an HTML file (typically in the current directory) showing:
- Timestamped sequence of actions
- Screenshots at each step
- Tool use details
- Model responses
- Any errors or exceptions

**Configuration:**
```python
# Specify output location
SimpleHtmlReporter(output_dir="./reports", filename="agent_run.html")
```

### Custom Reporters

Create custom reporters by implementing the `Reporter` interface:

```python
from typing import Optional, Union
from typing_extensions import override
from askui.reporting import Reporter
from PIL import Image

class CustomReporter(Reporter):
    def __init__(self):
        self.messages = []

    @override
    def add_message(
        self,
        role: str,
        content: Union[str, dict, list],
        image: Optional[Image.Image | list[Image.Image]] = None,
    ) -> None:
        """Called for each message in the agent conversation.

        Args:
            role: Message role ('user', 'assistant', 'system')
            content: Message content (text, dict, or list of content blocks)
            image: Optional screenshot(s) associated with the message
        """
        self.messages.append({
            "role": role,
            "content": content,
            "has_image": image is not None
        })
        print(f"[{role}]: {str(content)[:100]}...")

    @override
    def generate(self) -> None:
        """Called at the end to finalize the report.

        Use this to write files, upload data, or perform cleanup.
        """
        print(f"\nReport complete: {len(self.messages)} messages")
        # Write to file, upload to service, etc.

with VisionAgent(reporters=[CustomReporter()]) as agent:
    agent.act("Search for flights")
```

**Use Cases for Custom Reporters:**
- **JSON Logging**: Export structured logs for analysis
- **Cloud Upload**: Send reports to S3, Azure Blob, etc.
- **Database Storage**: Store execution traces in a database
- **Slack/Email Notifications**: Alert teams of execution results
- **Test Frameworks**: Integrate with pytest, unittest reporting

### Multiple Reporters

Use multiple reporters simultaneously to serve different purposes:

```python
from askui.reporting import SimpleHtmlReporter

with VisionAgent(reporters=[
    SimpleHtmlReporter(),           # Human-readable HTML report
    CustomReporter(),               # Custom logging/alerting
    DatabaseReporter(),             # Store in database
]) as agent:
    agent.act("Complete checkout process")
```

Reporters are called in order:
1. `add_message()` is called for each message on all reporters
2. `generate()` is called on all reporters when the agent finishes or exits

## Telemetry

Telemetry collects usage data to help improve AskUI Vision Agent. This data is used to detect bugs, understand usage patterns, and improve the user experience.

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
import os
os.environ["ASKUI__VA__TELEMETRY__ENABLED"] = "False"

from askui import VisionAgent
# Telemetry is now disabled for this session
```

When disabled, no usage data is collected or transmitted.

## OpenTelemetry Tracing

OpenTelemetry (OTEL) tracing provides distributed tracing for the AskUI Vision Agent Chat API and complex multi-service deployments. This is primarily relevant for enterprise deployments and developers working on the Chat API.

### Core Concepts

- **Trace**: The complete end-to-end journey of a request through your system
- **Span**: A single unit of work within a trace (e.g., HTTP request, function call, database query)
- **Tracer**: The object used to create spans
- **Processor**: Determines how completed spans are handled and queued before export (we use `BatchSpanProcessor`)
- **Exporter**: Sends collected tracing data to a backend system (Grafana/Tempo)

**Context Propagation**: Trace IDs automatically flow across services, allowing you to see the full request path even when it crosses service boundaries.

### Components

AskUI Vision Agent uses these OpenTelemetry components:

**Foundational**:
- `opentelemetry-api` - Core OTEL API
- `opentelemetry-sdk` - OTEL SDK implementation

**Exporters**:
- `opentelemetry-exporter-otlp-proto-http` - Export traces to Grafana/Tempo

**Automatic Instrumentation**:
- `opentelemetry-instrumentation-fastapi` - FastAPI request tracing
- `opentelemetry-instrumentation-httpx` - HTTP client tracing
- `opentelemetry-instrumentation-sqlalchemy` - Database query tracing

Automatic instrumentors handle context propagation, so trace IDs flow across your entire service mesh without manual intervention.

### Configuration

OpenTelemetry tracing is **disabled by default** and controlled via environment variables:

```bash
# Enable tracing
ASKUI__CHAT_API__OTEL__ENABLED=True

# Configure endpoint (Grafana/Tempo)
ASKUI__CHAT_API__OTEL__ENDPOINT=http://localhost:4318/v1/traces

# Authentication secret
ASKUI__CHAT_API__OTEL__SECRET=your-secret-token
```

**Additional Settings**: See `src/askui/telemetry/otel.py` for the complete `OtelSettings` class with all configuration options.

### Creating Custom Spans

Add custom instrumentation to your code for better observability:

#### Context Manager Approach

```python
from askui.telemetry.otel import tracer

def truncate_text(input_text):
    with tracer.start_as_current_span("truncate") as span:
        # Add metadata to the span
        span.set_attribute("truncation.length", len(input_text))
        span.set_attribute("truncation.method", "simple")

        result = input_text[:10]
        span.set_attribute("truncation.result_length", len(result))
        return result
```

#### Decorator Approach

```python
from askui.telemetry.otel import tracer
from opentelemetry import trace

@tracer.start_as_current_span("process_user_request")
def process_request(user_id):
    # The span is already active - get it to add attributes
    current_span = trace.get_current_span()
    current_span.set_attribute("user.id", user_id)

    # Call other instrumented functions (creates nested spans)
    data = fetch_user_data(user_id)
    result = transform_data(data)

    current_span.set_attribute("result.size", len(result))
    return result
```

#### Getting the Current Span

```python
from opentelemetry import trace

# Get the current span anywhere in your code
current_span = trace.get_current_span()
current_span.set_attribute("custom.attribute", "value")
current_span.add_event("Important event occurred")
```

### Span Attributes Best Practices

Use semantic conventions for common attributes:

```python
# HTTP attributes
span.set_attribute("http.method", "GET")
span.set_attribute("http.url", "https://api.example.com/data")
span.set_attribute("http.status_code", 200)

# User attributes
span.set_attribute("user.id", user_id)
span.set_attribute("user.workspace_id", workspace_id)

# Custom application attributes
span.set_attribute("askui.model", "claude-sonnet-4")
span.set_attribute("askui.action", "click")
span.set_attribute("askui.duration_ms", 150)
```

### Viewing Traces

Traces are sent to your configured OTEL endpoint (typically Grafana/Tempo):

1. **Grafana Explore**: View traces by trace ID or filter by service/attributes
2. **Service Graphs**: Visualize service dependencies and latency
3. **Error Tracking**: Filter traces by error status for debugging

## Choosing the Right Tool

Use the right observability mechanism for your needs:

| Need | Use | Why |
|------|-----|-----|
| Debugging agent behavior | **Reporting** | Human-readable logs with screenshots |
| Understanding usage patterns | **Telemetry** | Aggregate analytics and error tracking |
| Production monitoring | **OTEL Tracing** | Distributed tracing across services |
| Test execution logs | **Reporting** | Detailed step-by-step execution |
| Performance analysis | **OTEL Tracing** | Latency breakdown by component |
| Compliance/Auditing | **Custom Reporter** | Structured logs for audit trails |

## Example: Complete Observability Setup

```python
from askui import VisionAgent
from askui.reporting import SimpleHtmlReporter
import os

# Configure observability
os.environ["ASKUI__VA__TELEMETRY__ENABLED"] = "True"  # Default, but explicit
os.environ["ASKUI__CHAT_API__OTEL__ENABLED"] = "True"  # For Chat API deployments

# Custom reporter for structured logging
class JsonReporter(Reporter):
    def __init__(self, output_file):
        self.output_file = output_file
        self.log = []

    @override
    def add_message(self, role, content, image=None):
        self.log.append({
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": str(content)[:200],  # Truncate for brevity
        })

    @override
    def generate(self):
        with open(self.output_file, 'w') as f:
            json.dump(self.log, f, indent=2)

# Run agent with full observability
with VisionAgent(reporters=[
    SimpleHtmlReporter(output_dir="./reports"),
    JsonReporter("execution.json")
]) as agent:
    agent.act(
        "Search for flights from NYC to London, "
        "filter by direct flights, and tell me the cheapest option"
    )
```

This provides:
- ✅ HTML report for human review
- ✅ JSON log for automated processing
- ✅ Telemetry for error tracking
- ✅ OTEL traces for performance monitoring (if enabled)

## See Also

- **[02_Prompting.md](./02_Prompting.md)** - Improve agent reliability through better prompts
- **[03_Using-Models-and-BYOM.md](./03_Using-Models-and-BYOM.md)** - Model selection affects performance
- **[05_Tools.md](./05_Tools.md)** - Tool usage appears in reports and traces

## Further Resources

- **OpenTelemetry Documentation**: https://opentelemetry.io/docs/
- **Grafana Tempo**: https://grafana.com/oss/tempo/
- **AskUI Discord**: https://discord.gg/Gu35zMGxbx (for support)
