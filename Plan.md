# Visual Validation Implementation Plan

Based on codebase exploration, here's a comprehensive plan to implement the visual validation feature for the caching system.

## 🎯 Key Decisions Summary

**Simplified Approach (Based on Requirements):**
1. **No separate visual metadata model** - Store visual hash as `visual_representation: str | None` field directly on `ToolUseBlockParam`
2. **Validation config in metadata** - Store validation settings (`method`, `region_size`, `threshold`) once in cache file's `metadata.visual_validation`
3. **Selective validation** - Only validate `"click"` and `"text_entry"` actions (most UI-sensitive)
4. **Hash only, no screenshots** - Store only visual hashes to keep cache files compact
5. **Model serializer pattern** - Use `model_serializer` on `ToolUseBlockParam` to drop `visual_representation` when serializing for API (via `context={'for_api': True}`)
6. **Region-based validation** - Extract region around action point (configurable size) for focused validation
7. **Screenshot extraction from message history** - Both during recording and validation, extract the most recent screenshot from message history (from previous tool result) to represent the "before" state

**Benefits:**
- ✅ Simple, flat data structure
- ✅ Compact cache files (no screenshot bloat)
- ✅ Backward compatible (all new fields optional)
- ✅ Clear separation between cache fields and API fields
- ✅ Focused validation reduces false positives

---

## 📊 Current State Summary

**What Exists:**
- ✅ Settings infrastructure (`CacheWritingSettings` with `visual_verification_method`, `visual_validation_region_size`, `visual_validation_threshold`)
- ✅ Hook in `CacheExecutor._validate_step_visually()` (placeholder, always returns `True`)
- ✅ Flag `_visual_validation_enabled` in `CacheExecutor` (always `False`)
- ✅ Basic image utilities in `src/askui/utils/image_utils.py`

**What's Missing:**
- ❌ Image hashing implementations (phash, ahash)
- ❌ Visual metadata storage in cache files (hashes, regions)
- ❌ Screenshot capture during recording
- ❌ Hash computation and comparison during execution
- ❌ Integration between recording and validation phases

---

## 🏗️ Architecture & Design Decisions

### 1. **Separation of Concerns**

Following the existing codebase pattern:

```
┌─────────────────────────────────────────────────────────┐
│ Visual Validation Components (Proposed)                 │
└─────────────────────────────────────────────────────────┘

1. Image Hashing Utilities
   Location: src/askui/utils/visual_validation.py (NEW)
   - compute_phash(image, hash_size) -> str
   - compute_ahash(image, hash_size) -> str
   - compute_hamming_distance(hash1, hash2) -> int
   - extract_region(image, region) -> Image
   - find_recent_screenshot(messages, from_index) -> Image | None

2. Data Model Extensions
   Location: src/askui/models/shared/agent_message_param.py (MODIFY)
   - ToolUseBlockParam.visual_representation: str | None
   - Add model_serializer to drop visual_representation for API

   Location: src/askui/models/shared/settings.py (MODIFY)
   - CacheMetadata.visual_validation: dict[str, Any] | None

3. Cache Recording (CacheManager)
   Location: src/askui/utils/caching/cache_manager.py (MODIFY)
   - Capture screenshots after each tool execution
   - Compute visual hashes based on settings
   - Store visual metadata in trajectory

4. Cache Validation (CacheExecutor)
   Location: src/askui/speaker/cache_executor.py (MODIFY)
   - Enable visual validation based on settings
   - Extract current screen region
   - Compute hash and compare with stored hash
   - Use threshold from settings for pass/fail decision
```

### 2. **Data Storage Strategy** ✅ DECIDED

**Decision: Store only visual hashes (compact)**
- Store visual hash as string in `visual_representation` field on each `ToolUseBlockParam`
- Store validation configuration in cache file `metadata.visual_validation` (method, region_size, threshold)
- **No screenshots stored** to avoid bloating cache files
- Pros: Compact, fast validation, minimal storage overhead
- Cons: No visual debugging capability (acceptable tradeoff)

### 3. **Cache File Format Extension**

```python
# Current ToolUseBlockParam
{
    "type": "tool_use",
    "id": "toolu_123",
    "name": "computer",
    "input": {...}
}

# Extended with visual validation (proposed)
{
    "type": "tool_use",
    "id": "toolu_123",
    "name": "computer",
    "input": {...},
    "visual_representation": "1a2b3c4d5e6f..."  # NEW: Visual hash string (or None)
}

# Cache file metadata extension
{
    "metadata": {
        "goal": "...",
        "created_at": "...",
        # ... existing fields ...
        "visual_validation": {  # NEW (optional, only when visual validation enabled)
            "method": "phash",  # or "ahash"
            "region_size": 100,
            "threshold": 10
        }
    },
    "trajectory": [...]  # Steps with visual_representation
}
```

