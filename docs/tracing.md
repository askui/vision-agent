# OpenTelemetry Traces

Traces give us the big picture of what happens when a request is made to an application and are essential to understanding the full flow a user request takes in our services.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Components](#components)
- [Configuration](#configuration)
- [Setup for VisionAgent](#setup-for-visionagent)
- [What Gets Traced](#what-gets-traced)
- [Usage](#usage)
  - [Create a new span](#create-a-new-span)
    - [Context Manager](#context-manager)
    - [Decorator](#decorator)

## Core Concepts
***Trace:*** The complete end-to-end journey of a request.
***Span:*** A single unit of work within a trace (e.g., an HTTP request, a function call, a DB query).
***Tracer:*** The object used to create spans.
***Processor***: Determines how completed spans are handled and queued before being sent to an Exporter. We typically use a BatchSpanProcessor to efficiently queue and send spans in batches.
***Exporter***: Exporters are responsible for formatting and sending the collected tracing data to a backend analysis system (like Grafana/Tempo)

## Components

There are different types of components we are using. 

Foundational components to work with OTEL like: 
- opentelemetry-api
- opentelemetry-sdk

Exporters to send data to Grafana:
- opentelemetry-exporter-otlp-proto-http

Instrumentors for automatic instrumentation of certain libraries:
- opentelemetry-instrumentation-fastapi
- opentelemetry-instrumentation-httpx
- opentelemetry-instrumentation-sqlalchemy

Automatic instrumentors (like opentelemetry-instrumentation-fastapi) handle context propagation automatically, which is how a single request/trace ID flows across multiple services.

## Configuration

This feature is entirely behind a feature flag and controlled via env variables see [.env.temp](https://github.com/askui/vision-agent/blob/main/.env.template).
To enable tracing we need to set the following flags:
- `ASKUI__CHAT_API__OTEL__ENABLED=True`
- `ASKUI__CHAT_API__OTEL__ENDPOINT=http://localhost/v1/traces`
- `ASKUI__CHAT_API__OTEL__SECRET=***`

For further configuration options please refer to [OtelSettings](https://github.com/askui/vision-agent/blob/feat/otel-tracing/src/askui/telemetry/otel.py).

## Setup for VisionAgent

To enable tracing in your VisionAgent application, you need to:

1. **Set up environment variables** for your OTLP endpoint and credentials:
   ```bash
   export OTEL_ENDPOINT="https://your-otlp-endpoint.com/v1/traces"
   export OTEL_B64_SECRET="your-base64-encoded-secret"
   ```

2. **Create an `OtelSettings` instance** with your configuration:
   ```python
   import os
   from askui import VisionAgent
   from askui.telemetry.otel import OtelSettings

   def get_tracing_settings() -> OtelSettings:
       return OtelSettings(
           enabled=True,
           secret=os.environ.get("OTEL_B64_SECRET", ""),
           endpoint=os.environ.get("OTEL_ENDPOINT", ""),
           service_name="vision-agent-sdk",  # Optional: defaults to "chat-api"
           service_version="1.0.0",  # Optional: defaults to package version
           cluster_name="my-cluster",  # Optional: defaults to "askui-dev"
       )
   ```

3. **Pass the tracing settings to the `act()` method**:
   ```python
   def main() -> None:
       agent = VisionAgent(display=1, model="askui/claude-haiku-4-5-20251001")
       tracing_settings = get_tracing_settings()

       with agent:
           agent.act(
               goal="Open Chrome and navigate to www.askui.com",
               tracing_settings=tracing_settings,
           )
   ```

### OtelSettings Configuration Options

The `OtelSettings` class accepts the following parameters:

- **`enabled`** (bool): Enable/disable tracing. Default: `False`
- **`secret`** (SecretStr | None): Base64-encoded authentication secret for OTLP. Required when `enabled=True`
- **`endpoint`** (str | None): OTLP endpoint URL (e.g., `https://tempo.example.com/v1/traces`)
- **`service_name`** (str): Name of your service in traces. Default: `"chat-api"`
- **`service_version`** (str): Version of your service. Default: package version
- **`cluster_name`** (str): Name of the cluster/environment. Default: `"askui-dev"`

## What Gets Traced

VisionAgent automatically creates spans for key operations during agent execution. Here's what gets traced:

### Span Hierarchy

```
act (root span)
├── _step (one per conversation turn)
│   ├── _call_on_message (for assistant messages)
│   ├── _handle_stop_reason
│   ├── _use_tools (if tools are used)
│   └── _call_on_message (for tool results)
└── (additional _step spans for recursive calls)
```

### Span Details

#### `act` Span
The root span for the entire conversation.

**Attributes:**
- `input_tokens` (int): Total input tokens consumed across all API calls
- `output_tokens` (int): Total output tokens generated across all API calls

#### `_step` Span
Represents a single conversation turn (one API call to the LLM).

**Attributes:**
- `input_tokens` (int): Input tokens for this specific API call
- `output_tokens` (int): Output tokens for this specific API call

#### `_use_tools` Span
Created when the agent uses tools (e.g., taking screenshots, clicking, typing).

**Attributes (per tool use):**
- `id_{n}` (str): Tool use block ID
- `input_{n}` (str): JSON-encoded tool input parameters
- `name_{n}` (str): Tool name (e.g., "computer", "bash")
- `type_{n}` (str): Always "tool_use"
- `caching_control_{n}` (str): Cache control settings

Where `{n}` is the tool index (1, 2, 3, ...).

#### `_call_on_message` Span
Tracks callbacks for new messages from the assistant or user.

#### `_handle_stop_reason` Span
Handles conversation stop reasons (e.g., max_tokens, tool_use, end_turn).

### Automatic Instrumentation

When tracing is enabled, VisionAgent also automatically instruments:
- **HTTPX**: All HTTP client requests (including Anthropic API calls)

## Usage

### Create a new span

#### Context Manager
```python
def truncate(input):
  with tracer.start_as_current_span("truncate") as span:
      # set metadata
      span.set_attribute("truncation.length", len(input))

      return input[:10]

```

#### Decorator
```python 
@tracer.start_as_current_span("process-request")
def process_request(user_id):
    # The span is already active here. We can get the current span:
    current_span = trace.get_current_span()
    current_span.set_attribute("user.id", user_id)

    # You can call another function which is also instrumented (e.g., the one
    # using the context manager) to create a nested span automatically.
    data = "super long string"
    result = truncate(data) 
    
    current_span.set_attribute("final.result", result)
    return f"Processed for user {user_id} with result {result}"

# Call the function
process_request(42)

```

### Getting and modifying a span

```python 

from opentelemetry import trace

current_span = trace.get_current_span()
current_span.set_attribute("job.id", "123")

```

