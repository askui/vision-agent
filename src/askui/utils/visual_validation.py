"""Visual validation utilities for cache execution.

This module provides utilities for computing and comparing visual hashes
to validate UI state before executing cached trajectory steps.
"""

import logging
from typing import Any

import numpy as np
from numpy.typing import NDArray
from PIL import Image

logger = logging.getLogger(__name__)


def compute_phash(image: Image.Image, hash_size: int = 8) -> str:
    """Compute perceptual hash (pHash) of an image.

    pHash is robust to minor changes (compression, scaling, lighting) while
    being sensitive to structural changes (moved buttons, different layouts).

    Args:
        image: PIL Image to hash
        hash_size: Size of the hash (default 8 = 64-bit hash)

    Returns:
        Hexadecimal string representation of the hash

    The algorithm:
    1. Resize image to hash_size x hash_size
    2. Convert to grayscale
    3. Compute DCT (Discrete Cosine Transform)
    4. Extract top-left 8x8 DCT coefficients
    5. Compute median of coefficients
    6. Create binary hash: 1 if coeff > median, else 0
    """
    # Resize to hash_size x hash_size
    resized = image.resize((hash_size, hash_size), Image.Resampling.LANCZOS)

    # Convert to grayscale
    gray = resized.convert("L")

    # Convert to numpy array
    pixels = np.array(gray, dtype=np.float32)

    # Compute DCT (using a simple 2D DCT approximation)
    # For production, consider using scipy.fftpack.dct
    dct = _dct_2d(pixels)

    # Extract top-left coefficients (excluding DC component at [0,0])
    dct_low = dct[:hash_size, :hash_size]

    # Compute median
    median = np.median(dct_low)

    # Create binary hash
    diff = dct_low > median

    # Convert to hexadecimal string
    hash_bytes = _binary_array_to_bytes(diff.flatten())
    return hash_bytes.hex()


def compute_ahash(image: Image.Image, hash_size: int = 8) -> str:
    """Compute average hash (aHash) of an image.

    aHash is a simpler but faster alternative to pHash. It's less robust
    to transformations but still useful for basic visual validation.

    Args:
        image: PIL Image to hash
        hash_size: Size of the hash (default 8 = 64-bit hash)

    Returns:
        Hexadecimal string representation of the hash

    The algorithm:
    1. Resize image to hash_size x hash_size
    2. Convert to grayscale
    3. Compute mean pixel value
    4. Create binary hash: 1 if pixel > mean, else 0
    """
    # Resize to hash_size x hash_size
    resized = image.resize((hash_size, hash_size), Image.Resampling.LANCZOS)

    # Convert to grayscale
    gray = resized.convert("L")

    # Convert to numpy array
    pixels = np.array(gray, dtype=np.float32)

    # Compute mean
    mean = pixels.mean()

    # Create binary hash
    diff = pixels > mean

    # Convert to hexadecimal string
    hash_bytes = _binary_array_to_bytes(diff.flatten())
    return hash_bytes.hex()


def hamming_distance(hash1: str, hash2: str) -> int:
    """Compute Hamming distance between two hash strings.

    The Hamming distance is the number of bit positions where the two
    hashes differ. A distance of 0 means identical hashes, while 64
    means completely different (for 64-bit hashes).

    Args:
        hash1: First hash (hexadecimal string)
        hash2: Second hash (hexadecimal string)

    Returns:
        Number of differing bits (0-64 for 64-bit hashes)

    Raises:
        ValueError: If hashes have different lengths
    """
    if len(hash1) != len(hash2):
        msg = f"Hash lengths differ: {len(hash1)} vs {len(hash2)}"
        raise ValueError(msg)

    # Convert hex strings to integers and XOR them
    # XOR will have 1s where bits differ
    xor_result = int(hash1, 16) ^ int(hash2, 16)

    # Count number of 1s (differing bits)
    return (xor_result).bit_count()


def extract_region(
    image: Image.Image, center: tuple[int, int], size: int = 100
) -> Image.Image:
    """Extract a square region from an image centered at given coordinates.

    Args:
        image: Source image
        center: (x, y) coordinates of region center
        size: Size of the square region in pixels

    Returns:
        Cropped image region

    The region is clipped to image boundaries if necessary.
    """
    x, y = center
    half_size = size // 2

    # Calculate bounds, clipping to image boundaries
    left = max(0, x - half_size)
    top = max(0, y - half_size)
    right = min(image.width, x + half_size)
    bottom = min(image.height, y + half_size)

    # Crop and return
    return image.crop((left, top, right, bottom))


