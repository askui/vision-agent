"""Basic Caching Example - Introduction to Cache Recording and Execution.

This example demonstrates:
- Recording a trajectory to a cache file (record mode)
- Executing a cached trajectory (execute mode)
- Using both modes together (both mode)
- Cache parameters for dynamic value substitution
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


def record_trajectory_example() -> None:
    """Record a new trajectory to a cache file.

    This example records a simple task (opening Calculator and performing
    a calculation) to a cache file. The first time you run this, the agent
    will perform the task normally. The trajectory will be saved to
    'basic_example.json' for later reuse.
    """
    goal = """Please open the Calculator application and calculate 15 + 27.
    Then close the Calculator application.
    """

    caching_settings = CachingSettings(
        strategy="record",  # Record mode: save trajectory to cache file
        cache_dir=".askui_cache",
        writing_settings=CacheWritingSettings(
            filename="basic_example.json",
            visual_verification_method="phash",  # Use perceptual hashing
            visual_validation_region_size=100,  # 100x100 pixel region around clicks
            visual_validation_threshold=10,  # Hamming distance threshold
            parameter_identification_strategy="llm",  # AI-based parameter detection
        ),
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
    ) as agent:
        agent.act(goal, caching_settings=caching_settings)

    logger.info("✓ Trajectory recorded to .askui_cache/basic_example.json")
    logger.info("Run execute_trajectory_example() to replay this trajectory")


def execute_trajectory_example() -> None:
    """Execute a previously recorded trajectory from cache.

    This example executes the trajectory recorded in record_trajectory_example().
    The agent will replay the exact sequence of actions from the cache file,
    validating the UI state at each step using visual hashing.

    Prerequisites:
    - Run record_trajectory_example() first to create the cache file
    """
    goal = """Please execute the cached trajectory from basic_example.json
    """

    caching_settings = CachingSettings(
        strategy="execute",  # Execute mode: replay from cache file
        cache_dir=".askui_cache",
        execution_settings=CacheExecutionSettings(
            delay_time_between_action=0.5,  # Wait 0.5s between actions
        ),
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
    ) as agent:
        agent.act(goal, caching_settings=caching_settings)

    logger.info("✓ Trajectory executed from cache")


def both_mode_example() -> None:
    """Use both record and execute modes together.

    This example demonstrates the "both" strategy, which:
    1. First tries to execute from cache if available
    2. Falls back to normal execution if cache doesn't exist
    3. Records the trajectory if it wasn't cached

    This is the most flexible mode for development and testing.
    """
    goal = """Please open the TextEdit application, type "Hello from cache!",
    and close the application without saving.
    If available, use cache file at both_mode_example.json
    """

    caching_settings = CachingSettings(
        strategy="both",  # Both: try execute, fall back to record
        cache_dir=".askui_cache",
        writing_settings=CacheWritingSettings(
            filename="both_mode_example.json",
            visual_verification_method="phash",
            parameter_identification_strategy="llm",
        ),
        execution_settings=CacheExecutionSettings(
            delay_time_between_action=0.3,
        ),
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
    ) as agent:
        agent.act(goal, caching_settings=caching_settings)

    logger.info("✓ Task completed using both mode")


def cache_parameters_example() -> None:
    """Demonstrate cache parameters for dynamic value substitution.

    Cache parameters allow you to record a trajectory once and replay it
    with different values. The AI identifies dynamic values (like search
    terms, numbers, dates) and replaces them with {{parameter_name}} syntax.

    When executing the cache, you can provide different values for these
    parameters.
    """
    # First run: Record with original value
    goal_record = """Please open Safari, navigate to www.google.com,
    search for "Python programming", and close Safari.
    """

    caching_settings = CachingSettings(
        strategy="record",
        cache_dir=".askui_cache",
        writing_settings=CacheWritingSettings(
            filename="parameterized_example.json",
            visual_verification_method="phash",
            parameter_identification_strategy="llm",  # AI detects "Python programming" as parameter
        ),
    )

    logger.info("Recording parameterized trajectory...")
    with VisionAgent(display=1, reporters=[SimpleHtmlReporter()]) as agent:
        agent.act(goal_record, caching_settings=caching_settings)

    logger.info("✓ Parameterized trajectory recorded")
    logger.info("The AI identified dynamic values and created parameters")
    logger.info(
        "Check .askui_cache/parameterized_example.json to see {{parameter}} syntax"
    )


if __name__ == "__main__":
    # Run examples in sequence
    print("\n" + "=" * 70)
    print("BASIC CACHING EXAMPLES")
    print("=" * 70 + "\n")

    print("\n1. Recording a trajectory to cache...")
    print("-" * 70)
    record_trajectory_example()

    print("\n2. Executing from cache...")
    print("-" * 70)
    # Uncomment to execute the cached trajectory:
    execute_trajectory_example()

    print("\n3. Using 'both' mode (execute or record)...")
    print("-" * 70)
    # Uncomment to try both mode:
    both_mode_example()

    print("\n4. Cache parameters for dynamic values...")
    print("-" * 70)
    # Uncomment to try parameterized caching:
    cache_parameters_example()

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70 + "\n")
