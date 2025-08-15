import base64
import pathlib

import pytest
from PIL import Image

from askui.utils.source_utils import load_image_source


class TestLoadImageSource:
    def test_image_source_from_pil(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        source = load_image_source(path_fixtures_github_com__icon)
        assert source.root == Image.open(path_fixtures_github_com__icon)

    def test_image_source_from_path(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        # Test loading from Path
        source = load_image_source(path_fixtures_github_com__icon)
        assert isinstance(source.root, Image.Image)
        assert source.root.size == (128, 125)  # GitHub icon size

        # Test loading from str path
        source = load_image_source(str(path_fixtures_github_com__icon))
        assert isinstance(source.root, Image.Image)
        assert source.root.size == (128, 125)

    def test_image_source_from_data_url(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        # Load test image and convert to base64
        with pathlib.Path.open(path_fixtures_github_com__icon, "rb") as f:
            img_bytes = f.read()
        img_str = base64.b64encode(img_bytes).decode()
        data_url = f"data:image/png;base64,{img_str}"

        source = load_image_source(data_url)
        assert isinstance(source.root, Image.Image)
        assert source.root.size == (128, 125)

    def test_image_source_invalid(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        with pytest.raises(FileNotFoundError):
            load_image_source("invalid_path.png")

        with pytest.raises(FileNotFoundError):
            load_image_source("invalid_base64")

        with pytest.raises(OSError):
            with pathlib.Path.open(path_fixtures_github_com__icon, "rb") as f:
                img_bytes = f.read()
                img_str = base64.b64encode(img_bytes).decode()
                load_image_source(img_str)