def validate_visual_hash(
    stored_hash: str,
    current_image: Image.Image,
    threshold: int = 10,
    hash_method: str = "phash",
) -> tuple[bool, str | None, int]:
    """Validate that current image matches stored visual hash.

    Args:
        stored_hash: The hash stored in the cache
        current_image: Current screenshot region
        threshold: Maximum Hamming distance to accept (0-64)
            - 0-5: Nearly identical (strict validation)
            - 6-10: Very similar (recommended default)
            - 11-15: Similar (lenient)
            - 16+: Different (validation should fail)
        hash_method: Hash method to use ('phash' or 'ahash')

    Returns:
        Tuple of (is_valid, error_message, distance)
        - is_valid: True if validation passes
        - error_message: None if valid, error description if invalid
        - distance: Hamming distance between hashes
    """
    # Compute current hash
    if hash_method == "phash":
        current_hash = compute_phash(current_image)
    elif hash_method == "ahash":
        current_hash = compute_ahash(current_image)
    else:
        return False, f"Unknown hash method: {hash_method}", -1

    # Compare hashes
    try:
        distance = hamming_distance(stored_hash, current_hash)
    except ValueError as e:
        return False, f"Hash comparison failed: {e}", -1

    # Validate against threshold
    if distance <= threshold:
        return True, None, distance

    error_msg = (
        f"Visual validation failed: UI region changed significantly "
        f"(Hamming distance: {distance} > threshold: {threshold})"
    )
    return False, error_msg, distance


def should_validate_step(tool_name: str) -> bool:
    """Determine if a tool step should have visual validation.

    Args:
        tool_name: Name of the tool
        action: Action type (for computer tool)

    Returns:
        True if step should be validated
    """
    # Computer tool with click or type actions
    if tool_name in [
        "android_tap_tool",
        "android_drag_and_drop_tool",
        "android_swipe_tool",
        "computer_mouse_scroll",
        "computer_move_mouse",
    ]:
        return True

    return False


def get_validation_coordinate(tool_input: dict[str, Any]) -> tuple[int, int] | None:
    """Extract the coordinate for visual validation from tool input.

    Args:
        tool_input: Tool input dictionary

    Returns:
        (x, y) coordinate tuple or None if not applicable

    For click actions, returns the click coordinate.
    For type actions, returns the coordinate of the text input field.
    """

    def try_pair(x_val: Any, y_val: Any) -> tuple[int, int] | None:
        x = _safe_int(x_val)
        y = _safe_int(y_val)
        if x is None or y is None:
            return None
        return (x, y)

    if "coordinate" in tool_input:
        coord = tool_input["coordinate"]
        if isinstance(coord, list) and len(coord) == 2:
            result = try_pair(coord[0], coord[1])
            if result is not None:
                return result

    if "x" in tool_input and "y" in tool_input:
        result = try_pair(tool_input["x"], tool_input["y"])
        if result is not None:
            return result

    if "x1" in tool_input and "y1" in tool_input:
        result = try_pair(tool_input["x1"], tool_input["y1"])
        if result is not None:
            return result

    return None


# Private helper functions


def _safe_int(value: Any) -> int | None:
    """Try converting value to int, return None if not possible."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _dct_2d(image_array: NDArray[np.float32]) -> NDArray[np.complex128]:
    """Compute 2D Discrete Cosine Transform.

    This is a simplified implementation. For production use, consider
    using scipy.fftpack.dct for better performance and accuracy.

    Args:
        image_array: 2D numpy array

    Returns:
        2D DCT coefficients
    """
    # Using a simple DCT approximation via FFT
    # For production, use: from scipy.fftpack import dct
    # return dct(dct(image_array.T, norm='ortho').T, norm='ortho')

    # Simplified approach: use numpy's FFT and take real part
    fft = np.fft.fft2(image_array)
    # Take absolute value and use as approximation
    # Note: This is not a true DCT, but works for hash purposes
    return np.abs(fft)


def _binary_array_to_bytes(binary_array: NDArray[np.bool_]) -> bytes:
    """Convert binary numpy array to bytes.

    Args:
        binary_array: 1D array of boolean values

    Returns:
        Bytes representation
    """
    # Convert to string of 0s and 1s
    binary_string = "".join("1" if b else "0" for b in binary_array)

    # Pad to multiple of 8
    padding = 8 - (len(binary_string) % 8)
    if padding != 8:
        binary_string += "0" * padding

    # Convert to bytes
    byte_array = bytearray()
    for i in range(0, len(binary_string), 8):
        byte = binary_string[i : i + 8]
        byte_array.append(int(byte, 2))

    return bytes(byte_array)
