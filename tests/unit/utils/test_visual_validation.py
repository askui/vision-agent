"""Tests for visual validation utilities."""

import pytest
from PIL import Image

from askui.models.shared.agent_message_param import (
    ContentBlockParam,
    ImageBlockParam,
    MessageParam,
    TextBlockParam,
    ToolResultBlockParam,
    ToolUseBlockParam,
)
from askui.utils.visual_validation import (
    compute_ahash,
    compute_hamming_distance,
    compute_phash,
    extract_region,
    find_recent_screenshot,
)


class TestComputePhash:
    """Test perceptual hash computation."""

    def test_compute_phash_returns_string(
        self, github_login_screenshot: Image.Image
    ) -> None:
        """Test that phash returns a string hash."""
        hash_result = compute_phash(github_login_screenshot, hash_size=8)
        assert isinstance(hash_result, str)
        assert len(hash_result) > 0

    def test_compute_phash_consistent(
        self, github_login_screenshot: Image.Image
    ) -> None:
        """Test that phash produces consistent results for same image."""
        hash1 = compute_phash(github_login_screenshot, hash_size=8)
        hash2 = compute_phash(github_login_screenshot, hash_size=8)
        assert hash1 == hash2

    def test_compute_phash_different_sizes(
        self, github_login_screenshot: Image.Image
    ) -> None:
        """Test that different hash sizes produce different length hashes."""
        hash_8 = compute_phash(github_login_screenshot, hash_size=8)
        hash_16 = compute_phash(github_login_screenshot, hash_size=16)
        # Hash sizes should differ: 8x8=64 bits vs 16x16=256 bits
        assert len(hash_8) != len(hash_16)

    def test_compute_phash_identical_images_identical_hash(
        self, github_login_screenshot: Image.Image
    ) -> None:
        """Test that identical images produce identical hashes."""
        # Create a copy of the image
        img_copy = github_login_screenshot.copy()
        hash1 = compute_phash(github_login_screenshot, hash_size=8)
        hash2 = compute_phash(img_copy, hash_size=8)
        assert hash1 == hash2


class TestComputeAhash:
    """Test average hash computation."""

    def test_compute_ahash_returns_string(
        self, github_login_screenshot: Image.Image
    ) -> None:
        """Test that ahash returns a string hash."""
        hash_result = compute_ahash(github_login_screenshot, hash_size=8)
        assert isinstance(hash_result, str)
        assert len(hash_result) > 0

    def test_compute_ahash_consistent(
        self, github_login_screenshot: Image.Image
    ) -> None:
        """Test that ahash produces consistent results for same image."""
        hash1 = compute_ahash(github_login_screenshot, hash_size=8)
        hash2 = compute_ahash(github_login_screenshot, hash_size=8)
        assert hash1 == hash2

    def test_compute_ahash_different_sizes(
        self, github_login_screenshot: Image.Image
    ) -> None:
        """Test that different hash sizes produce different length hashes."""
        hash_8 = compute_ahash(github_login_screenshot, hash_size=8)
        hash_16 = compute_ahash(github_login_screenshot, hash_size=16)
        assert len(hash_8) != len(hash_16)


class TestComputeHammingDistance:
    """Test Hamming distance computation."""

    def test_hamming_distance_identical_hashes(
        self, github_login_screenshot: Image.Image
    ) -> None:
        """Test that identical hashes have zero Hamming distance."""
        hash1 = compute_phash(github_login_screenshot, hash_size=8)
        distance = compute_hamming_distance(hash1, hash1)
        assert distance == 0

    def test_hamming_distance_different_hashes(
        self, github_login_screenshot: Image.Image, white_page_screenshot: Image.Image
    ) -> None:
        """Test that different images have non-zero Hamming distance."""
        hash1 = compute_phash(github_login_screenshot, hash_size=8)
        hash2 = compute_phash(white_page_screenshot, hash_size=8)
        distance = compute_hamming_distance(hash1, hash2)
        assert distance > 0

    def test_hamming_distance_symmetric(
        self, github_login_screenshot: Image.Image, white_page_screenshot: Image.Image
    ) -> None:
        """Test that Hamming distance is symmetric."""
        hash1 = compute_phash(github_login_screenshot, hash_size=8)
        hash2 = compute_phash(white_page_screenshot, hash_size=8)
        distance1 = compute_hamming_distance(hash1, hash2)
        distance2 = compute_hamming_distance(hash2, hash1)
        assert distance1 == distance2

    def test_hamming_distance_single_bit_difference(self) -> None:
        """Test Hamming distance with known hash values."""
        # Binary representations differ by 1 bit: 0000 vs 0001
        hash1 = "0" * 64  # All zeros
        hash2 = "0" * 63 + "1"  # One bit different
        distance = compute_hamming_distance(hash1, hash2)
        assert distance == 1

    def test_hamming_distance_all_bits_different(self) -> None:
        """Test Hamming distance when all bits differ."""
        hash1 = "0" * 64
        hash2 = "1" * 64
        distance = compute_hamming_distance(hash1, hash2)
        assert distance == 64