### 4. **Selective Visual Validation** ✅ DECIDED

**Decision: Only validate specific tool actions**
- Visual validation applies ONLY to: `"click"` and `"text_entry"` actions
- Other actions get `visual_representation: null` in the cache file
- Rationale: These are the actions most sensitive to UI changes

### 5. **API Serialization** (NEW REQUIREMENT)

**Challenge:** `visual_representation` field must NOT be sent to the Anthropic API
- It's only for cache storage/validation
- API would reject unknown fields

**Solution: Model Serializer Pattern**
Implement `model_serializer` on `ToolUseBlockParam` to drop fields based on context:

```python
from pydantic import model_serializer

class ToolUseBlockParam(BaseModel):
    type: Literal["tool_use"]
    id: str
    name: str
    input: dict[str, Any]
    cache_control: CacheControlEphemeralParam | None = None
    visual_representation: str | None = None  # NEW: Visual hash for caching

    @model_serializer(mode='wrap', when_used='json-unless-none')
    def _serialize_model(self, serializer, info):
        """Custom serializer to drop fields based on context."""
        data = serializer(self)

        # When serializing for API, drop cache-only fields
        if info.context and info.context.get('for_api'):
            data.pop('visual_representation', None)
            # Can also drop other fields here
            # data.pop('stop_reason', None)
            # data.pop('usage', None)

        return data

# Usage in code:
messages.model_dump(context={'for_api': True})
```

This pattern can also handle excluding `stop_reason` and `usage` fields that are currently excluded manually.

---

## 📝 Implementation Plan

### **Phase 1: Core Utilities** (Foundation)

#### 1.1 Create Image Hashing Utilities
**File:** `src/askui/utils/visual_validation.py` (NEW)

```python
"""Visual validation utilities for cache trajectory verification."""

from PIL import Image
import imagehash
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from askui.models.shared.agent_message_param import MessageParam

def compute_phash(image: Image.Image, hash_size: int = 8) -> str:
    """Compute perceptual hash (pHash) of an image.

    Args:
        image: PIL Image to hash
        hash_size: Size of the hash (default 8 = 8x8 = 64 bits)

    Returns:
        Hexadecimal string representation of the hash
    """

def compute_ahash(image: Image.Image, hash_size: int = 8) -> str:
    """Compute average hash (aHash) of an image.

    Args:
        image: PIL Image to hash
        hash_size: Size of the hash (default 8 = 8x8 = 64 bits)

    Returns:
        Hexadecimal string representation of the hash
    """

def compute_hamming_distance(hash1: str, hash2: str) -> int:
    """Compute Hamming distance between two hashes.

    Args:
        hash1: First hash (hex string)
        hash2: Second hash (hex string)

    Returns:
        Number of differing bits (0 = identical)
    """

def extract_region(
    image: Image.Image,
    region: dict[str, int] | None
) -> Image.Image:
    """Extract a region from an image for focused validation.

    Args:
        image: Source image
        region: Dictionary with x, y, width, height keys

    Returns:
        Cropped image or original if region is None
    """

def find_recent_screenshot(
    messages: list["MessageParam"],
    from_index: int | None = None
) -> Image.Image | None:
    """Extract most recent screenshot from message history.

    Looks backwards through message history for the most recent tool result
    containing an image block (screenshot). This is used during both recording
    and validation to extract the "before" state screenshot.

    Args:
        messages: Message history to search through
        from_index: Optional index to start searching backwards from.
                   If None, starts from end of list.

    Returns:
        PIL Image from most recent screenshot, or None if not found

    Usage:
        # During recording - find screenshot before tool use at index i
        screenshot = find_recent_screenshot(trajectory, from_index=i)

        # During validation - find most recent screenshot
        screenshot = find_recent_screenshot(message_history)
    """
    start_idx = from_index if from_index is not None else len(messages) - 1

    # Look backwards from start index
    for i in range(start_idx, -1, -1):
        message = messages[i]
        if message.role != "user":
            continue

        # Check if message content is a list of blocks
        if isinstance(message.content, str):
            continue

        # Look for tool result blocks with images
        for block in message.content:
            if block.type == "tool_result":
                # Check for image blocks within tool result
                if isinstance(block.content, list):
                    for content_item in block.content:
                        if content_item.type == "image":
                            # Found screenshot - decode and return
                            from askui.utils.image_utils import ImageSource
                            return ImageSource.from_base64(
                                content_item.source.data
                            ).to_pil_image()

    return None
```

**Dependencies:** Add `imagehash>=4.3.1` to `pyproject.toml`

---

#### 1.2 Extend Data Models
**File:** `src/askui/models/shared/settings.py` (MODIFY)

