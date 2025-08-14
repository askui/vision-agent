import pathlib

import pytest

from askui.utils.pdf_utils import load_pdf


class TestLoadPdf:
    def test_load_pdf_from_path(self, path_fixtures_dummy_pdf: pathlib.Path) -> None:
        # Test loading from Path
        loaded = load_pdf(path_fixtures_dummy_pdf)
        assert isinstance(loaded, bytes)
        assert len(loaded) > 0

        # Test loading from str path
        loaded = load_pdf(str(path_fixtures_dummy_pdf))
        assert isinstance(loaded, bytes)
        assert len(loaded) > 0

    def test_load_pdf_nonexistent_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_pdf("nonexistent_file.pdf")
