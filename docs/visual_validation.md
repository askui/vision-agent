# Visual Validation for Caching

> **Status**: ✅ Implemented
> **Version**: v0.2
> **Last Updated**: 2025-12-30

## Overview

Visual validation verifies that the UI state matches expectations before executing cached trajectory steps. This significantly improves cache reliability by detecting UI changes that would cause cached actions to fail.

The system stores visual representations (perceptual hashes) of UI regions where actions like clicks are executed. During cache execution, these hashes are compared with the current UI state to detect changes.

## How are the visual Representations computed

We can think of multiple methods, e.g. aHash, pHash, ...

**Key Necessary Properties:**
- Fast computation (~1-2ms per hash)
- Small storage footprint (64 bits = 8 bytes)
- Robust to minor changes (compression, scaling, lighting)
- Sensitive to structural changes (moved buttons, different layouts)

Which method was used will be added to the metadata field of the cached trajectory.


## How It Works

### 1. Representation Storage

When a trajectory is recorded and cached, visual representations will be captured for critical steps:

```json
{
  "type": "tool_use",
  "name": "computer",
  "input": {
    "action": "left_click",
    "coordinate": [450, 300]
  },
  "visual_representation": "a8f3c9e14b7d2056"
}
```

**Which steps should be validated?**
- Mouse clicks (left_click, right_click, double_click, middle_click)
- Type actions (verify input field hasn't moved)
- Key presses targeting specific UI elements

**Hash region selection:**
- For clicks: Capture region around click coordinate (e.g., 100x100px centered on target)
- For type actions: Capture region around text input field (e.g., 100x100px centered on target)

### 2. Hash Verification (During Cache Execution)

Before executing each step that has a `visual_representation`:

1. **Capture current screen region** at the same coordinates used during recording
2. **Compute visual Representation, e.g. aHash** of the current region
3. **Compare with stored hash** using Hamming distance
4. **Make decision** based on threshold:

```python
def should_validate_step(stored_hash: str, current_screen: Image, threshold: int = 10) -> bool:
    """
    Check if visual validation passes.

    Args:
        stored_hash: The aHash stored in the cache
        current_screen: Current screenshot region
        threshold: Maximum Hamming distance (0-64)
            - 0-5: Nearly identical (recommended for strict validation)
            - 6-10: Very similar (default - allows minor changes)
            - 11-15: Similar (more lenient)
            - 16+: Different (validation should fail)

    Returns:
        True if validation passes, False if UI has changed significantly
    """
    current_hash = compute_ahash(current_screen)
    distance = hamming_distance(stored_hash, current_hash)
    return distance <= threshold
```

### 3. Validation Results

**If validation passes** (distance ≤ threshold):
- ✅ Execute the cached step normally
- Continue with trajectory execution

**If validation fails** (distance > threshold):
- ⚠️ Pause trajectory execution
- Return control to agent with detailed information:
  ```
  Visual validation failed at step 5 (left_click at [450, 300]) as the UI region has changed significantly as compared to during recording time.
  Please  Inspect the current UI state and perform the necessary step.
  ```

## Configuration

Visual validation is configured in the Cache Settings:

```python
# In settings
class CachingSettings:
    visual_verification_method: CACHING_VISUAL_VERIFICATION_METHOD = "phash"  # or "ahash", "none"

class CachedExecutionToolSettings:
    visual_validation_threshold: int = 10  # Hamming distance threshold (0-64)
```

**Configuration Options:**
- `visual_verification_method`: Hash method to use
  - `"phash"` (default): Perceptual hash - robust to minor changes, sensitive to structural changes
  - `"ahash"`: Average hash - faster but less robust
  - `"none"`: Disable visual validation
- `visual_validation_threshold`: Maximum allowed Hamming distance (0-64)
  - `0-5`: Nearly identical (strict validation)
  - `6-10`: Very similar (default - recommended)
  - `11-15`: Similar (lenient)
  - `16+`: Different (likely to fail validation)


## Benefits

### 1. Improved Reliability
- Detect UI changes before execution fails
- Reduce cache invalidation due to false negatives
- Provide early warning of UI state mismatches

### 2. Better User Experience
- Agent can make informed decisions about cache validity
- Clear feedback when UI has changed
- Opportunity to adapt instead of failing

### 3. Intelligent Cache Management
- Automatically identify outdated caches
- Track which UI regions are stable vs. volatile
- Optimize cache usage patterns

## Limitations and Considerations

### 1. Performance Impact
- Each validation requires a screenshot + hash computation (~5-10ms)
- May slow down trajectory execution
- Mitigation: Only validate critical steps, not every action

### 2. False Positives
- Minor UI changes (animations, hover states) may trigger validation failures
- Threshold tuning required for different applications
- Mitigation: Adaptive thresholds, ignore transient changes

### 3. False Negatives
- Subtle but critical changes might not be detected
- Text content changes may not affect visual hash significantly
- Mitigation: Combine with other validation methods (OCR, element detection)

### 4. Storage Overhead
- Each validated step adds 8 bytes (visual_hash) + 1 byte (flag)
- A 100-step trajectory adds ~900 bytes
- Mitigation: Acceptable overhead for improved reliability