Add visual validation metadata to cache file metadata:

```python
class CacheMetadata(BaseModel):
    """Metadata for a cached trajectory."""

    goal: str
    created_at: str
    # ... existing fields ...
    visual_validation: dict[str, Any] | None = None  # NEW: {"method": "phash", "region_size": 100, "threshold": 10}
```

**File:** `src/askui/models/shared/agent_message_param.py` (MODIFY)

Update `ToolUseBlockParam` to include visual representation and add model serializer:

```python
from pydantic import model_serializer

class ToolUseBlockParam(BaseModel):
    type: Literal["tool_use"]
    id: str
    name: str
    input: dict[str, Any]
    cache_control: CacheControlEphemeralParam | None = None
    visual_representation: str | None = None  # NEW: Visual hash (hex string)

    @model_serializer(mode='wrap', when_used='json-unless-none')
    def _serialize_model(self, serializer, info):
        """Custom serializer to drop fields based on context.

        When serializing for API (context={'for_api': True}), removes:
        - visual_representation: Cache-only field not accepted by API
        - stop_reason: Internal field (if applicable)
        - usage: Internal field (if applicable)
        """
        data = serializer(self)

        # When serializing for API, drop cache-only and internal fields
        if info.context and info.context.get('for_api'):
            data.pop('visual_representation', None)
            # Note: stop_reason and usage are on MessageParam, not ToolUseBlockParam
            # But this pattern can be reused there

        return data
```

**Important:** Need to also add similar serializer to `MessageParam` to handle `stop_reason` and `usage` fields.

---

### **Phase 2: Recording Phase** (Capture Visual State)

#### 2.1 Capture Screenshots During Recording
**File:** `src/askui/utils/caching/cache_manager.py` (MODIFY)

In `finish_recording()` method:
1. When `writing_settings.visual_verification_method != "none"`
2. Add visual validation metadata to cache file metadata
3. For each tool use block, determine if it needs visual validation (only "click" and "text_entry")
4. Extract most recent screenshot BEFORE the tool use from message history
5. Compute hash from extracted region and store in `visual_representation` field (or None for non-validated actions)

```python
def finish_recording(
    self,
    messages: list[MessageParam],
) -> None:
    """Extract tool blocks from message history and write cache file.

    Args:
        messages: Complete message history from conversation
    """

    # Extract tool blocks as before
    tool_blocks = self._extract_from_messages(messages)

    # NEW: Add visual validation if enabled
    if self._writing_settings and self._writing_settings.visual_verification_method != "none":
        self._add_visual_validation(messages)

        # Store validation settings in metadata
        self._cache_file_metadata["visual_validation"] = {
            "method": self._writing_settings.visual_verification_method,
            "region_size": self._writing_settings.visual_validation_region_size,
            "threshold": self._writing_settings.visual_validation_threshold,
        }

    # Continue with existing logic (parameterization, writing, etc.)...
```

Add new method:

```python
# Actions that should have visual validation
VISUAL_VALIDATION_ACTIONS = {"click", "text_entry"}

def _add_visual_validation(
    self,
    tool_blocks: list[ToolUseBlockParam],
    messages: list[MessageParam],
) -> list[ToolUseBlockParam]:
    """Add visual representation hashes to tool blocks.

    Only adds hashes for actions in VISUAL_VALIDATION_ACTIONS (click, text_entry).
    Other actions get visual_representation=None.

    For each validated tool block:
    1. Check if action is in VISUAL_VALIDATION_ACTIONS
    2. Find most recent screenshot BEFORE this tool use (from previous tool result)
    3. Extract region around action point based on visual_validation_region_size
    4. Compute hash using specified method (phash/ahash)
    5. Store hash string in visual_representation field

    Args:
        trajectory: Complete message history with tool uses and results

    Returns:
        Nothing - modifies tool blocks in place by setting visual_representation
    """
    # Implementation:
    # - Iterate through assistant messages containing tool use blocks
    # - For each validated action (click/text_entry):
    #   - Find most recent screenshot BEFORE this tool use
    #   - Extract region around action coordinate
    #   - Compute hash from region
    #   - Store hash in tool block's visual_representation field
    # - Non-validated actions get visual_representation = None
```

**Implementation Details:**

In the `_add_visual_validation()` method, use the shared `find_recent_screenshot()` utility:

