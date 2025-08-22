# Observability

## 📜 Logging

You want a better understanding of what you agent is doing? Set the `log_level` to DEBUG.

```python
import logging

with VisionAgent(log_level=logging.DEBUG) as agent:
    agent...
```

## 📜 Reporting

You want to see a report of the actions your agent took? Register a reporter using the `reporters` parameter.

```python
from typing import Optional, Union
from typing_extensions import override
from askui.reporting import SimpleHtmlReporter
from PIL import Image

with VisionAgent(reporters=[SimpleHtmlReporter()]) as agent:
    agent...
```

You can also create your own reporter by implementing the `Reporter` interface.

```python
from askui.reporting import Reporter

class CustomReporter(Reporter):
    @override
    def add_message(
        self,
        role: str,
        content: Union[str, dict, list],
        image: Optional[Image.Image | list[Image.Image]] = None,
    ) -> None:
        # adding message to the report (see implementation of `SimpleHtmlReporter` as an example)
        pass

    @override
    def generate(self) -> None:
        # generate the report if not generated live (see implementation of `SimpleHtmlReporter` as an example)
        pass


with VisionAgent(reporters=[CustomReporter()]) as agent:
    agent...
```

You can also use multiple reporters at once. Their `generate()` and `add_message()` methods will be called in the order of the reporters in the list.

```python
with VisionAgent(reporters=[SimpleHtmlReporter(), CustomReporter()]) as agent:
    agent...
```
