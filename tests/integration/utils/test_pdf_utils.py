import base64
import pathlib

import pytest

from askui.utils.source_utils import load_source


class TestLoadPdf:
    def test_load_pdf_from_path(self, path_fixtures_dummy_pdf: pathlib.Path) -> None:
        loaded = load_source(path_fixtures_dummy_pdf)
        assert isinstance(loaded.root, bytes | pathlib.Path)
        with loaded.reader as r:
            assert len(r.read()) > 0

    def test_load_pdf_nonexistent_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_source("nonexistent_file.pdf")

    def test_pdf_source_from_data_url(
        self, path_fixtures_dummy_pdf: pathlib.Path
    ) -> None:
        # Load test image and convert to base64
        with pathlib.Path.open(path_fixtures_dummy_pdf, "rb") as f:
            pdf_bytes = f.read()
        pdf_str = base64.b64encode(pdf_bytes).decode()
        data_url = f"data:application/pdf;base64,{pdf_str}"
        source = load_source(data_url)
        assert isinstance(source.root, bytes | pathlib.Path)
        with source.reader as r:
            assert len(r.read()) > 0