```python
from askui.utils.visual_validation import find_recent_screenshot

def _add_visual_validation(self, trajectory: list[MessageParam]) -> None:
    """Add visual validation hashes to tool use blocks in trajectory."""

    for i, message in enumerate(trajectory):
        if message.role != "assistant":
            continue

        if isinstance(message.content, str):
            continue

        for block in message.content:
            if block.type == "tool_use" and block.name == "computer":
                action = block.input.get("action")

                if action in {"click", "text_entry"}:
                    # Find most recent screenshot BEFORE this tool use
                    screenshot = find_recent_screenshot(trajectory, from_index=i-1)

                    if screenshot:
                        # Extract region and compute hash
                        region = self._extract_action_region(
                            screenshot,
                            block.input,
                            self._visual_validation_region_size
                        )
                        visual_hash = self._compute_visual_hash(
                            region,
                            self._visual_verification_method
                        )
                        block.visual_representation = visual_hash
                    else:
                        logger.warning(f"No screenshot found before step {i}")
                        block.visual_representation = None
                else:
                    # Non-validated actions
                    block.visual_representation = None
```

**Key Considerations:**
- Screenshots are available in tool result messages (user messages containing images)
- Extract screenshot BEFORE each tool use block to represent "before" state
- Region extraction: center region around action point (coordinate for clicks)
- Only "click" and "text_entry" actions are validated

---

### **Phase 3: Validation Phase** (Compare Visual State)

#### 3.1 Enable Visual Validation in CacheExecutor
**File:** `src/askui/speaker/cache_executor.py` (MODIFY)

In `activate_cache_execution()`:

```python
def activate_cache_execution(
    self,
    cache_file: CacheFile,
    cache_file_path: str,
    toolbox: ToolCollection,
    parameter_values: dict[str, str],
    start_from_step_index: int = 0,
    execution_settings: CacheExecutionSettings | None = None,  # NEW
) -> None:
    """Activate cache execution mode with execution settings.

    Args:
        cache_file: The cache file to execute
        cache_file_path: Path to the cache file
        toolbox: Tool collection for executing cached actions
        parameter_values: Values for cache parameters
        start_from_step_index: Step to start from (for resuming)
        execution_settings: Settings for execution including visual validation threshold
    """

    # Store execution settings
    self._execution_settings = execution_settings

    # Enable visual validation if cache file has visual_validation metadata
    # and any steps have visual_representation hashes
    self._visual_validation_enabled = (
        cache_file.metadata.visual_validation is not None
        and any(step.visual_representation is not None for step in cache_file.trajectory)
    )

    # Store validation settings from cache file metadata
    if self._visual_validation_enabled:
        self._visual_validation_config = cache_file.metadata.visual_validation
```

#### 3.2 Implement Visual Validation Logic
**File:** `src/askui/speaker/cache_executor.py` (MODIFY)

Replace placeholder in `_validate_step_visually()`:

```python
def _validate_step_visually(
    self,
    step: ToolUseBlockParam,
    current_screenshot: Image.Image | None = None
) -> tuple[bool, str | None]:
    """Validate cached step against current visual state.

    Compares the stored visual hash with the current screen state
    to detect UI changes that might break cached trajectory.

    Args:
        step: Tool use block with optional visual_representation hash
        current_screenshot: Current screen capture

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if validation passes or is skipped
        - error_message: Description of validation failure (if any)
    """
    # If no visual representation hash, skip validation
    if not step.visual_representation:
        return True, None

    # If no screenshot provided, can't validate
    if current_screenshot is None:
        return True, None  # Skip validation if screenshot unavailable

    # Get validation config from cache metadata
    hash_method = self._visual_validation_config["method"]
    region_size = self._visual_validation_config["region_size"]
    stored_hash = step.visual_representation

    # Extract region around action point
    region_screenshot = self._extract_action_region(
        current_screenshot,
        step.input,
        region_size
    )

    # Compute current hash
    if hash_method == "phash":
        current_hash = compute_phash(region_screenshot)
    elif hash_method == "ahash":
        current_hash = compute_ahash(region_screenshot)
    else:
        return True, None

    # Compare hashes
    distance = compute_hamming_distance(stored_hash, current_hash)

    # Get threshold from execution settings or cache metadata
    threshold = (
        self._execution_settings.visual_validation_threshold
        if self._execution_settings and hasattr(self._execution_settings, 'visual_validation_threshold')
        else self._visual_validation_config["threshold"]  # Default from cache metadata
    )

    # Validate
    if distance <= threshold:
        return True, None
    else:
        return False, f"Visual validation failed: hash distance {distance} > threshold {threshold}"

def _extract_action_region(
    self,
    screenshot: Image.Image,
    action_input: dict[str, Any],
    region_size: int,
) -> Image.Image:
    """Extract region around action point for validation.

    Args:
        screenshot: Full screenshot
        action_input: Tool input containing action details (coordinate, text, etc.)
        region_size: Size of region to extract (width and height)

    Returns:
        Cropped image centered on action point, or full image if no coordinate
    """
    # For click actions with coordinates
    if "coordinate" in action_input:
        x, y = action_input["coordinate"]
        half_size = region_size // 2
        return screenshot.crop((
            max(0, x - half_size),
            max(0, y - half_size),
            min(screenshot.width, x + half_size),
            min(screenshot.height, y + half_size),
        ))

    # For other actions (text_entry), use full screen
    # TODO: Could extract focus region if detectable
    return screenshot
```

