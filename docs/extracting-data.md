# Extracting Data

This guide covers how to extract information from screens using AskUI Vision Agent's `get()` method, including structured data extraction, response schemas, and working with different data sources.

## Table of Contents

- [Overview](#overview)
- [Basic Usage](#basic-usage)
- [Working with Different Data Sources](#working-with-different-data-sources)
- [Structured Data Extraction](#structured-data-extraction)
  - [Basic Data Types](#basic-data-types)
  - [Complex Data Structures (nested and recursive)](#complex-data-structures-nested-and-recursive)
- [Under the hood: How we extract data from documents](#under-the-hood-how-we-extract-data-from-documents)
- [Limitations](#limitations)


## Overview

The `get()` method allows you to extract information from the screen. You can use it to:

- Get text or data from the screen
- Check the state of UI elements
- Make decisions based on screen content
- Analyze static images and documents

We currently support the following data sources:
- Images (max. 20MB, .jpg, .png)
- PDFs (max. 20MB, .pdf)
- Excel files (.xlsx, .xls)
- Word documents (.docx, .doc)

## Basic Usage

By default, the `get()` method will take a screenshot of the currently selected display and use the `askui` model to extract the textual information as a `str`.

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

## Working with Different Data Sources

Instead of taking a screenshot, you can analyze specific images or documents:

```python
from PIL import Image
from askui import VisionAgent
from pathlib import Path

with VisionAgent() as agent:
    # From PIL Image
    image = Image.open("screenshot.png")
    result = agent.get("What's in this image?", source=image)

    # From file path

    ## as a string
    result = agent.get("What's in this image?", source="screenshot.png")
    result = agent.get("What is this PDF about?", source="document.pdf")

    ## as a Path
    result = agent.get("What is this PDF about?", source="document.pdf")
    result = agent.get("What is this PDF about?", source=Path("table.xlsx"))

    # From a data url
    result = agent.get("What's in this image?", source="data:image/png;base64,...")
    result = agent.get("What is this PDF about?", source="data:application/pdf;base64,...")
```

## Extracting data other than strings

### Structured data extraction

For structured data extraction, use Pydantic models extending `ResponseSchemaBase`:

```python
from askui import ResponseSchemaBase, VisionAgent
from PIL import Image
import json

class UserInfo(ResponseSchemaBase):
    username: str
    is_online: bool

class UrlResponse(ResponseSchemaBase):
    url: str

with VisionAgent() as agent:
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
    response = agent.get(
        "What is the current url shown in the url bar?",
        response_schema=UrlResponse,
        source="screenshot.png",
    )

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

## Under the hood: How we extract data from documents

When extracting data from documents like Docs or Excel files, we use the `markitdown` library to convert them into markdown format. We chose `markitdown` over other tools for several reasons:

- **LLM-Friendly Output:** The markdown output is optimized for token usage, which is efficient for subsequent processing with large language models.
- **Includes Sheet Names:** When converting Excel files, the name of the sheet is included in the generated markdown, providing better context.
- **Enhanced Image Descriptions:** It can use an OpenAI client (`llm_client` and `llm_model`) to generate more descriptive captions for images within documents.
- **No Local Inference:** No model inference is performed on the client machine, which means no need to install and maintain heavy packages like `torch`.
- **Optional Dependencies:** It allows for optional imports, meaning you only need to install the dependencies for the file types you are working with. This reduces the number of packages to manage.
- **Microsoft Maintained:** Being maintained by Microsoft, it offers robust support for converting Office documents.

## Limitations

- The support for response schemas varies among models. Currently, the `askui` model provides best support for response schemas as we try different models under the hood with your schema to see which one works best.
- PDF processing is only supported for Gemini models hosted on AskUI and for PDFs up to 20MB.
- Complex nested schemas may not work with all models.
- Some models may have token limits that affect extraction capabilities.
