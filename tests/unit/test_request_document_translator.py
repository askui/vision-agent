from pathlib import Path
from unittest.mock import MagicMock

import pytest
import pytest_mock

from askui.chat.api.messages.models import RequestDocumentBlockParam
from askui.chat.api.messages.translator import RequestDocumentBlockParamTranslator
from askui.models.shared.agent_message_param import (
    CacheControlEphemeralParam,
    TextBlockParam,
)
from askui.utils.pdf_utils import PdfSource


class TestRequestDocumentBlockParamTranslator:
    """Test cases for RequestDocumentBlockParamTranslator."""

    @pytest.fixture
    def file_service(self) -> MagicMock:
        """Mock file service."""
        return MagicMock()

    @pytest.fixture
    def translator(
        self, file_service: MagicMock
    ) -> RequestDocumentBlockParamTranslator:
        """Create translator instance."""
        return RequestDocumentBlockParamTranslator(file_service)

    @pytest.fixture
    def cache_control(self) -> CacheControlEphemeralParam:
        """Sample cache control parameter."""
        return CacheControlEphemeralParam(type="ephemeral")

    def test_init(self, file_service: MagicMock) -> None:
        """Test translator initialization."""
        translator = RequestDocumentBlockParamTranslator(file_service)
        assert translator._file_service == file_service

    @pytest.mark.asyncio
    async def test_to_anthropic_success(
        self,
        translator: RequestDocumentBlockParamTranslator,
        cache_control: CacheControlEphemeralParam,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        """Test successful conversion to Anthropic format."""
        document_block = RequestDocumentBlockParam(
            source={"file_id": "xyz789", "type": "file"},
            type="document",
            cache_control=cache_control,
        )

        # Mock the file service response
        mock_file = MagicMock()
        mock_file.model_dump_json.return_value = '{"id": "xyz789", "name": "test.pdf"}'
        mock_path = Path("/tmp/test.pdf")
        mocker.patch.object(
            translator._file_service,
            "retrieve_file_content",
            return_value=(mock_file, mock_path),
        )

        # Mock the load_source function to avoid filesystem access
        mock_pdf_source = PdfSource(root=mock_path)
        mocker.patch(
            "askui.chat.api.messages.translator.load_source",
            return_value=mock_pdf_source,
        )

        # Mock the extract_content method to return a simple text block
        mock_text_block = TextBlockParam(
            text="Extracted text content", type="text", cache_control=cache_control
        )
        mocker.patch.object(
            translator, "extract_content", return_value=[mock_text_block]
        )

        result = await translator.to_anthropic(document_block)

        assert isinstance(result, list)
        assert len(result) == 2  # file info + extracted content
        # First element should be the file info as TextBlockParam
        assert isinstance(result[0], TextBlockParam)
        assert result[0].type == "text"
        assert result[0].cache_control == cache_control
        # Second element should be the extracted content
        assert result[1] == mock_text_block

    @pytest.mark.asyncio
    async def test_to_anthropic_no_cache_control(
        self,
        translator: RequestDocumentBlockParamTranslator,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        """Test conversion without cache control."""
        document_block = RequestDocumentBlockParam(
            source={"file_id": "def456", "type": "file"},
            type="document",
        )

        # Mock the file service response
        mock_file = MagicMock()
        mock_file.model_dump_json.return_value = '{"id": "def456", "name": "test.pdf"}'
        mock_path = Path("/tmp/test.pdf")
        mocker.patch.object(
            translator._file_service,
            "retrieve_file_content",
            return_value=(mock_file, mock_path),
        )

        # Mock the load_source function to avoid filesystem access
        mock_pdf_source = PdfSource(root=mock_path)
        mocker.patch(
            "askui.chat.api.messages.translator.load_source",
            return_value=mock_pdf_source,
        )

        # Mock the extract_content method to return a simple text block
        mock_text_block = TextBlockParam(text="Extracted text content", type="text")
        mocker.patch.object(
            translator, "extract_content", return_value=[mock_text_block]
        )

        result = await translator.to_anthropic(document_block)

        assert isinstance(result, list)
        assert len(result) == 2  # file info + extracted content
        # First element should be the file info as TextBlockParam
        assert isinstance(result[0], TextBlockParam)
        assert result[0].cache_control is None
        # Second element should be the extracted content
        assert result[1] == mock_text_block
