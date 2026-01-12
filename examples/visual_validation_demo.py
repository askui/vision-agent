"""
Visual Validation Demo

This example demonstrates how to use visual validation with cache trajectories.
Visual validation helps ensure that the UI state during cache execution matches
the recorded state, preventing cached actions from executing in the wrong context.

Usage:
    1. Run this script once to record a trajectory with visual validation
    2. Run it again to replay with visual validation
    3. Try changing the UI and observe validation failure handling
"""

import logging

from askui import VisionAgent
from askui.models.shared.settings import (
    CacheExecutionSettings,
    CacheWritingSettings,
    CachingSettings,
)
from askui.reporting import SimpleHtmlReporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def record_with_visual_validation() -> None:
    """Record a trajectory with visual validation enabled."""
    logger.info("=" * 60)
    logger.info("RECORDING: Creating cache with visual validation")
    logger.info("=" * 60)

    goal = """Please open a new window in Google Chrome by right clicking on the icon
    in the Dock at the bottom of the screen. Then, navigate to www.example.com.

    This trajectory will be recorded with visual validation enabled, which means
    visual hashes will be computed for each click and text_entry action.
    """

    caching_settings = CachingSettings(
        strategy="record",
        cache_dir=".askui_cache",
        writing_settings=CacheWritingSettings(
            filename="visual_validation_demo.json",
            # Visual validation settings
            visual_verification_method="phash",  # Use perceptual hash
            visual_validation_region_size=100,  # 100px region around action
            visual_validation_threshold=10,  # Hamming distance threshold
        ),
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
        act_model_name="claude-sonnet-4-5-20250929",
    ) as agent:
        agent.act(goal, caching_settings=caching_settings)

    logger.info("✓ Recording complete! Visual hashes stored in cache file.")


def replay_with_visual_validation() -> None:
    """Replay a trajectory with visual validation enabled."""
    logger.info("=" * 60)
    logger.info("REPLAYING: Executing cache with visual validation")
    logger.info("=" * 60)

    goal = """Please open a new window in Google Chrome and navigate to www.example.com.

    If the cache file 'visual_validation_demo.json' is available, please use it
    to replay the actions. Visual validation will check that the UI state matches
    the recorded state before executing each cached action.

    If visual validation fails (UI has changed), the agent will take over and
    continue manually.
    """

    caching_settings = CachingSettings(
        strategy="execute",
        cache_dir=".askui_cache",
        execution_settings=CacheExecutionSettings(
            delay_time_between_action=0.5,  # Wait 0.5s between actions
            skip_visual_validation=False,  # Enable visual validation
        ),
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
        act_model_name="claude-sonnet-4-5-20250929",
    ) as agent:
        agent.act(goal, caching_settings=caching_settings)

    logger.info("✓ Replay complete!")


def replay_without_visual_validation() -> None:
    """Replay a trajectory with visual validation disabled."""
    logger.info("=" * 60)
    logger.info("REPLAYING: Executing cache WITHOUT visual validation")
    logger.info("=" * 60)

    goal = """Please open a new window in Google Chrome and navigate to www.example.com.

    If the cache file 'visual_validation_demo.json' is available, please use it.
    In this execution, visual validation is disabled, so cached actions will execute
    even if the UI has changed.
    """

    caching_settings = CachingSettings(
        strategy="execute",
        cache_dir=".askui_cache",
        execution_settings=CacheExecutionSettings(
            delay_time_between_action=0.5,
            skip_visual_validation=True,  # Disable visual validation
        ),
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
        act_model_name="claude-sonnet-4-5-20250929",
    ) as agent:
        agent.act(goal, caching_settings=caching_settings)

    logger.info("✓ Replay complete (validation skipped)!")


def demo_different_thresholds() -> None:
    """Demonstrate how threshold affects validation sensitivity."""
    logger.info("=" * 60)
    logger.info("DEMO: Testing different validation thresholds")
    logger.info("=" * 60)

    # Record with default threshold (10)
    logger.info("\n1. Recording with threshold=10 (moderate sensitivity)...")
    caching_settings = CachingSettings(
        strategy="record",
        cache_dir=".askui_cache",
        writing_settings=CacheWritingSettings(
            filename="threshold_demo.json",
            visual_verification_method="phash",
            visual_validation_threshold=10,  # Moderate
        ),
    )

    goal = "Click on the Chrome icon in the Dock."

    with VisionAgent(display=1, act_model_name="claude-sonnet-4-5-20250929") as agent:
        agent.act(goal, caching_settings=caching_settings)

    # Replay with strict threshold (5)
    logger.info(
        "\n2. Replaying with threshold=5 (strict - more likely to detect changes)..."
    )
    caching_settings = CachingSettings(
        strategy="execute",
        cache_dir=".askui_cache",
        execution_settings=CacheExecutionSettings(
            skip_visual_validation=False,
        ),
    )

    # Note: threshold comes from cache file metadata, not execution settings
    # To override, need to modify cache file or re-record

    logger.info(
        "\n✓ Lower threshold = stricter validation (more sensitive to UI changes)"
    )
    logger.info("✓ Higher threshold = looser validation (tolerates minor differences)")


def main() -> None:
    """Run the complete visual validation demo."""
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        logger.info(
            "Usage: python visual_validation_demo.py [record|replay|replay-no-validation]"
        )
        logger.info("Running in RECORD mode by default...")
        mode = "record"

    if mode == "record":
        record_with_visual_validation()
    elif mode == "replay":
        replay_with_visual_validation()
    elif mode == "replay-no-validation":
        replay_without_visual_validation()
    elif mode == "thresholds":
        demo_different_thresholds()
    else:
        logger.error(f"Unknown mode: {mode}")
        logger.error(
            "Valid modes: record, replay, replay-no-validation, thresholds"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
