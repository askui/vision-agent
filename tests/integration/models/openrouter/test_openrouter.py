import json
from typing import Any
from unittest.mock import Mock

import pytest

from askui.models.exceptions import QueryNoResponseError
from askui.models.openrouter.model import OpenRouterModel
from askui.models.types.response_schemas import ResponseSchemaBase
from askui.utils.image_utils import ImageSource


class TestResponse(ResponseSchemaBase):
    text: str
    number: int


def _create_mock_completion(content: str | None) -> Any:
    """Create a mock object that mimics the OpenAI ChatCompletion response."""
    mock_message = Mock()
    mock_message.content = content
    mock_choice = Mock()
    mock_choice.message = mock_message
    mock_completion = Mock()
    mock_completion.choices = [mock_choice]
    return mock_completion


def test_basic_query_returns_string(
    mock_openai_client: Mock,
    openrouter_model: OpenRouterModel,
    image_source_github_login_screenshot: ImageSource,
) -> None:
    mock_openai_client.chat.completions.create.return_value = _create_mock_completion(
        "Test response"
    )

    result = openrouter_model.get(
        query="What is in the image?",
        image=image_source_github_login_screenshot,
        response_schema=None,
        model_choice="test-model",
    )

    assert isinstance(result, str)
    assert result == "Test response"
    mock_openai_client.chat.completions.create.assert_called_once()


def test_query_with_response_schema_returns_validated_object(
    mock_openai_client: Mock,
    openrouter_model: OpenRouterModel,
    image_source_github_login_screenshot: ImageSource,
) -> None:
    mock_response = {
        "response": {
            "text": "Test text",
            "number": 42,
        }
    }
    mock_openai_client.chat.completions.create.return_value = _create_mock_completion(
        json.dumps(mock_response)
    )

    result = openrouter_model.get(
        query="What is in the image?",
        image=image_source_github_login_screenshot,
        response_schema=TestResponse,
        model_choice="test-model",
    )

    assert isinstance(result, TestResponse)
    assert result.text == "Test text"
    assert result.number == 42
    mock_openai_client.chat.completions.create.assert_called_once()


def test_no_response_from_model(
    mock_openai_client: Mock,
    openrouter_model: OpenRouterModel,
    image_source_github_login_screenshot: ImageSource,
) -> None:
    mock_openai_client.chat.completions.create.return_value = _create_mock_completion(
        None
    )

    with pytest.raises(QueryNoResponseError):
        openrouter_model.get(
            query="What is in the image?",
            image=image_source_github_login_screenshot,
            response_schema=None,
            model_choice="test-model",
        )
    mock_openai_client.chat.completions.create.assert_called_once()


def test_malformed_json_from_model(
    mock_openai_client: Mock,
    openrouter_model: OpenRouterModel,
    image_source_github_login_screenshot: ImageSource,
) -> None:
    mock_openai_client.chat.completions.create.return_value = _create_mock_completion(
        "Invalid JSON {"
    )

    with pytest.raises(ValueError):
        openrouter_model.get(
            query="What is in the image?",
            image=image_source_github_login_screenshot,
            response_schema=TestResponse,
            model_choice="test-model",
        )
    mock_openai_client.chat.completions.create.assert_called_once()
