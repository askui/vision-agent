# vision-agent


## Setup

### 1. Install AskUI Controller

TODO: Exlain

### 2. Set Install Environment

`export ASKUI_INSTALL_DIRECTORY=<path>`

`export ANTHROPIC_API_KEY='your-api-key-here'`

### 3. Start Building

```python
from askui import VisionAgent

# Initialize your agent
agent = VisionAgent()

# Launch you target application via CLI
agent.cli("firefox)

# Start to automate
agent.click("url bar")
agent.type("http://www.google.com")

# Close agent when done
agent.close()
```