#### 3.3 Extract Screenshot from Message History
**File:** `src/askui/speaker/cache_executor.py` (MODIFY)

Update `_execute_next_step()` to use the shared `find_recent_screenshot()` utility:

```python
from askui.utils.visual_validation import find_recent_screenshot

# NEW: Extract screenshot for visual validation
current_screenshot = None
if self._visual_validation_enabled and step.visual_representation:
    current_screenshot = find_recent_screenshot(self._message_history)

# Validate step visually
is_valid, error_msg = self._validate_step_visually(step, current_screenshot)
if not is_valid:
    # Visual validation failed - hand execution back to agent
    # Add informative message about validation failure
    validation_failure_msg = MessageParam(
        role="user",
        content=f"⚠️ Visual validation failed at step {self._current_step_index}: {error_msg}. "
                f"The UI appears to have changed since this trajectory was recorded. "
                f"Please continue manually from this point.",
    )
    self._message_history.append(validation_failure_msg)

    # Switch to askui_agent speaker to handle the situation
    return SpeakerResult(
        status="switch_speaker",
        next_speaker="askui_agent",
        message_history=self._message_history,
    )
```

---

### **Phase 4: Configuration & Settings**

#### 4.1 Update CacheExecutionSettings
**File:** `src/askui/models/shared/settings.py` (MODIFY)

```python
class CacheExecutionSettings(BaseModel):
    """Settings for executing/replaying cache files."""

    delay_time_between_action: float = 0.5
    visual_validation_threshold: int = 10  # NEW: Override threshold during execution
    skip_visual_validation: bool = False  # NEW: Allow disabling validation at runtime
```

#### 4.2 Pass Execution Settings Through
**File:** `src/askui/tools/caching_tools.py` (MODIFY)

Update `ExecuteCachedTrajectory` tool to accept and pass execution settings:

```python
class ExecuteCachedTrajectory(Tool):
    def __call__(
        self,
        trajectory_file: str,
        parameter_values: dict[str, str] | None = None,
        start_from_step_index: int = 0,
        visual_validation_threshold: int | None = None,  # NEW
    ) -> str:
        """Execute a cached trajectory with optional visual validation override."""

        # Build execution settings
        execution_settings = CacheExecutionSettings(
            delay_time_between_action=self._execution_settings.delay_time_between_action,
            visual_validation_threshold=visual_validation_threshold or self._execution_settings.visual_validation_threshold,
        )

        # Pass to cache executor
        self._cache_executor.activate_cache_execution(
            # ...
            execution_settings=execution_settings,
        )
```

---

### **Phase 5: Testing & Examples**

#### 5.1 Unit Tests

**File:** `tests/unit/utils/test_visual_validation.py` (NEW)
```python
"""Tests for visual validation utilities."""

def test_compute_phash():
    """Test pHash computation produces consistent results."""

def test_compute_ahash():
    """Test aHash computation produces consistent results."""

def test_hamming_distance():
    """Test Hamming distance calculation."""

def test_extract_region():
    """Test image region extraction."""

def test_identical_images_zero_distance():
    """Test that identical images have zero Hamming distance."""

def test_different_images_nonzero_distance():
    """Test that different images have non-zero Hamming distance."""
```

**File:** `tests/unit/caching/test_cache_manager_visual.py` (NEW)
```python
"""Tests for cache manager with visual validation."""

def test_record_with_visual_validation_phash():
    """Test recording cache with phash validation."""

def test_record_with_visual_validation_ahash():
    """Test recording cache with ahash validation."""

def test_record_without_visual_validation():
    """Test that visual_verification_method='none' doesn't add validation data."""

def test_visual_validation_stores_hash():
    """Test that visual hashes are stored in trajectory."""

def test_visual_validation_metadata():
    """Test that validation config is stored in cache metadata."""

def test_selective_validation_click_only():
    """Test that only click actions get visual_representation."""

def test_selective_validation_text_entry_only():
    """Test that only text_entry actions get visual_representation."""
```

**File:** `tests/unit/caching/test_cache_executor_visual.py` (NEW)
```python
"""Tests for cache executor with visual validation."""

def test_execute_with_visual_validation_success():
    """Test successful execution with matching visual state."""

def test_execute_with_visual_validation_failure_switches_to_agent():
    """Test that validation failure switches to askui_agent speaker (no crash)."""

def test_visual_validation_failure_message_in_history():
    """Test that validation failure adds informative message to history."""

def test_agent_continues_after_visual_validation_failure():
    """Test that agent can continue and complete goal after validation failure."""

def test_visual_validation_threshold():
    """Test that threshold controls validation sensitivity."""

def test_skip_visual_validation():
    """Test that skip_visual_validation setting works."""
```

