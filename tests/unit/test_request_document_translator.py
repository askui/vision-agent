from unittest.mock import MagicMock

import pytest

from askui.chat.api.messages.models import RequestDocumentBlockParam
from askui.chat.api.messages.translator import RequestDocumentBlockParamTranslator
from askui.models.shared.agent_message_param import (
    CacheControlEphemeralParam,
    TextBlockParam,
)


class TestRequestDocumentBlockParamTranslator:
    """Test cases for RequestDocumentBlockParamTranslator."""

    @pytest.fixture
    def file_service(self):
        """Mock file service."""
        return MagicMock()

    @pytest.fixture
    def translator(self, file_service):
        """Create translator instance."""
        return RequestDocumentBlockParamTranslator(file_service)

    @pytest.fixture
    def cache_control(self):
        """Sample cache control parameter."""
        return CacheControlEphemeralParam(type="ephemeral")

    def test_init(self, file_service):
        """Test translator initialization."""
        translator = RequestDocumentBlockParamTranslator(file_service)
        assert translator._file_service == file_service

    @pytest.mark.asyncio
    async def test_from_anthropic_success(self, translator, cache_control):
        """Test successful conversion from Anthropic format."""
        text_block = TextBlockParam(
            text="file:abc123",
            type="text",
            cache_control=cache_control,
        )

        result = await translator.from_anthropic(text_block)

        assert isinstance(result, RequestDocumentBlockParam)
        assert result.type == "document"
        assert result.source.file_id == "abc123"
        assert result.source.type == "file"
        assert result.cache_control == cache_control

    @pytest.mark.asyncio
    async def test_from_anthropic_wrong_type(self, translator):
        """Test error when block type is not text."""
        image_block = MagicMock()
        image_block.type = "image"

        with pytest.raises(ValueError, match="Expected text block, got image"):
            await translator.from_anthropic(image_block)

    @pytest.mark.asyncio
    async def test_from_anthropic_no_file_id(self, translator):
        """Test error when no file ID is found in text."""
        text_block = TextBlockParam(
            text="No file reference here",
            type="text",
        )

        with pytest.raises(ValueError, match="No file ID found in text content"):
            await translator.from_anthropic(text_block)

    @pytest.mark.asyncio
    async def test_to_anthropic_success(self, translator, cache_control):
        """Test successful conversion to Anthropic format."""
        document_block = RequestDocumentBlockParam(
            source={"file_id": "xyz789", "type": "file"},
            type="document",
            cache_control=cache_control,
        )

        result = await translator.to_anthropic(document_block)

        assert isinstance(result, TextBlockParam)
        assert result.type == "text"
        assert result.text == "file:xyz789"
        assert result.cache_control == cache_control

    @pytest.mark.asyncio
    async def test_to_anthropic_no_cache_control(self, translator):
        """Test conversion without cache control."""
        document_block = RequestDocumentBlockParam(
            source={"file_id": "def456", "type": "file"},
            type="document",
        )

        result = await translator.to_anthropic(document_block)

        assert result.cache_control is None
