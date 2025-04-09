import pytest
from pathlib import Path
import base64
from PIL import Image

from askui.locators.image_utils import load_image, ImageSource


TEST_IMAGE_PATH = Path("tests/fixtures/images/github__icon.png")


class TestLoadImage:
    def test_load_image_from_pil(self) -> None:
        img = Image.open(TEST_IMAGE_PATH)
        loaded = load_image(img)
        assert loaded == img

    def test_load_image_from_path(self) -> None:
        # Test loading from Path
        loaded = load_image(TEST_IMAGE_PATH)
        assert isinstance(loaded, Image.Image)
        assert loaded.size == (128, 125)  # GitHub icon size

        # Test loading from str path
        loaded = load_image(str(TEST_IMAGE_PATH))
        assert isinstance(loaded, Image.Image)
        assert loaded.size == (128, 125)

    def test_load_image_from_base64(self) -> None:
        # Load test image and convert to base64
        with open(TEST_IMAGE_PATH, "rb") as f:
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

    def test_load_image_invalid(self) -> None:
        with pytest.raises(ValueError):
            load_image("invalid_path.png")

        with pytest.raises(ValueError):
            load_image("invalid_base64")
            
        with pytest.raises(ValueError):
            with open(TEST_IMAGE_PATH, "rb") as f:
                img_bytes = f.read()
                img_str = base64.b64encode(img_bytes).decode()
                load_image(img_str)


class TestImageSource:
    def test_image_source(self) -> None:
        # Test with PIL Image
        img = Image.open(TEST_IMAGE_PATH)
        source = ImageSource(root=img)
        assert source.root == img

        # Test with path
        source = ImageSource(root=TEST_IMAGE_PATH)
        assert isinstance(source.root, Image.Image)
        assert source.root.size == (128, 125)

        # Test with base64
        with open(TEST_IMAGE_PATH, "rb") as f:
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