#### 5.2 Integration Tests

**File:** `tests/integration/test_visual_validation_e2e.py` (NEW)
```python
"""End-to-end tests for visual validation."""

def test_record_and_replay_with_visual_validation():
    """Test full cycle: record with visual validation, then replay successfully."""

def test_detect_ui_changes():
    """Test that UI changes are detected during replay."""

def test_visual_validation_with_cache_parameters():
    """Test visual validation works alongside cache parameters."""

def test_model_serializer_drops_visual_representation():
    """Test that model_dump(context={'for_api': True}) drops visual_representation."""
```

#### 5.3 Update Examples

**File:** `examples/caching_demo_with_visual_validation.py` (NEW)

```python
"""Example demonstrating visual validation in cache trajectories."""

from askui import VisionAgent
from askui.models.shared.settings import (
    CachingSettings,
    CacheWritingSettings,
    CacheExecutionSettings,
)

def main():
    # Record with visual validation
    print("Recording trajectory with visual validation...")
    with VisionAgent() as agent:
        agent.act(
            "Open Chrome and navigate to www.example.com",
            caching_settings=CachingSettings(
                strategy="record",
                cache_dir=".askui_cache",
                writing_settings=CacheWritingSettings(
                    filename="visual_demo.json",
                    visual_verification_method="phash",  # Enable visual validation
                    visual_validation_region_size=100,
                    visual_validation_threshold=10,
                ),
            ),
        )

    # Replay with visual validation
    print("Replaying trajectory with visual validation...")
    with VisionAgent() as agent:
        agent.act(
            "Open Chrome and navigate to www.example.com. Use cached trajectory if available.",
            caching_settings=CachingSettings(
                strategy="execute",
                cache_dir=".askui_cache",
                execution_settings=CacheExecutionSettings(
                    delay_time_between_action=0.5,
                    visual_validation_threshold=10,
                ),
            ),
        )

if __name__ == "__main__":
    main()
```

---

## 🔄 Implementation Order

1. **Phase 1**: Create utilities and extend data models (1-2 days)
   - Implement image hashing functions and screenshot extraction utility
   - Add visual_representation to ToolUseBlockParam and visual_validation to CacheMetadata
   - Add model_serializer for API serialization
   - Write unit tests for utilities

2. **Phase 2**: Implement recording with visual capture (2-3 days)
   - Modify CacheManager.finish_recording()
   - Implement _add_visual_validation()
   - Extract screenshots from message history
   - Write unit tests for recording

3. **Phase 3**: Implement validation logic (2-3 days)
   - Update CacheExecutor.activate_cache_execution()
   - Implement _validate_step_visually()
   - Handle screenshot capture during execution
   - Write unit tests for validation

4. **Phase 4**: Configuration updates (1 day)
   - Extend CacheExecutionSettings
   - Update caching tools
   - Update documentation

5. **Phase 5**: Testing and examples (2-3 days)
   - Write integration tests
   - Create example scripts
   - Test end-to-end workflows

**Total estimated effort: 8-12 days**

---

## ⚠️ Design Questions & Decisions

### 1. **Screenshot Storage** ✅ DECIDED
**Decision:** Store only visual hashes (compact), no screenshots

**Rationale:**
- Keeps cache files small and fast to load
- Hash validation is sufficient for detecting UI changes
- Acceptable tradeoff vs. debugging capability

---

### 2. **Validation on All Steps** ✅ DECIDED
**Decision:** Only validate specific actions - `"click"` and `"text_entry"`

**Rationale:**
- These actions are most sensitive to UI changes
- Other actions (screenshot, wait, etc.) don't need visual validation
- Steps without validation get `visual_representation: null`

---

### 3. **Validation Failure Handling** ✅ DECIDED
**Decision:** Hand execution back to Agent (fail-fast = stop cache execution, let agent continue)

**Implementation:**
- Visual validation failure → Return `SpeakerResult(status="switch_speaker", next_speaker="askui_agent")`
- Cache executor stops executing the cached trajectory
- AskUIAgent speaker takes over and continues with the goal
- Agent can see the validation failure in message history and adapt
- Override: `CacheExecutionSettings.skip_visual_validation = True` to disable validation entirely

**Rationale:**
- Visual validation failure means UI has changed since recording
- Cached trajectory can't be trusted → let agent figure out what to do
- Similar to non-cacheable tool handling (pause cache, switch to agent)
- Agent can recover, adapt to UI changes, and complete the goal
- No crash, graceful handoff of control

---