class TestExtractRegion:
    """Test region extraction from images."""

    def test_extract_region_center(self, github_login_screenshot: Image.Image) -> None:
        """Test extracting a region from the center of an image."""
        width, height = github_login_screenshot.size
        center_x, center_y = width // 2, height // 2
        region_size = 50

        region = extract_region(
            github_login_screenshot,
            {"coordinate": [center_x, center_y]},
            region_size=region_size,
        )

        assert isinstance(region, Image.Image)
        assert region.size == (region_size, region_size)

    def test_extract_region_edge(self, github_login_screenshot: Image.Image) -> None:
        """Test extracting a region near the edge (should be clipped)."""
        width, height = github_login_screenshot.size
        edge_x, edge_y = width - 10, height - 10
        region_size = 50

        region = extract_region(
            github_login_screenshot,
            {"coordinate": [edge_x, edge_y]},
            region_size=region_size,
        )

        assert isinstance(region, Image.Image)
        # Region should be clipped at the edge
        assert region.size[0] <= region_size
        assert region.size[1] <= region_size

    def test_extract_region_corner(self, github_login_screenshot: Image.Image) -> None:
        """Test extracting a region from a corner."""
        region_size = 50

        region = extract_region(
            github_login_screenshot,
            {"coordinate": [0, 0]},
            region_size=region_size,
        )

        assert isinstance(region, Image.Image)
        assert region.size[0] <= region_size
        assert region.size[1] <= region_size

    def test_extract_region_with_text(
        self, github_login_screenshot: Image.Image
    ) -> None:
        """Test extracting a region for text_entry action."""
        width, height = github_login_screenshot.size
        center_x, center_y = width // 2, height // 2
        region_size = 50

        region = extract_region(
            github_login_screenshot,
            {"coordinate": [center_x, center_y], "text": "example"},
            region_size=region_size,
        )

        assert isinstance(region, Image.Image)
        assert region.size == (region_size, region_size)

    def test_extract_region_small_image(self) -> None:
        """Test extracting a region from a very small image."""
        small_img = Image.new("RGB", (10, 10), color="white")
        region_size = 50

        region = extract_region(
            small_img,
            {"coordinate": [5, 5]},
            region_size=region_size,
        )

        assert isinstance(region, Image.Image)
        # Region should be clipped to image size
        assert region.size == (10, 10)


