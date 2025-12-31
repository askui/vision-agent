# AskUI Caching Examples

This directory contains example scripts demonstrating the capabilities of the AskUI caching system (v0.2).

## Examples Overview

### 1. `basic_caching_example.py`
**Introduction to cache recording and execution**

Demonstrates:
- ✅ **Record mode**: Save a trajectory to a cache file
- ✅ **Execute mode**: Replay a cached trajectory
- ✅ **Both mode**: Try execute, fall back to record
- ✅ **Cache parameters**: Dynamic value substitution with `{{parameter}}` syntax
- ✅ **AI-based parameter detection**: Automatic identification of dynamic values

**Best for**: Getting started with caching, understanding the basic workflow

### 2. `visual_validation_example.py`
**Visual UI state validation with perceptual hashing**

Demonstrates:
- ✅ **pHash validation**: Perceptual hashing (recommended, robust)
- ✅ **aHash validation**: Average hashing (faster, simpler)
- ✅ **Threshold tuning**: Adjusting strictness (0-64 range)
- ✅ **Region size**: Controlling validation area (50-200 pixels)
- ✅ **Disabling validation**: When to skip visual validation

**Best for**: Understanding visual validation, tuning validation parameters for your use case

## Quick Start

1. **Install dependencies**:
   ```bash
   pdm install
   ```

2. **Run an example**:
   ```bash
   pdm run python examples/basic_caching_example.py
   ```

3. **Explore the cache files**:
   ```bash
   cat .askui_cache/basic_example.json
   ```

## Understanding the Examples

### Basic Workflow

```python
# 1. Record a trajectory
caching_settings = CachingSettings(
    strategy="record",  # Save to cache
    cache_dir=".askui_cache",
    writing_settings=CacheWritingSettings(
        filename="my_cache.json",
        visual_verification_method="phash",
    ),
)

# 2. Execute from cache
caching_settings = CachingSettings(
    strategy="execute",  # Replay from cache
    cache_dir=".askui_cache",
    execution_settings=CacheExecutionSettings(
        delay_time_between_action=0.5,
    ),
)

# 3. Both (recommended for development)
caching_settings = CachingSettings(
    strategy="both",  # Try execute, fall back to record
    cache_dir=".askui_cache",
    writing_settings=CacheWritingSettings(filename="my_cache.json"),
    execution_settings=CacheExecutionSettings(),
)
```

### Visual Validation Settings

```python
writing_settings=CacheWritingSettings(
    visual_verification_method="phash",  # or "ahash" or "none"
    visual_validation_region_size=100,   # 100x100 pixel region
    visual_validation_threshold=10,      # Hamming distance (0-64)
)
```

**Threshold Guidelines**:
- `0-5`: Very strict (detects tiny changes)
- `6-10`: Strict (recommended for stable UIs) ✅
- `11-15`: Moderate (tolerates minor changes)
- `16+`: Lenient (may miss significant changes)

**Region Size Guidelines**:
- `50`: Small, precise validation
- `100`: Balanced (recommended default) ✅
- `150-200`: Large, more context

## Customizing Examples

Each example can be customized by modifying:

1. **The goal**: Change the task description
2. **Cache settings**: Adjust validation parameters
3. **Tools**: Add custom tools to the agent
4. **Model**: Change the AI model (e.g., `model="askui/claude-sonnet-4-5-20250929"`)

## Cache File Structure (v0.2)

```json
{
  "metadata": {
    "version": "0.1",
    "created_at": "2025-01-15T10:30:00Z",
    "goal": "Task description",
    "visual_verification_method": "phash",
    "visual_validation_region_size": 100,
    "visual_validation_threshold": 10
  },
  "trajectory": [
    {
      "type": "tool_use",
      "name": "computer",
      "input": {"action": "left_click", "coordinate": [450, 320]},
      "visual_representation": "80c0e3f3e3e7e381..."  // pHash/aHash
    }
  ],
  "cache_parameters": {
    "search_term": "Description of the parameter"
  }
}
```

## Tips and Best Practices

### When to Use Caching

✅ **Good use cases**:
- Repetitive UI automation tasks
- Testing workflows that require setup
- Demos and presentations
- Regression testing of UI workflows

❌ **Not recommended**:
- Highly dynamic UIs that change frequently
- Tasks requiring real-time decision making
- One-off tasks that won't be repeated

### Choosing Validation Settings

**For stable UIs** (e.g., desktop applications):
- Method: `phash`
- Threshold: `5-10`
- Region: `100`

**For dynamic UIs** (e.g., websites with ads):
- Method: `phash`
- Threshold: `15-20`
- Region: `150`

**For maximum performance** (trusted cache):
- Method: `none`
- (Visual validation disabled)

### Debugging Cache Execution

If cache execution fails:

1. **Check visual validation**: Lower threshold or disable temporarily
2. **Verify UI state**: Ensure UI hasn't changed since recording
3. **Check cache file**: Look for `visual_representation` fields
4. **Review logs**: Look for "Visual validation failed" messages
5. **Re-record**: Delete cache file and record fresh trajectory

## Additional Resources

- **Documentation**: See `docs/caching.md` for complete documentation
- **Visual Validation**: See `docs/visual_validation.md` for technical details
- **Playground**: See `playground/caching_demo.py` for more examples

## Questions?

For issues or questions, please refer to the main documentation or open an issue in the repository.
