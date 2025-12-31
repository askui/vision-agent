"""Tests for visual validation utilities."""

import pytest
from PIL import Image, ImageDraw

from askui.utils.visual_validation import (
    compute_ahash,
    compute_phash,
    extract_region,
    get_validation_coordinate,
    hamming_distance,
    should_validate_step,
    validate_visual_hash,
)


class TestHashComputation:
    """Test hash computation functions."""

    def test_compute_phash_returns_hex_string(self) -> None:
        """Test that compute_phash returns a hexadecimal string."""
        # Create a simple test image
        img = Image.new("RGB", (100, 100), color="red")
        hash_result = compute_phash(img)

        # Should be a hex string
        assert isinstance(hash_result, str)
        assert len(hash_result) > 0
        # Should be valid hex
        int(hash_result, 16)  # Will raise if not valid hex

    def test_compute_ahash_returns_hex_string(self) -> None:
        """Test that compute_ahash returns a hexadecimal string."""
        # Create a simple test image
        img = Image.new("RGB", (100, 100), color="blue")
        hash_result = compute_ahash(img)

        # Should be a hex string
        assert isinstance(hash_result, str)
        assert len(hash_result) > 0
        # Should be valid hex
        int(hash_result, 16)  # Will raise if not valid hex

    def test_identical_images_produce_same_phash(self) -> None:
        """Test that identical images produce identical phashes."""
        img1 = Image.new("RGB", (100, 100), color="green")
        img2 = Image.new("RGB", (100, 100), color="green")

        hash1 = compute_phash(img1)
        hash2 = compute_phash(img2)

        assert hash1 == hash2

    def test_different_images_produce_different_phash(self) -> None:
        """Test that different images produce different phashes."""
        # Create images with patterns, not solid colors
        img1 = Image.new("RGB", (100, 100), color="white")
        draw1 = ImageDraw.Draw(img1)
        draw1.rectangle((10, 10, 50, 50), fill="red")

        img2 = Image.new("RGB", (100, 100), color="white")
        draw2 = ImageDraw.Draw(img2)
        draw2.rectangle((60, 60, 90, 90), fill="blue")

        hash1 = compute_phash(img1)
        hash2 = compute_phash(img2)

        assert hash1 != hash2


class TestHammingDistance:
    """Test Hamming distance calculation."""

    def test_identical_hashes_have_zero_distance(self) -> None:
        """Test that identical hashes have Hamming distance of 0."""
        hash1 = "a1b2c3d4"
        hash2 = "a1b2c3d4"

        distance = hamming_distance(hash1, hash2)
        assert distance == 0

    def test_different_hashes_have_nonzero_distance(self) -> None:
        """Test that different hashes have non-zero Hamming distance."""
        hash1 = "ffffffff"  # All 1s in binary
        hash2 = "00000000"  # All 0s in binary

        distance = hamming_distance(hash1, hash2)
        assert distance > 0

    def test_hamming_distance_raises_on_different_lengths(self) -> None:
        """Test that hamming_distance raises ValueError for different lengths."""
        hash1 = "a1b2"
        hash2 = "a1b2c3"

        with pytest.raises(ValueError, match="Hash lengths differ"):
            hamming_distance(hash1, hash2)


class TestExtractRegion:
    """Test region extraction from images."""

    def test_extract_region_returns_image(self) -> None:
        """Test that extract_region returns a PIL Image."""
        img = Image.new("RGB", (200, 200), color="red")
        center = (100, 100)

        region = extract_region(img, center, size=50)

        assert isinstance(region, Image.Image)

    def test_extract_region_has_correct_size(self) -> None:
        """Test that extracted region has correct size."""
        img = Image.new("RGB", (200, 200), color="red")
        center = (100, 100)
        size = 50

        region = extract_region(img, center, size=size)

        # Region should be approximately size x size
        assert region.width <= size
        assert region.height <= size

    def test_extract_region_at_edge(self) -> None:
        """Test that extract_region handles edge cases."""
        img = Image.new("RGB", (100, 100), color="red")
        center = (10, 10)  # Near edge

        # Should not raise an error
        region = extract_region(img, center, size=50)
        assert isinstance(region, Image.Image)