class TestFindRecentScreenshot:
    """Test screenshot extraction from message history."""

    def test_find_recent_screenshot_from_tool_result(self) -> None:
        """Test finding screenshot from a tool result message."""
        # Create a dummy image
        test_image = Image.new("RGB", (100, 100), color="red")

        # Convert to base64
        from askui.utils.image_utils import image_to_base64

        image_base64 = image_to_base64(test_image)

        # Create message history with tool result containing image
        messages = [
            MessageParam(
                role="assistant",
                content=[
                    ToolUseBlockParam(
                        type="tool_use",
                        id="tool_1",
                        name="computer",
                        input={"action": "screenshot"},
                    )
                ],
            ),
            MessageParam(
                role="user",
                content=[
                    ToolResultBlockParam(
                        type="tool_result",
                        tool_use_id="tool_1",
                        content=[
                            ImageBlockParam(
                                type="image",
                                source={
                                    "type": "base64",
                                    "data": image_base64,
                                    "media_type": "image/png",
                                },
                            )
                        ],
                    )
                ],
            ),
        ]

        screenshot = find_recent_screenshot(messages)
        assert screenshot is not None
        assert isinstance(screenshot, Image.Image)
        assert screenshot.size == (100, 100)

    def test_find_recent_screenshot_with_from_index(self) -> None:
        """Test finding screenshot with from_index parameter."""
        # Create dummy images
        image1 = Image.new("RGB", (100, 100), color="red")
        image2 = Image.new("RGB", (100, 100), color="blue")

        from askui.utils.image_utils import image_to_base64

        image1_base64 = image_to_base64(image1)
        image2_base64 = image_to_base64(image2)

        # Create message history with multiple screenshots
        messages = [
            MessageParam(
                role="user",
                content=[
                    ToolResultBlockParam(
                        type="tool_result",
                        tool_use_id="tool_1",
                        content=[
                            ImageBlockParam(
                                type="image",
                                source={
                                    "type": "base64",
                                    "data": image1_base64,
                                    "media_type": "image/png",
                                },
                            )
                        ],
                    )
                ],
            ),
            MessageParam(
                role="assistant",
                content=[
                    ToolUseBlockParam(
                        type="tool_use",
                        id="tool_2",
                        name="computer",
                        input={"action": "click", "coordinate": [50, 50]},
                    )
                ],
            ),
            MessageParam(
                role="user",
                content=[
                    ToolResultBlockParam(
                        type="tool_result",
                        tool_use_id="tool_2",
                        content=[
                            ImageBlockParam(
                                type="image",
                                source={
                                    "type": "base64",
                                    "data": image2_base64,
                                    "media_type": "image/png",
                                },
                            )
                        ],
                    )
                ],
            ),
        ]

        # Find screenshot before index 2 (should return first screenshot)
        screenshot = find_recent_screenshot(messages, from_index=1)
        assert screenshot is not None
        # Verify it's the first image (red) by checking a pixel
        pixel = screenshot.getpixel((0, 0))
        assert pixel == (255, 0, 0)  # Red

    def test_find_recent_screenshot_no_screenshot(self) -> None:
        """Test when no screenshot exists in message history."""
        messages = [
            MessageParam(
                role="assistant",
                content=[
                    ToolUseBlockParam(
                        type="tool_use",
                        id="tool_1",
                        name="computer",
                        input={"action": "click", "coordinate": [50, 50]},
                    )
                ],
            ),
            MessageParam(
                role="user",
                content=[
                    ToolResultBlockParam(
                        type="tool_result",
                        tool_use_id="tool_1",
                        content=[TextBlockParam(type="text", text="Success")],
                    )
                ],
            ),
        ]

        screenshot = find_recent_screenshot(messages)
        assert screenshot is None

    def test_find_recent_screenshot_empty_messages(self) -> None:
        """Test with empty message history."""
        messages: list[MessageParam] = []
        screenshot = find_recent_screenshot(messages)
        assert screenshot is None

    def test_find_recent_screenshot_only_text_content(self) -> None:
        """Test when messages only contain text content."""
        messages = [
            MessageParam(
                role="assistant",
                content="Hello, how can I help you?",
            ),
            MessageParam(
                role="user",
                content="Please click the button.",
            ),
        ]

        screenshot = find_recent_screenshot(messages)
        assert screenshot is None

    def test_find_recent_screenshot_mixed_content(self) -> None:
        """Test finding screenshot in messages with mixed content types."""
        test_image = Image.new("RGB", (100, 100), color="green")

        from askui.utils.image_utils import image_to_base64

        image_base64 = image_to_base64(test_image)

        messages = [
            MessageParam(
                role="assistant",
                content="Starting task...",
            ),
            MessageParam(
                role="user",
                content=[
                    TextBlockParam(type="text", text="Here is the screenshot:"),
                    ToolResultBlockParam(
                        type="tool_result",
                        tool_use_id="tool_1",
                        content=[
                            ImageBlockParam(
                                type="image",
                                source={
                                    "type": "base64",
                                    "data": image_base64,
                                    "media_type": "image/png",
                                },
                            )
                        ],
                    ),
                ],
            ),
        ]

        screenshot = find_recent_screenshot(messages)
        assert screenshot is not None
        assert isinstance(screenshot, Image.Image)
        pixel = screenshot.getpixel((0, 0))
        assert pixel == (0, 128, 0)  # Green


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple functions."""

    def test_full_visual_validation_workflow(
        self, github_login_screenshot: Image.Image
    ) -> None:
        """Test complete workflow: extract region, compute hash, compare."""
        # Extract region
        width, height = github_login_screenshot.size
        center_x, center_y = width // 2, height // 2
        region = extract_region(
            github_login_screenshot,
            {"coordinate": [center_x, center_y]},
            region_size=50,
        )

        # Compute hashes
        hash1 = compute_phash(region, hash_size=8)
        hash2 = compute_phash(region, hash_size=8)

        # Verify identical
        distance = compute_hamming_distance(hash1, hash2)
        assert distance == 0

    def test_similar_images_small_distance(
        self, github_login_screenshot: Image.Image
    ) -> None:
        """Test that similar images have small Hamming distance."""
        # Create a slightly modified copy
        img_copy = github_login_screenshot.copy()
        # Add a small change (draw one pixel)
        pixels = img_copy.load()
        if pixels is not None:
            pixels[0, 0] = (255, 0, 0)

        hash1 = compute_phash(github_login_screenshot, hash_size=8)
        hash2 = compute_phash(img_copy, hash_size=8)
        distance = compute_hamming_distance(hash1, hash2)

        # Distance should be very small (perceptual hash is robust to minor changes)
        assert distance < 5  # Threshold for "similar"

    def test_different_images_large_distance(
        self, github_login_screenshot: Image.Image, white_page_screenshot: Image.Image
    ) -> None:
        """Test that different images have large Hamming distance."""
        hash1 = compute_phash(github_login_screenshot, hash_size=8)
        hash2 = compute_phash(white_page_screenshot, hash_size=8)
        distance = compute_hamming_distance(hash1, hash2)

        # Distance should be significant for completely different images
        assert distance > 10  # Threshold for "different"

    def test_recording_validation_scenario(
        self, github_login_screenshot: Image.Image
    ) -> None:
        """Test scenario simulating recording and validation phases."""
        # RECORDING phase: Extract region and compute hash
        action_input = {"action": "click", "coordinate": [100, 100]}
        recorded_region = extract_region(
            github_login_screenshot, action_input, region_size=50
        )
        recorded_hash = compute_phash(recorded_region, hash_size=8)

        # VALIDATION phase: Extract same region and compute hash
        validation_region = extract_region(
            github_login_screenshot, action_input, region_size=50
        )
        validation_hash = compute_phash(validation_region, hash_size=8)

        # Compare hashes
        distance = compute_hamming_distance(recorded_hash, validation_hash)
        assert distance == 0  # Should be identical for same input


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_extract_region_negative_coordinates(
        self, github_login_screenshot: Image.Image
    ) -> None:
        """Test extracting region with negative coordinates (should handle gracefully)."""
        region = extract_region(
            github_login_screenshot,
            {"coordinate": [-10, -10]},
            region_size=50,
        )

        assert isinstance(region, Image.Image)
        # Should clip to valid region starting at (0, 0)
        assert region.size[0] > 0
        assert region.size[1] > 0

    def test_extract_region_out_of_bounds(
        self, github_login_screenshot: Image.Image
    ) -> None:
        """Test extracting region completely out of bounds."""
        width, height = github_login_screenshot.size
        region = extract_region(
            github_login_screenshot,
            {"coordinate": [width + 100, height + 100]},
            region_size=50,
        )

        assert isinstance(region, Image.Image)
        # Should handle gracefully, returning empty or minimal region
        assert region.size[0] >= 0
        assert region.size[1] >= 0

    def test_hamming_distance_different_lengths(self) -> None:
        """Test Hamming distance with different hash lengths."""
        hash1 = "0" * 64
        hash2 = "0" * 32  # Different length

        with pytest.raises((ValueError, AssertionError)):
            compute_hamming_distance(hash1, hash2)

    def test_compute_hash_grayscale_image(self) -> None:
        """Test computing hash on grayscale image."""
        gray_img = Image.new("L", (100, 100), color=128)
        hash_result = compute_phash(gray_img, hash_size=8)
        assert isinstance(hash_result, str)
        assert len(hash_result) > 0

    def test_compute_hash_rgba_image(self) -> None:
        """Test computing hash on RGBA image."""
        rgba_img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        hash_result = compute_phash(rgba_img, hash_size=8)
        assert isinstance(hash_result, str)
        assert len(hash_result) > 0
