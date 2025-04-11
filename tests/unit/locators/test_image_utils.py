import pathlib
import pytest
import base64
from PIL import Image

from askui.locators.image_utils import load_image, ImageSource

class TestLoadImage:
    def test_load_image_from_pil(self, path_fixtures_github_com__icon: pathlib.Path) -> None:
        img = Image.open(path_fixtures_github_com__icon)
        loaded = load_image(img)
        assert loaded == img

    def test_load_image_from_path(self, path_fixtures_github_com__icon: pathlib.Path) -> None:
        # Test loading from Path
        loaded = load_image(path_fixtures_github_com__icon)
        assert isinstance(loaded, Image.Image)
        assert loaded.size == (128, 125)  # GitHub icon size

        # Test loading from str path
        loaded = load_image(str(path_fixtures_github_com__icon))
        assert isinstance(loaded, Image.Image)
        assert loaded.size == (128, 125)

    def test_load_image_from_base64(self, path_fixtures_github_com__icon: pathlib.Path) -> None:
        # Load test image and convert to base64
        with open(path_fixtures_github_com__icon, "rb") as f:
            img_bytes = f.read()
        img_str = base64.b64encode(img_bytes).decode()

        # Test different base64 formats
        formats = [
            f"data:image/png;base64,{img_str}",
            f"data:;base64,{img_str}",
            f"data:,{img_str}",
            f",{img_str}",
        ]

        for fmt in formats:
            loaded = load_image(fmt)
            assert isinstance(loaded, Image.Image)
            assert loaded.size == (128, 125)

    def test_load_image_invalid(self, path_fixtures_github_com__icon: pathlib.Path) -> None:
        with pytest.raises(ValueError):
            load_image("invalid_path.png")

        with pytest.raises(ValueError):
            load_image("invalid_base64")
            
        with pytest.raises(ValueError):
            with open(path_fixtures_github_com__icon, "rb") as f:
                img_bytes = f.read()
                img_str = base64.b64encode(img_bytes).decode()
                load_image(img_str)


class TestImageSource:
    def test_image_source(self, path_fixtures_github_com__icon: pathlib.Path) -> None:
        # Test with PIL Image
        img = Image.open(path_fixtures_github_com__icon)
        source = ImageSource(root=img)
        assert source.root == img

        # Test with path
        source = ImageSource(root=path_fixtures_github_com__icon)
        assert isinstance(source.root, Image.Image)
        assert source.root.size == (128, 125)

        # Test with base64
        with open(path_fixtures_github_com__icon, "rb") as f:
            img_bytes = f.read()
        img_str = base64.b64encode(img_bytes).decode()
        source = ImageSource(root=f"data:image/png;base64,{img_str}")
        assert isinstance(source.root, Image.Image)
        assert source.root.size == (128, 125)

    def test_image_source_invalid(self) -> None:
        with pytest.raises(ValueError):
            ImageSource(root="invalid_path.png")

        with pytest.raises(ValueError):
            ImageSource(root="invalid_base64")
