# OpenTelemetry Traces

Traces give us the big picture of what happens when a request is made to an application and are essential to understanding the full flow a user request takes in our services.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Components](#components)
- [Configuration](#configuration)
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