### 4. **Region Detection** ✅ DECIDED
**Decision:** Automatic region around action point

**Implementation:**
- For `click`: Extract region centered on coordinate (configurable size via `visual_validation_region_size`)
- For `text_entry`: Use full screen (TODO: Could detect focus region if possible)
- Region size configurable via `CacheWritingSettings.visual_validation_region_size` (default: 100px)

**Rationale:**
- Focused validation reduces false positives from unrelated UI changes
- Simpler than full UI element detection
- Can be enhanced later with intelligent boundary detection

---

### 5. **Hash Size** ✅ DECIDED
**Decision:** Fixed 8x8 (64 bits) - standard

**Rationale:**
- Standard size for perceptual hashing
- Good balance of accuracy and performance
- Can be made configurable later if needed

---

### 6. **Screenshot Access** ✅ DECIDED
**Decision:** Extract most recent screenshot from message history

**Approach:**
- During **RECORDING**: Extract screenshot from message history BEFORE each validated action
- During **VALIDATION**: Extract screenshot from message history BEFORE executing cached action
- Compares "before" states: UI state before original action vs. UI state before replaying action

**Rationale:**
- After each tool execution, screenshot appears in tool result message (user message)
- Most recent screenshot represents the current state
- Simple and avoids need to execute computer tool directly
- Provides accurate comparison: both hashes represent pre-action states

**Flow Example:**
```
1. Tool result (step N-1) → screenshot A in message history
2. Tool use (step N) → extract screenshot A, compute hash, execute
3. Tool result (step N) → screenshot B in message history
4. Tool use (step N+1) → extract screenshot B, compute hash, execute
```

**Acceptable Inaccuracy:**
- If UI changes between last screenshot and current action (rare edge case)
- Trade-off: simplicity vs. perfect accuracy (acceptable for v1)

---

### 7. **Missing Screenshot Handling** ✅ DECIDED
**Decision:** Skip validation silently (return True)

**Rationale:**
- Backward compatibility - old code may not provide screenshots
- Graceful degradation - validation is enhancement, not requirement
- Avoids breaking existing functionality

---

### 8. **Cache File Backward Compatibility** ✅ DECIDED
**Decision:** Full backward compatibility maintained

**Implementation:**
- `visual_representation` field is optional (defaults to None)
- `metadata.visual_validation` is optional
- Old cache files without these fields work exactly as before
- No breaking changes to existing cache files

---

### 9. **Data Model Structure** ✅ DECIDED
**Decision:** Simplified structure

**Implementation:**
- `ToolUseBlockParam.visual_representation`: str | None (visual hash)
- `CacheMetadata.visual_validation`: dict | None (validation config)
- No separate VisualValidationData model

**Rationale:**
- Simpler implementation
- Less nesting in cache files
- Validation config stored once in metadata vs. per-step

---

### 10. **API Serialization** ✅ DECIDED
**Decision:** Use `model_serializer` with context pattern

**Implementation:**
- Add `@model_serializer` to `ToolUseBlockParam`
- Use `messages.model_dump(context={'for_api': True})` when sending to API
- Drops `visual_representation` (and potentially `stop_reason`, `usage`) for API calls

**Rationale:**
- Clean separation of cache fields vs. API fields
- Centralized serialization logic
- Can extend to other models (MessageParam) for consistency

---

## 📦 Dependencies

**New dependencies needed:**

```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "imagehash>=4.3.1",  # For phash/ahash computation
]
```

**Dependency details:**
- `imagehash` is a pure Python library
- Built on top of PIL/Pillow (already in dependencies)
- Provides pHash, aHash, dHash, wHash implementations
- Well-maintained, stable API

---

## 🎯 Success Criteria

**Must Have:**
- [ ] Can record cache with visual hashes (phash and ahash)
- [ ] Can replay cache with visual validation
- [ ] Validation detects UI changes (different hash triggers handoff to agent)
- [ ] Validation passes when UI is same (similar hash within threshold)
- [ ] Validation failure switches to askui_agent speaker (no crash)
- [ ] Agent can continue after validation failure and complete goal
- [ ] Threshold controls sensitivity appropriately
- [ ] Old cache files without visual validation still work
- [ ] Unit tests cover all new utilities
- [ ] Integration tests verify end-to-end flow

**Should Have:**
- [ ] Region-based validation works (extract region around action point)
- [ ] Only click and text_entry actions are validated
- [ ] Clear error messages on validation failure (with hash distance)
- [ ] Documentation updated with examples
- [ ] Performance impact is minimal (hashing is fast)
- [ ] model_serializer correctly drops visual_representation for API calls

**Nice to Have:**
- [ ] Automatic region detection around action points
- [ ] Visual diff reporting (show what changed)
- [ ] Configurable hash size
- [ ] Visual validation statistics in cache metadata

