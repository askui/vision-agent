"""AskUI Vision Agent"""

__version__ = "0.10.3"

from .agent import VisionAgent
from .locators import Locator
from .models import (
    ActModel,
    Base64ImageSourceParam,
    CacheControlEphemeralParam,
    CitationCharLocationParam,
    CitationContentBlockLocationParam,
    CitationPageLocationParam,
    ContentBlockParam,
    GetModel,
    ImageBlockParam,
    LocateModel,
    MessageParam,
    Model,
    ModelChoice,
    ModelComposition,
    ModelDefinition,
    ModelName,
    ModelRegistry,
    OnMessageCb,
    OnMessageCbParam,
    Point,
    TextBlockParam,
    TextCitationParam,
    ToolResultBlockParam,
    ToolUseBlockParam,
    UrlImageSourceParam,
)
from .models.shared.settings import ActSettings, MessageSettings
from .models.shared.tools import Tool
from .models.types.response_schemas import ResponseSchema, ResponseSchemaBase
from .retry import ConfigurableRetry, Retry
from .tools import ModifierKey, PcKey
from .utils.image_utils import ImageSource, Img

try:
    from .android_agent import AndroidVisionAgent

    _ANDROID_AGENT_AVAILABLE = True
except ImportError:
    _ANDROID_AGENT_AVAILABLE = False

try:
    from .web_agent import WebVisionAgent
    from .web_testing_agent import WebTestingAgent

    _WEB_AGENTS_AVAILABLE = True
except ImportError:
    _WEB_AGENTS_AVAILABLE = False

__all__ = [
    "ActModel",
    "ActSettings",
    "Base64ImageSourceParam",
    "CacheControlEphemeralParam",
    "CitationCharLocationParam",
    "CitationContentBlockLocationParam",
    "CitationPageLocationParam",
    "ConfigurableRetry",
    "ContentBlockParam",
    "GetModel",
    "ImageBlockParam",
    "ImageSource",
    "Img",
    "LocateModel",
    "Locator",
    "MessageParam",
    "MessageSettings",
    "Model",
    "ModelChoice",
    "ModelComposition",
    "ModelDefinition",
    "ModelName",
    "ModelRegistry",
    "ModifierKey",
    "OnMessageCb",
    "OnMessageCbParam",
    "PcKey",
    "Point",
    "ResponseSchema",
    "ResponseSchemaBase",
    "Retry",
    "TextBlockParam",
    "TextCitationParam",
    "Tool",
    "ToolResultBlockParam",
    "ToolUseBlockParam",
    "UrlImageSourceParam",
    "VisionAgent",
]

if _ANDROID_AGENT_AVAILABLE:
    __all__ += ["AndroidVisionAgent"]

if _WEB_AGENTS_AVAILABLE:
    __all__ += ["WebVisionAgent", "WebTestingAgent"]
