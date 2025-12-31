"""Visual Validation Example - Demonstrating Visual UI State Validation.

This example demonstrates:
- Visual validation using perceptual hashing (pHash)
- Visual validation using average hashing (aHash)
- Adjusting validation thresholds for strictness
- Handling visual validation failures gracefully
- Understanding when visual validation helps detect UI changes
"""

import logging

from askui import VisionAgent
from askui.models.shared.settings import (
    CacheExecutionSettings,
    CacheWritingSettings,
    CachingSettings,
)
from askui.reporting import SimpleHtmlReporter

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()


def phash_validation_example() -> None:
    """Record and execute with pHash visual validation.

    Perceptual hashing (pHash) is the default and recommended method for
    visual validation. It uses Discrete Cosine Transform (DCT) to create
    a fingerprint of the UI region around each click/action.

    pHash is robust to:
    - Minor image compression artifacts
    - Small lighting changes
    - Slight color variations

    But will detect:
    - UI element position changes
    - Different UI states (buttons, menus, etc.)
    - Major layout changes
    """
    goal = """Please open the System Settings application, click on "General",
    then close the System Settings application.
    If available, use cache file at phash_example.json
    """

    caching_settings = CachingSettings(
        strategy="both",
        cache_dir=".askui_cache",
        writing_settings=CacheWritingSettings(
            filename="phash_example.json",
            visual_verification_method="phash",  # Perceptual hashing (recommended)
            visual_validation_region_size=100,  # 100x100 pixel region
            visual_validation_threshold=10,  # Lower = stricter (0-64 range)
        ),
        execution_settings=CacheExecutionSettings(
            delay_time_between_action=0.5,
        ),
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
    ) as agent:
        agent.act(goal, caching_settings=caching_settings)

    logger.info("✓ pHash validation example completed")
    logger.info("Visual hashes were computed for each click/action")
    logger.info("Check the cache file to see 'visual_representation' fields")


def ahash_validation_example() -> None:
    """Record and execute with aHash visual validation.

    Average hashing (aHash) is an alternative method that computes
    the average pixel values in a region. It's simpler and faster than
    pHash but slightly less robust.

    aHash is good for:
    - Very fast validation
    - Simple UI elements
    - High-contrast interfaces

    Use pHash for better accuracy in most cases.
    """
    goal = """Please open the Finder application, navigate to Documents folder,
    then close the Finder window.
    If available, use cache file at ahash_example.json
    """

    caching_settings = CachingSettings(
        strategy="both",
        cache_dir=".askui_cache",
        writing_settings=CacheWritingSettings(
            filename="ahash_example.json",
            visual_verification_method="ahash",  # Average hashing (alternative)
            visual_validation_region_size=100,
            visual_validation_threshold=10,
        ),
        execution_settings=CacheExecutionSettings(
            delay_time_between_action=0.5,
        ),
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
    ) as agent:
        agent.act(goal, caching_settings=caching_settings)

    logger.info("✓ aHash validation example completed")


def strict_validation_example() -> None:
    """Use strict visual validation (low threshold).

    A lower threshold means stricter validation. The threshold represents
    the maximum Hamming distance (number of differing bits) allowed between
    the cached hash and the current UI state.

    Threshold guidelines:
    - 0-5:  Very strict (detects tiny changes)
    - 6-10: Strict (recommended for stable UIs)
    - 11-15: Moderate (tolerates minor changes)
    - 16+:  Lenient (may miss significant changes)
    """
    goal = """Please open the Calendar application and click on today's date.
    Then close the Calendar application.
    If available, use cache file at strict_validation.json
    """

    caching_settings = CachingSettings(
        strategy="both",
        cache_dir=".askui_cache",
        writing_settings=CacheWritingSettings(
            filename="strict_validation.json",
            visual_verification_method="phash",
            visual_validation_region_size=100,
            visual_validation_threshold=5,  # Very strict validation
        ),
        execution_settings=CacheExecutionSettings(
            delay_time_between_action=0.5,
        ),
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
    ) as agent:
        agent.act(goal, caching_settings=caching_settings)

    logger.info("✓ Strict validation example completed")
    logger.info("Threshold=5 will catch even minor UI changes")