---

## 📊 Performance Considerations

**Image Hashing Performance:**
- pHash computation: ~10-20ms per image
- aHash computation: ~5-10ms per image
- Hamming distance: <1ms
- Total overhead per step: ~10-20ms (negligible for UI automation)

**Storage Impact:**
- Hash size: 16 characters (64 bits as hex string)
- Region metadata: ~50 bytes
- Total per step: ~100 bytes (without screenshot)
- With screenshot (debug mode): ~100-500KB per step

**Recommendation:** Visual validation adds minimal performance overhead and storage cost (without debug mode).

---

## 🔧 Implementation Notes

### Region Extraction Strategy

For automatic region extraction around action points:

```python
def extract_action_region(
    screenshot: Image.Image,
    action_input: dict[str, Any],
    region_size: int,
) -> Image.Image:
    """Extract region around action point for validation.

    Args:
        screenshot: Full screenshot
        action_input: Tool input containing action details
        region_size: Size of region to extract (width and height)

    Returns:
        Cropped image centered on action point, or full image if no coordinate
    """
    # For click actions with coordinates
    if "coordinate" in action_input:
        x, y = action_input["coordinate"]
        half_size = region_size // 2
        return screenshot.crop((
            max(0, x - half_size),
            max(0, y - half_size),
            min(screenshot.width, x + half_size),
            min(screenshot.height, y + half_size),
        ))

    # For text_entry and other actions, use full screen
    return screenshot
```

### Action Type Detection

Determine which actions need visual validation:

```python
VISUAL_VALIDATION_ACTIONS = {"click", "text_entry"}

def should_validate_action(tool_input: dict[str, Any]) -> bool:
    """Check if this tool action should have visual validation.

    Args:
        tool_input: Tool input dictionary containing 'action' field

    Returns:
        True if action is in VISUAL_VALIDATION_ACTIONS
    """
    action = tool_input.get("action")
    return action in VISUAL_VALIDATION_ACTIONS
```

### Error Handling

Visual validation should be resilient to errors:

```python
try:
    is_valid, error_msg = self._validate_step_visually(step, screenshot)
except Exception as e:
    # Log error but don't fail execution
    logger.warning(f"Visual validation error: {e}")
    is_valid, error_msg = True, None  # Continue execution
```

### API Serialization Usage

When sending messages to API, use context to drop cache-only fields:

```python
# Before sending to Anthropic API
api_messages = [
    msg.model_dump(mode='json', context={'for_api': True})
    for msg in messages
]

# This will automatically drop:
# - visual_representation from ToolUseBlockParam
# - stop_reason and usage from MessageParam (if implemented)
```

### Visual Validation Failure Flow

When visual validation fails, the execution flow is:

```
1. CacheExecutor detects visual validation failure
   ↓
2. CacheExecutor adds informative message to message history
   "⚠️ Visual validation failed at step X: hash distance Y > threshold Z"
   ↓
3. CacheExecutor returns SpeakerResult(status="switch_speaker", next_speaker="askui_agent")
   ↓
4. Conversation switches to AskUIAgent speaker
   ↓
5. AskUIAgent sees the validation failure message and current goal
   ↓
6. AskUIAgent continues execution manually (adapts to UI changes)
   ↓
7. Goal can still be achieved despite UI changes
```

**Key Benefits:**
- No crash - graceful degradation
- Agent can adapt to UI changes
- Similar to non-cacheable tool handling
- Validation failure is transparent to agent (in message history)
- Agent can make intelligent decisions based on what failed

---

## 📚 Related Documentation

**Files to update:**
- `docs/caching.md` - Update visual validation section with actual implementation details
- `README.md` - Mention visual validation as a feature
- `docs/architecture.md` - Document visual validation in cache architecture

**Documentation additions:**
- How to enable visual validation
- How to tune threshold for your application
- Debugging failed validations
- Performance impact and best practices

---

## 🚀 Future Enhancements

**Phase 6 (Future):**
- Visual diff reporting (highlight what changed)
- Automatic threshold calibration
- Multi-region validation (validate multiple areas)
- Structural similarity index (SSIM) as alternative to hashing
- ML-based validation (detect semantic changes vs. cosmetic)
- Visual validation statistics and analytics

---

## ✅ Checklist Before Starting Implementation

- [x] Review and approve design decisions
- [x] Clarify screenshot access mechanism (extract from message history)
- [x] Decide on region extraction strategy (region around coordinate)
- [x] Confirm validation failure handling (hand back to agent)
- [x] Set up development branch (using current branch)
- [x] Install imagehash dependency (already installed)
- [ ] Write failing tests first (TDD)

---

This plan provides a clear roadmap for implementing visual validation while respecting the existing codebase architecture and maintaining backward compatibility.
