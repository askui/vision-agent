"""Model Store - Central location for discovering and creating available models.

This module provides factory functions and a registry for all available models
in the AskUI ecosystem. It enables model discovery and easy instantiation without
needing to import from specific provider modules.

Example:
    ```python
    from askui import model_store

    # Discover available models
    models = model_store.list_available_models()
    for name, metadata in models.items():
        print(f"{name}: {metadata['description']}")

    # Create a specific model using factory function
    act_model = model_store.create_askui_act_model()
    get_model = model_store.create_askui_get_model()
    locate_model = model_store.create_askui_locate_model()

    # Or use the factory from the registry
    claude_act = model_store.list_available_models()["claude_act"]["factory"]()
    ```
"""

from typing import Any, Callable

from askui.models.defaults import (
    default_act_model as create_askui_act_model,
)
from askui.models.defaults import (
    default_get_model as create_askui_get_model,
)
from askui.models.defaults import (
    default_locate_model as create_askui_locate_model,
)
from askui.models.models import ActModel, GetModel, LocateModel

__all__ = [
    "create_askui_act_model",
    "create_askui_get_model",
    "create_askui_locate_model",
    "list_available_models",
]


def list_available_models() -> dict[str, dict[str, Any]]:
    """List all available models with their metadata.

    Returns a dictionary mapping model identifiers to their metadata including:
    - `type`: The model type ("act", "get", or "locate")
    - `provider`: The provider name ("askui", "anthropic", "google", etc.)
    - `factory`: The factory function to create the model instance
    - `description`: Human-readable description of the model

    Returns:
        dict[str, dict[str, Any]]: Dictionary mapping model names to metadata.

    Example:
        ```python
        from askui import model_store

        models = model_store.list_available_models()

        # List all available models
        for name, info in models.items():
            print(f"{name} ({info['type']}): {info['description']}")

        # Create a model from the registry
        act_model = models["askui_act"]["factory"]()
        ```
    """
    return {
        "askui_act": {
            "type": "act",
            "provider": "askui",
            "factory": create_askui_act_model,
            "description": "AskUI default agentic model (Claude Sonnet 4 via AskUI)",
        },
        "askui_get": {
            "type": "get",
            "provider": "askui",
            "factory": create_askui_get_model,
            "description": "AskUI default info extraction (Gemini 2.5 Flash + AskUI)",
        },
        "askui_locate": {
            "type": "locate",
            "provider": "askui",
            "factory": create_askui_locate_model,
            "description": "AskUI default element locator (AskUI vision models)",
        },
    }


def create_model_from_name(model_name: str) -> ActModel | GetModel | LocateModel:
    """Create a model instance from its registry name.

    Args:
        model_name (str): The model name as registered in `list_available_models()`.

    Returns:
        ActModel | GetModel | LocateModel: The created model instance.

    Raises:
        KeyError: If the model name is not found in the registry.

    Example:
        ```python
        from askui import model_store

        # Create model by name
        model = model_store.create_model_from_name("askui_act")
        ```
    """
    models = list_available_models()
    if model_name not in models:
        available = ", ".join(models.keys())
        error_msg = f"Model '{model_name}' not found. Available models: {available}"
        raise KeyError(error_msg)

    factory: Callable[[], ActModel | GetModel | LocateModel] = models[model_name][
        "factory"
    ]
    return factory()
