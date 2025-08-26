"""Integration tests for RequestDocumentBlockParamTranslator."""

import pathlib
import shutil
import tempfile
from typing import Generator

import pytest
from PIL import Image

from askui.chat.api.files.service import FileService
from askui.chat.api.messages.models import RequestDocumentBlockParam
from askui.chat.api.messages.translator import RequestDocumentBlockParamTranslator
from askui.models.shared.agent_message_param import CacheControlEphemeralParam
from askui.utils.excel_utils import OfficeDocumentSource
from askui.utils.image_utils import ImageSource


class TestRequestDocumentBlockParamTranslator:
    """Integration tests for RequestDocumentBlockParamTranslator with real files."""

    @pytest.fixture
    def temp_dir(self) -> Generator[pathlib.Path, None, None]:
        """Create a temporary directory for test files."""
        temp_dir = pathlib.Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup: remove the temporary directory and all its contents
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def file_service(self, temp_dir: pathlib.Path) -> FileService:
        """Create a FileService instance using the temporary directory."""
        return FileService(temp_dir)

    @pytest.fixture
    def translator(
        self, file_service: FileService
    ) -> RequestDocumentBlockParamTranslator:
        """Create a RequestDocumentBlockParamTranslator instance."""
        return RequestDocumentBlockParamTranslator(file_service)

    @pytest.fixture
    def cache_control(self) -> CacheControlEphemeralParam:
        """Sample cache control parameter."""
        return CacheControlEphemeralParam(type="ephemeral")

    def test_extract_content_from_image(
        self,
        translator: RequestDocumentBlockParamTranslator,
        path_fixtures_github_com__icon: pathlib.Path,
        temp_dir: pathlib.Path,
        cache_control: CacheControlEphemeralParam,
    ) -> None:
        """Test extracting content from an image file."""
        # Copy the fixture image to the temporary directory
        temp_image_path = temp_dir / "test_icon.png"
        shutil.copy2(path_fixtures_github_com__icon, temp_image_path)

        # Create a document block with cache control
        document_block = RequestDocumentBlockParam(
            source={"file_id": "image123", "type": "file"},
            type="document",
            cache_control=cache_control,
        )

        # Load the image source using PIL Image from the temporary file
        pil_image = Image.open(temp_image_path)
        image_source = ImageSource(pil_image)

        # Extract content
        result = translator.extract_content(image_source, document_block)

        # Should return a list with one image block
        assert isinstance(result, list)
        assert len(result) == 1

        # First element should be an image block
        image_block = result[0]
        assert image_block.type == "image"
        assert image_block.cache_control == cache_control

        # Check the source is base64 encoded
        assert image_block.source.type == "base64"
        assert image_block.source.media_type == "image/png"
        assert isinstance(image_block.source.data, str)
        assert len(image_block.source.data) > 0

    def test_extract_content_from_excel(
        self,
        translator: RequestDocumentBlockParamTranslator,
        path_fixtures_dummy_excel: pathlib.Path,
        temp_dir: pathlib.Path,
        cache_control: CacheControlEphemeralParam,
    ) -> None:
        """Test extracting content from an Excel file."""
        # Copy the fixture Excel file to the temporary directory
        temp_excel_path = temp_dir / "test_data.xlsx"
        shutil.copy2(path_fixtures_dummy_excel, temp_excel_path)

        # Create a document block with cache control
        document_block = RequestDocumentBlockParam(
            source={"file_id": "excel123", "type": "file"},
            type="document",
            cache_control=cache_control,
        )

        # Load the Excel source from the temporary file
        excel_source = OfficeDocumentSource(root=temp_excel_path)

        # Extract content
        result = translator.extract_content(excel_source, document_block)

        # Should return a list with one text block
        assert isinstance(result, list)
        assert len(result) == 1

        # First element should be a text block
        text_block = result[0]
        assert text_block.type == "text"
        assert text_block.cache_control == cache_control

        # Check the text content
        assert isinstance(text_block.text, str)
        assert len(text_block.text) > 0

    def test_extract_content_from_word(
        self,
        translator: RequestDocumentBlockParamTranslator,
        path_fixtures_dummy_doc: pathlib.Path,
        temp_dir: pathlib.Path,
        cache_control: CacheControlEphemeralParam,
    ) -> None:
        """Test extracting content from a Word document."""
        # Copy the fixture Word file to the temporary directory
        temp_doc_path = temp_dir / "test_document.docx"
        shutil.copy2(path_fixtures_dummy_doc, temp_doc_path)

        # Create a document block with cache control
        document_block = RequestDocumentBlockParam(
            source={"file_id": "word123", "type": "file"},
            type="document",
            cache_control=cache_control,
        )

        # Load the Word source from the temporary file
        word_source = OfficeDocumentSource(root=temp_doc_path)

        # Extract content
        result = translator.extract_content(word_source, document_block)

        # Should return a list with one text block
        assert isinstance(result, list)
        assert len(result) == 1

        # First element should be a text block
        text_block = result[0]
        assert text_block.type == "text"
        assert text_block.cache_control == cache_control

        # Check the text content
        assert isinstance(text_block.text, str)
        assert len(text_block.text) > 0

    def test_extract_content_from_image_no_cache_control(
        self,
        translator: RequestDocumentBlockParamTranslator,
        path_fixtures_github_com__icon: pathlib.Path,
        temp_dir: pathlib.Path,
    ) -> None:
        """Test extracting content from an image file without cache control."""
        # Copy the fixture image to the temporary directory
        temp_image_path = temp_dir / "test_icon_no_cache.png"
        shutil.copy2(path_fixtures_github_com__icon, temp_image_path)

        # Create a document block without cache control
        document_block = RequestDocumentBlockParam(
            source={"file_id": "image123", "type": "file"},
            type="document",
        )

        # Load the image source using PIL Image from the temporary file
        pil_image = Image.open(temp_image_path)
        image_source = ImageSource(pil_image)

        # Extract content
        result = translator.extract_content(image_source, document_block)

        # Should return a list with one image block
        assert isinstance(result, list)
        assert len(result) == 1

        # First element should be an image block
        image_block = result[0]
        assert image_block.type == "image"
        assert image_block.cache_control is None

        # Check the source is base64 encoded
        assert image_block.source.type == "base64"
        assert image_block.source.media_type == "image/png"
        assert isinstance(image_block.source.data, str)
        assert len(image_block.source.data) > 0

    def test_extract_content_from_excel_no_cache_control(
        self,
        translator: RequestDocumentBlockParamTranslator,
        path_fixtures_dummy_excel: pathlib.Path,
        temp_dir: pathlib.Path,
    ) -> None:
        """Test extracting content from an Excel file without cache control."""
        # Copy the fixture Excel file to the temporary directory
        temp_excel_path = temp_dir / "test_data_no_cache.xlsx"
        shutil.copy2(path_fixtures_dummy_excel, temp_excel_path)

        # Create a document block without cache control
        document_block = RequestDocumentBlockParam(
            source={"file_id": "excel123", "type": "file"},
            type="document",
        )

        # Load the Excel source from the temporary file
        excel_source = OfficeDocumentSource(root=temp_excel_path)

        # Extract content
        result = translator.extract_content(excel_source, document_block)

        # Should return a list with one text block
        assert isinstance(result, list)
        assert len(result) == 1

        # First element should be a text block
        text_block = result[0]
        assert text_block.type == "text"
        assert text_block.cache_control is None

        # Check the text content
        assert isinstance(text_block.text, str)
        assert len(text_block.text) > 0

    def test_extract_content_from_word_no_cache_control(
        self,
        translator: RequestDocumentBlockParamTranslator,
        path_fixtures_dummy_doc: pathlib.Path,
        temp_dir: pathlib.Path,
    ) -> None:
        """Test extracting content from a Word document without cache control."""
        # Copy the fixture Word file to the temporary directory
        temp_doc_path = temp_dir / "test_document_no_cache.docx"
        shutil.copy2(path_fixtures_dummy_doc, temp_doc_path)

        # Create a document block without cache control
        document_block = RequestDocumentBlockParam(
            source={"file_id": "word123", "type": "file"},
            type="document",
        )

        # Load the Word source from the temporary file
        word_source = OfficeDocumentSource(root=temp_doc_path)

        # Extract content
        result = translator.extract_content(word_source, document_block)

        # Should return a list with one text block
        assert isinstance(result, list)
        assert len(result) == 1

        # First element should be a text block
        text_block = result[0]
        assert text_block.type == "text"
        assert text_block.cache_control is None

        # Check the text content
        assert isinstance(text_block.text, str)
        assert len(text_block.text) > 0
