# Reporting

Reporting provides human-readable logs of agent actions, perfect for debugging, auditing, and understanding agent behavior during development and testing.

## Built-in Reporters

AskUI Vision Agent includes `SimpleHtmlReporter`, which generates an HTML report of all agent actions with screenshots:

```python
from askui import ComputerAgent
from askui.reporting import SimpleHtmlReporter

with ComputerAgent(reporters=[SimpleHtmlReporter()]) as agent:
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

## Custom Reporters

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

with ComputerAgent(reporters=[CustomReporter()]) as agent:
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

with ComputerAgent(reporters=[
    SimpleHtmlReporter(),           # Human-readable HTML report
    CustomReporter(),               # Custom logging/alerting
    DatabaseReporter(),             # Store in database
]) as agent:
    agent.act("Complete checkout process")
```

Reporters are called in order:
1. `add_message()` is called for each message on all reporters
2. `generate()` is called on all reporters when the agent finishes or exits