def lenient_validation_example() -> None:
    """Use lenient visual validation (high threshold).

    A higher threshold makes validation more tolerant of UI changes.
    Use this when:
    - UI has dynamic elements (ads, recommendations, etc.)
    - Layout changes slightly between executions
    - You want cache to work across minor UI updates

    Be careful: Too lenient validation may miss important UI changes!
    """
    goal = """Please open Safari, navigate to www.apple.com,
    and close Safari.
    If available, use cache file at lenient_validation.json
    """

    caching_settings = CachingSettings(
        strategy="both",
        cache_dir=".askui_cache",
        writing_settings=CacheWritingSettings(
            filename="lenient_validation.json",
            visual_verification_method="phash",
            visual_validation_region_size=100,
            visual_validation_threshold=20,  # Lenient validation
        ),
        execution_settings=CacheExecutionSettings(
            delay_time_between_action=0.5,
        ),
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
    ) as agent:
        agent.act(goal, caching_settings=caching_settings)

    logger.info("✓ Lenient validation example completed")
    logger.info("Threshold=20 tolerates more UI variation")


def region_size_example() -> None:
    """Demonstrate different validation region sizes.

    The region size determines how large an area around each click point
    is captured and validated. Larger regions capture more context but
    may be less precise.

    Region size guidelines:
    - 50x50:   Small, precise validation of exact click target
    - 100x100: Balanced (recommended default)
    - 150x150: Large, includes more surrounding UI context
    - 200x200: Very large, captures entire UI section
    """
    goal = """Please open the Notes application, click on "New Note" button,
    and close Notes without saving.
    If available, use cache file at region_size_example.json
    """

    caching_settings = CachingSettings(
        strategy="both",
        cache_dir=".askui_cache",
        writing_settings=CacheWritingSettings(
            filename="region_size_example.json",
            visual_verification_method="phash",
            visual_validation_region_size=150,  # Larger region for more context
            visual_validation_threshold=10,
        ),
        execution_settings=CacheExecutionSettings(
            delay_time_between_action=0.5,
        ),
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
    ) as agent:
        agent.act(goal, caching_settings=caching_settings)

    logger.info("✓ Region size example completed")
    logger.info("Used 150x150 pixel region for validation")


def no_validation_example() -> None:
    """Disable visual validation entirely.

    Set visual_verification_method="none" to disable visual validation.
    The cache will still work, but won't verify UI state during execution.

    Use this when:
    - You trust the cache completely
    - UI changes frequently and validation would fail
    - Performance is critical (validation adds small overhead)

    Warning: Without validation, cached actions may execute on wrong UI!
    """
    goal = """Please open the Music application and close it.
    If available, use cache file at no_validation_example.json
    """

    caching_settings = CachingSettings(
        strategy="both",
        cache_dir=".askui_cache",
        writing_settings=CacheWritingSettings(
            filename="no_validation_example.json",
            visual_verification_method="none",  # Disable visual validation
        ),
        execution_settings=CacheExecutionSettings(
            delay_time_between_action=0.5,
        ),
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
    ) as agent:
        agent.act(goal, caching_settings=caching_settings)

    logger.info("✓ No validation example completed")
    logger.info("Cache executed without visual validation")


if __name__ == "__main__":
    # Run examples to demonstrate different validation modes
    print("\n" + "=" * 70)
    print("VISUAL VALIDATION EXAMPLES")
    print("=" * 70 + "\n")

    print("\n1. pHash validation (recommended)...")
    print("-" * 70)
    phash_validation_example()

    print("\n2. aHash validation (alternative)...")
    print("-" * 70)
    # Uncomment to try aHash:
    ahash_validation_example()

    print("\n3. Strict validation (threshold=5)...")
    print("-" * 70)
    # Uncomment to try strict validation:
    strict_validation_example()

    print("\n4. Lenient validation (threshold=20)...")
    print("-" * 70)
    # Uncomment to try lenient validation:
    lenient_validation_example()

    print("\n5. Large region size (150x150)...")
    print("-" * 70)
    # Uncomment to try larger region:
    region_size_example()

    print("\n6. No validation (disabled)...")
    print("-" * 70)
    # Uncomment to try without validation:
    no_validation_example()

    print("\n" + "=" * 70)
    print("Visual validation examples completed!")
    print("=" * 70 + "\n")

    print("\nKey Takeaways:")
    print("- pHash is recommended for most use cases (robust and accurate)")
    print("- Threshold 5-10 is good for stable UIs")
    print("- Threshold 15-20 is better for dynamic UIs")
    print("- Region size 100x100 is a good default")
    print("- Visual validation helps detect unexpected UI changes")
    print()