class TestValidateVisualHash:
    """Test visual hash validation."""

    def test_validate_visual_hash_passes_for_identical_images(self) -> None:
        """Test validation passes for identical images."""
        img = Image.new("RGB", (100, 100), color="red")
        stored_hash = compute_phash(img)

        is_valid, error_msg, distance = validate_visual_hash(
            stored_hash, img, threshold=10, hash_method="phash"
        )

        assert is_valid is True
        assert error_msg is None
        assert distance == 0

    def test_validate_visual_hash_fails_for_different_images(self) -> None:
        """Test validation fails for very different images."""
        # Create images with different patterns
        img1 = Image.new("RGB", (100, 100), color="white")
        draw1 = ImageDraw.Draw(img1)
        draw1.rectangle((10, 10, 50, 50), fill="red")

        img2 = Image.new("RGB", (100, 100), color="white")
        draw2 = ImageDraw.Draw(img2)
        draw2.rectangle((60, 60, 90, 90), fill="blue")

        stored_hash = compute_phash(img1)

        is_valid, error_msg, distance = validate_visual_hash(
            stored_hash, img2, threshold=5, hash_method="phash"
        )

        # Should fail due to high distance
        assert is_valid is False
        assert error_msg is not None
        assert "Visual validation failed" in error_msg

    def test_validate_visual_hash_with_ahash_method(self) -> None:
        """Test validation works with ahash method."""
        img = Image.new("RGB", (100, 100), color="green")
        stored_hash = compute_ahash(img)

        is_valid, error_msg, distance = validate_visual_hash(
            stored_hash, img, threshold=10, hash_method="ahash"
        )

        assert is_valid is True
        assert error_msg is None
        assert distance == 0

    def test_validate_visual_hash_unknown_method(self) -> None:
        """Test validation fails gracefully with unknown hash method."""
        img = Image.new("RGB", (100, 100), color="red")
        stored_hash = "abcdef"

        is_valid, error_msg, distance = validate_visual_hash(
            stored_hash, img, threshold=10, hash_method="unknown_method"
        )

        assert is_valid is False
        assert error_msg is not None
        assert "Unknown hash method" in error_msg


class TestShouldValidateStep:
    """Test step validation logic."""

    def test_should_validate_left_click(self) -> None:
        """Test that left_click actions should be validated."""
        assert should_validate_step("computer", "left_click") is True

    def test_should_validate_right_click(self) -> None:
        """Test that right_click actions should be validated."""
        assert should_validate_step("computer", "right_click") is True

    def test_should_validate_type_action(self) -> None:
        """Test that type actions should be validated."""
        assert should_validate_step("computer", "type") is True

    def test_should_not_validate_screenshot(self) -> None:
        """Test that screenshot actions should not be validated."""
        assert should_validate_step("computer", "screenshot") is False

    def test_should_not_validate_unknown_tool(self) -> None:
        """Test that unknown tools should not be validated."""
        assert should_validate_step("unknown_tool", None) is False


class TestGetValidationCoordinate:
    """Test coordinate extraction for validation."""

    def test_get_validation_coordinate_from_computer_tool(self) -> None:
        """Test extracting coordinate from computer tool input."""
        tool_input = {"action": "left_click", "coordinate": [450, 300]}

        coord = get_validation_coordinate(tool_input)

        assert coord == (450, 300)

    def test_get_validation_coordinate_returns_none_without_coordinate(self) -> None:
        """Test returns None when no coordinate in input."""
        tool_input = {"action": "screenshot"}

        coord = get_validation_coordinate(tool_input)

        assert coord is None

    def test_get_validation_coordinate_handles_invalid_format(self) -> None:
        """Test handles invalid coordinate format gracefully."""
        tool_input = {"coordinate": "invalid"}

        coord = get_validation_coordinate(tool_input)

        assert coord is None
