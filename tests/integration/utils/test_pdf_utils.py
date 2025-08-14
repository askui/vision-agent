import base64
import pathlib

import pytest

from askui.utils.file_utils import PdfSource


class TestLoadPdf:
    def test_load_pdf_from_path(self, path_fixtures_dummy_pdf: pathlib.Path) -> None:
        # Test loading from Path
        loaded = PdfSource(path_fixtures_dummy_pdf)
        assert isinstance(loaded.root, bytes)
        assert len(loaded.root) > 0

        # Test loading from str path
        loaded = PdfSource(str(path_fixtures_dummy_pdf))
        assert isinstance(loaded.root, bytes)
        assert len(loaded.root) > 0

    def test_load_pdf_nonexistent_file(self) -> None:
        with pytest.raises(ValueError):
            PdfSource("nonexistent_file.pdf")

    def test_pdf_source_from_data_url(
        self, path_fixtures_dummy_pdf: pathlib.Path
    ) -> None:
        # Load test image and convert to base64
        with pathlib.Path.open(path_fixtures_dummy_pdf, "rb") as f:
            pdf_bytes = f.read()
        pdf_str = base64.b64encode(pdf_bytes).decode()

        # Test different base64 formats
        formats = [
            f"data:application/pdf;base64,{pdf_str}",
        ]

        for fmt in formats:
            source = PdfSource(fmt)
            assert isinstance(source.root, bytes)
            assert len(source.root) > 0
