import base64
import pathlib

import pytest
from PIL import Image

from askui.utils.image_utils import (
    ImageSource,
    ScalingResults,
    base64_to_image,
    data_url_to_image,
    draw_point_on_image,
    image_to_base64,
    image_to_data_url,
    load_image,
    scale_coordinates,
    scale_image_to_fit,
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

    def test_load_image_unsupported_type(self) -> None:
        with pytest.raises(AttributeError):
            load_image(123)  # type: ignore

    def test_load_image_nonexistent_file(self) -> None:
        with pytest.raises(ValueError, match="Could not open image from file path"):
            load_image("nonexistent_file.png")


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

    def test_data_url_to_image_invalid_format(self) -> None:
        with pytest.raises(ValueError):
            data_url_to_image("invalid_data_url")

    def test_data_url_to_image_invalid_base64(self) -> None:
        with pytest.raises(ValueError):
            data_url_to_image("data:image/png;base64,invalid_base64")


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
        pixel_color = new_img.getpixel((x, y))
        assert pixel_color == (255, 0, 0, 255)  # Red color

    def test_draw_point_on_image_custom_size(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        img = Image.open(path_fixtures_github_com__icon)
        x, y = 64, 62
        size = 5
        new_img = draw_point_on_image(img, x, y, size)

        # Check that the point was drawn with custom size
        pixel_color = new_img.getpixel((x, y))
        assert pixel_color == (255, 0, 0, 255)  # Red color

    def test_draw_point_on_image_edge_coordinates(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        img = Image.open(path_fixtures_github_com__icon)
        x, y = 0, 0  # Edge coordinates
        new_img = draw_point_on_image(img, x, y)

        assert new_img != img
        pixel_color = new_img.getpixel((x, y))
        assert pixel_color == (255, 0, 0, 255)  # Red color


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

    def test_base64_to_image_invalid(self) -> None:
        with pytest.raises(ValueError):
            base64_to_image("invalid_base64")

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

    def test_image_to_base64_unsupported_type(self) -> None:
        with pytest.raises(AttributeError):
            image_to_base64(123)  # type: ignore


class TestImageScaling:
    def test_scale_image_with_padding(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        img = Image.open(path_fixtures_github_com__icon)
        max_width, max_height = 200, 200

        scaled = scale_image_to_fit(img, (max_width, max_height))
        assert isinstance(scaled, Image.Image)
        assert scaled.size == (max_width, max_height)

        # Check that the image was scaled proportionally
        original_ratio = img.size[0] / img.size[1]
        scaled_ratio = (
            scaled.size[0]
            - 2 * (max_width - int(img.size[0] * (max_height / img.size[1]))) // 2
        ) / max_height
        assert abs(original_ratio - scaled_ratio) < 0.01

    def test_scale_image_smaller_than_target(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        img = Image.open(path_fixtures_github_com__icon)
        # Target size smaller than original
        target_size = (50, 50)

        scaled = scale_image_to_fit(img, target_size)
        assert isinstance(scaled, Image.Image)
        assert scaled.size == target_size

    def test_scale_image_square_to_rectangle(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        img = Image.open(path_fixtures_github_com__icon)
        # Test scaling to a rectangular target
        target_size = (300, 100)

        scaled = scale_image_to_fit(img, target_size)
        assert isinstance(scaled, Image.Image)
        assert scaled.size == target_size

    def test_scale_coordinates_back(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        img = Image.open(path_fixtures_github_com__icon)
        max_width, max_height = 200, 200

        # Test coordinates in the center of the scaled image
        x, y = 100, 100
        original_x, original_y = scale_coordinates(
            (x, y),
            img.size,
            (max_width, max_height),
            inverse=True,
        )

        # Coordinates should be within the original image bounds
        assert 0 <= original_x <= img.size[0]
        assert 0 <= original_y <= img.size[1]

        # Test coordinates outside the padded area
        with pytest.raises(ValueError):
            scale_coordinates(
                (-10, -10),
                img.size,
                (max_width, max_height),
                inverse=True,
            )

    def test_scale_coordinates_forward(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        img = Image.open(path_fixtures_github_com__icon)
        target_size = (200, 200)

        # Test scaling coordinates from original to target
        original_coords = (64, 62)  # Center of original image
        scaled_coords = scale_coordinates(
            original_coords,
            img.size,
            target_size,
            inverse=False,
        )

        # Coordinates should be within the target bounds
        assert 0 <= scaled_coords[0] <= target_size[0]
        assert 0 <= scaled_coords[1] <= target_size[1]

    def test_scale_coordinates_out_of_bounds(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        img = Image.open(path_fixtures_github_com__icon)
        target_size = (200, 200)

        # Test coordinates outside bounds
        with pytest.raises(ValueError, match="are out of bounds"):
            scale_coordinates(
                (300, 300),  # Outside target bounds
                img.size,
                target_size,
                inverse=False,
            )


class TestScalingResults:
    def test_scaling_results(self) -> None:
        factor = 0.5
        size = (100, 50)
        results = ScalingResults(factor=factor, size=size)

        assert results.factor == factor
        assert results.size == size


class TestEdgeCases:
    def test_empty_image(self) -> None:
        # Create a minimal 1x1 image
        img = Image.new("RGB", (1, 1), color="white")

        # Test scaling
        scaled = scale_image_to_fit(img, (100, 100))
        assert scaled.size == (100, 100)

        # For a 1x1 image scaled to 100x100:
        # - Scaling factor = 100 (both dimensions)
        # - Scaled size = (100, 100)
        # - Offset = (0, 0) since the scaled image is the same size as target
        # - Coordinates (0, 0) in original map to (0, 0) in target
        coords = scale_coordinates((0, 0), img.size, (100, 100))
        assert coords == (0, 0)  # Should map to (0, 0) since no offset

    def test_large_image_scaling(self) -> None:
        # Create a large image
        img = Image.new("RGB", (1000, 1000), color="white")
        target_size = (100, 100)

        scaled = scale_image_to_fit(img, target_size)
        assert scaled.size == target_size

    def test_very_small_target(
        self, path_fixtures_github_com__icon: pathlib.Path
    ) -> None:
        img = Image.open(path_fixtures_github_com__icon)
        target_size = (1, 1)

        scaled = scale_image_to_fit(img, target_size)
        assert scaled.size == target_size

    def test_data_url_edge_cases(self) -> None:
        # Test malformed data URLs
        with pytest.raises(ValueError):
            data_url_to_image("not_a_data_url")

        with pytest.raises(ValueError):
            data_url_to_image("data:invalid")

        with pytest.raises(ValueError):
            data_url_to_image("data:image/png;base64,")  # Empty base64
