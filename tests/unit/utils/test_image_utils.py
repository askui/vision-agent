import base64
import pathlib

import pytest
from PIL import Image

from askui.utils.image_utils import (
    ImageSource,
    base64_to_image,
    data_url_to_image,
    draw_point_on_image,
    image_to_base64,
    image_to_data_url,
    load_image,
    scale_coordinates_back,
    scale_image_with_padding,
)


class TestLoadImage:
    def test_load_image_from_pil(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        img = Image.open(path_fixtures_github_com__icon)
        loaded = load_image(img)
        assert loaded == img

    def test_load_image_from_path(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        # Test loading from Path
        loaded = load_image(path_fixtures_github_com__icon)
        assert isinstance(loaded, Image.Image)
        assert loaded.size == (128, 125)  # GitHub icon size

        # Test loading from str path
        loaded = load_image(str(path_fixtures_github_com__icon))
        assert isinstance(loaded, Image.Image)
        assert loaded.size == (128, 125)

    def test_load_image_from_base64(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        # Load test image and convert to base64
        with pathlib.Path.open(path_fixtures_github_com__icon, "rb") as f:
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

    def test_load_image_invalid(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        with pytest.raises(ValueError):
            load_image("invalid_path.png")

        with pytest.raises(ValueError):
            load_image("invalid_base64")

        with pytest.raises(ValueError):
            with pathlib.Path.open(path_fixtures_github_com__icon, "rb") as f:
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
        with pathlib.Path.open(path_fixtures_github_com__icon, "rb") as f:
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

    def test_to_data_url(self, path_fixtures_github_com__icon: pathlib.Path) -> None:
        source = ImageSource(root=path_fixtures_github_com__icon)
        data_url = source.to_data_url()
        assert data_url.startswith("data:image/png;base64,")
        assert len(data_url) > 100  # Should have some base64 content

    def test_to_base64(self, path_fixtures_github_com__icon: pathlib.Path) -> None:
        source = ImageSource(root=path_fixtures_github_com__icon)
        base64_str = source.to_base64()
        assert len(base64_str) > 100  # Should have some base64 content


class TestDataUrlConversion:
    def test_image_to_data_url(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        img = Image.open(path_fixtures_github_com__icon)
        data_url = image_to_data_url(img)
        assert data_url.startswith("data:image/png;base64,")
        assert len(data_url) > 100

    def test_data_url_to_image(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        with pathlib.Path.open(path_fixtures_github_com__icon, "rb") as f:
            img_bytes = f.read()
        img_str = base64.b64encode(img_bytes).decode()
        data_url = f"data:image/png;base64,{img_str}"

        img = data_url_to_image(data_url)
        assert isinstance(img, Image.Image)
        assert img.size == (128, 125)


class TestPointDrawing:
    def test_draw_point_on_image(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        img = Image.open(path_fixtures_github_com__icon)
        x, y = 64, 62  # Center of the image
        new_img = draw_point_on_image(img, x, y)

        assert new_img != img  # Should be a new image
        assert isinstance(new_img, Image.Image)
        # Check that the point was drawn by looking at the pixel color
        assert new_img.getpixel((x, y)) == (255, 0, 0, 255)  # Red color


class TestBase64Conversion:
    def test_base64_to_image(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        with pathlib.Path.open(path_fixtures_github_com__icon, "rb") as f:
            img_bytes = f.read()
        img_str = base64.b64encode(img_bytes).decode()

        img = base64_to_image(img_str)
        assert isinstance(img, Image.Image)
        assert img.size == (128, 125)

    def test_image_to_base64(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        # Test with PIL Image
        img = Image.open(path_fixtures_github_com__icon)
        base64_str = image_to_base64(img)
        assert len(base64_str) > 100

        # Test with Path
        base64_str = image_to_base64(path_fixtures_github_com__icon)
        assert len(base64_str) > 100

    def test_image_to_base64_format(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        img = Image.open(path_fixtures_github_com__icon)

        # Test PNG format (default)
        png_base64 = image_to_base64(img, format_="PNG")
        png_img = base64_to_image(png_base64)
        assert png_img.format == "PNG"

        # Test JPEG format - convert to RGB first since JPEG doesn't support RGBA
        rgb_img = img.convert("RGB")
        jpeg_base64 = image_to_base64(rgb_img, format_="JPEG")
        jpeg_img = base64_to_image(jpeg_base64)
        assert jpeg_img.format == "JPEG"

        # Verify the images are different (JPEG is lossy)
        assert png_base64 != jpeg_base64


class TestImageScaling:
    def test_scale_image_with_padding(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        img = Image.open(path_fixtures_github_com__icon)
        max_width, max_height = 200, 200

        scaled = scale_image_with_padding(img, max_width, max_height)
        assert isinstance(scaled, Image.Image)
        assert scaled.size == (max_width, max_height)

        # Check that the image was scaled proportionally
        original_ratio = img.size[0] / img.size[1]
        scaled_ratio = (
            scaled.size[0]
            - 2 * (max_width - int(img.size[0] * (max_height / img.size[1]))) // 2
        ) / max_height
        assert abs(original_ratio - scaled_ratio) < 0.01

    def test_scale_coordinates_back(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        img = Image.open(path_fixtures_github_com__icon)
        max_width, max_height = 200, 200

        # Test coordinates in the center of the scaled image
        x, y = 100, 100
        original_x, original_y = scale_coordinates_back(
            x, y, img.size[0], img.size[1], max_width, max_height
        )

        # Coordinates should be within the original image bounds
        assert 0 <= original_x <= img.size[0]
        assert 0 <= original_y <= img.size[1]

        # Test coordinates outside the padded area
        with pytest.raises(ValueError):
            scale_coordinates_back(
                -10, -10, img.size[0], img.size[1], max_width, max_height
            )
