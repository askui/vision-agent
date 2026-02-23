# Extracting Data

## Overview

The `get()` method allows you to extract information from the screen. You can use it to:

- Get text or data from the screen
- Check the state of UI elements
- Make decisions based on screen content
- Analyze static images and documents (see [11_file_support.md](11_file_support.md))

## Basic Usage

By default, the `get()` method will take a screenshot of the currently selected display and extract the textual information as a `str`.

```python
# Get text from screen
url = agent.get("What is the current url shown in the url bar?")
print(url)  # e.g., "github.com/login"

# Check UI state
is_logged_in = agent.get("Is the user logged in? Answer with 'yes' or 'no'.") == "yes"
if is_logged_in:
    agent.click("Logout")
else:
    agent.click("Login")

# Get specific information
page_title = agent.get("What is the page title?")
button_count = agent.get("How many buttons are visible on this page?")
```

Instead of taking a screenshot, you can also analyze specific images or documents. Please refer to [11_file_support.md](11_file_support.md) for detailed instructions.

## Structured Data Extraction

### Overview

For structured data extraction, use Pydantic models extending `ResponseSchemaBase`:

```python
from askui import ComputerAgent, ResponseSchemaBase
from PIL import Image
import json

class UserInfo(ResponseSchemaBase):
    username: str
    is_online: bool

class UrlResponse(ResponseSchemaBase):
    url: str

with ComputerAgent() as agent:
    # Get structured data
    user_info = agent.get(
        "What is the username and online status?",
        response_schema=UserInfo
    )
    print(f"User {user_info.username} is {'online' if user_info.is_online else 'offline'}")

    # Get URL as string
    url = agent.get("What is the current url shown in the url bar?")
    print(url)  # e.g., "github.com/login"

    # Get URL as Pydantic model from image at (relative) path
    response = agent.get("What is the current url shown in the url bar?", response_schema=UrlResponse)

    # Dump whole model
    print(response.model_dump_json(indent=2))
    # or
    response_json_dict = response.model_dump(mode="json")
    print(json.dumps(response_json_dict, indent=2))
    # or for regular dict
    response_dict = response.model_dump()
    print(response_dict["url"])
```

### Basic Data Types

```python
# Get boolean response
is_login_page = agent.get(
    "Is this a login page?",
    response_schema=bool,
)
print(is_login_page)

# Get integer response
input_count = agent.get(
    "How many input fields are visible on this page?",
    response_schema=int,
)
print(input_count)

# Get float response
design_rating = agent.get(
    "Rate the page design quality from 0 to 1",
    response_schema=float,
)
print(design_rating)
```

### Complex Data Structures (nested and recursive)

```python
class NestedResponse(ResponseSchemaBase):
    nested: UrlResponse

class LinkedListNode(ResponseSchemaBase):
    value: str
    next: "LinkedListNode | None"

# Get nested response
nested = agent.get(
    "Extract the URL and its metadata from the page",
    response_schema=NestedResponse,
)
print(nested.nested.url)

# Get recursive response
linked_list = agent.get(
    "Extract the breadcrumb navigation as a linked list",
    response_schema=LinkedListNode,
)
current = linked_list
while current:
    print(current.value)
    current = current.next
```

## Limitations

- The support for response schemas varies among models. Currently, the `askui` model provides best support for response schemas as we try different models under the hood with your schema to see which one works best.
- Complex nested schemas may not work with all models.
- Some models may have token limits that affect extraction capabilities.
