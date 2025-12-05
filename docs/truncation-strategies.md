# Truncation Strategies

This guide explains how conversation history management works in AskUI Vision Agent and how to optimize token usage for long-running agents.

## Table of Contents

- [Overview](#overview)
- [Available Strategies](#available-strategies)
  - [SimpleTruncationStrategy (Default)](#simpletruncationstrategy-default)
  - [LatestImageOnlyTruncationStrategy (Experimental)](#latestimageonlytruncationstrategy-experimental)
- [When to Use Each Strategy](#when-to-use-each-strategy)
- [Configuration](#configuration)
- [Cost Implications](#cost-implications)
- [Troubleshooting](#troubleshooting)

## Overview

As vision agents execute tasks, they maintain a conversation history including:
- User instructions
- Assistant responses with reasoning
- Tool calls and results
- Screenshots (consuming 1,000-3,000 tokens each)

Without proper management, long conversations can:
- Exceed the 100,000 token API limit
- Increase API costs significantly
- Slow down response times

Truncation strategies automatically manage conversation history by removing less important messages while preserving critical context.

## Available Strategies

### SimpleTruncationStrategy (Default)

The default strategy that provides stable, reliable truncation.

**How it works:**
- Monitors token count and message count
- When thresholds are exceeded (75% of limits), removes messages in priority order:
  1. Tool calling loops from closed conversations
  2. Entire closed conversation loops (except first and last)
  3. The first conversation loop if not the active one
  4. Tool calling turns from the open loop (except first and last)

**Characteristics:**
- Conservative: Preserves all images until limits approached
- Stable: Well-tested for all use cases
- Higher token cost: All screenshots remain in context

**Usage:**

```python
from askui import VisionAgent

# Default - no configuration needed
with VisionAgent() as agent:
    agent.act("Complete the task")
```

### LatestImageOnlyTruncationStrategy (Experimental)

An experimental strategy that aggressively reduces token usage by keeping only the most recent screenshot.

**How it works:**
- Applies same message truncation as SimpleTruncationStrategy
- **Additionally**: Keeps only the most recent screenshot
- Replaces older images with text: `"[Image removed to save tokens]"`
- Preserves all text, tool calls, and non-image tool results

**Characteristics:**
- Aggressive savings: Up to 90% token reduction in multi-step scenarios
- Experimental: May affect performance when historical visual context is needed
- Cost-effective: Dramatically reduces API costs

**Token savings example:**

| Scenario | SimpleTruncationStrategy | LatestImageOnlyTruncationStrategy | Savings |
|----------|-------------------------|-----------------------------------|---------|
| 10-step task with screenshots | ~25,000 tokens | ~7,100 tokens | 72% |
| 20-step task with screenshots | ~50,000 tokens | ~12,000 tokens | 76% |

**Usage:**

```python
from askui import VisionAgent, ActSettings, TruncationStrategySettings

with VisionAgent() as agent:
    # Configure to use latest image only strategy
    settings = ActSettings(
        truncation=TruncationStrategySettings(strategy="latest_image_only")
    )
    agent.act("Complete the task", settings=settings)
```

**Warning:** On first use, you'll see a warning log:
```
WARNING: Using experimental LatestImageOnlyTruncationStrategy. This strategy removes old images from conversation history to save tokens. Only the most recent image is kept. This may affect model performance in scenarios requiring historical visual context.
```

## When to Use Each Strategy

### Use SimpleTruncationStrategy (Default) when:
- Starting a new project
- Requiring maximum stability
- Visual history is important
- Debugging complex issues
- Running critical production workloads

### Use LatestImageOnlyTruncationStrategy when:
- ✅ Tasks have many sequential actions with screenshots
- ✅ Token costs are a primary concern
- ✅ Only current screen state matters (e.g., form filling, navigation)
- ✅ Long-running agents would exceed token limits

### Avoid LatestImageOnlyTruncationStrategy when:
- ❌ Tasks require comparison between multiple screens
- ❌ Debugging scenarios need full visual history
- ❌ Complex workflows depend on historical visual context
- ❌ Stability is more important than cost

## Configuration

You can easily configure truncation strategies through the `act()` method using settings:

```python
from askui import VisionAgent, ActSettings, TruncationStrategySettings

with VisionAgent() as agent:
    # Use default (simple) strategy
    agent.act("Complete the task")

    # Use experimental latest image only strategy
    settings = ActSettings(
        truncation=TruncationStrategySettings(strategy="latest_image_only")
    )
    agent.act("Complete another task", settings=settings)

    # Mix and match - use simple for some tasks, latest_image_only for others
    simple_settings = ActSettings(
        truncation=TruncationStrategySettings(strategy="simple")
    )
    agent.act("Task requiring full visual history", settings=simple_settings)
```

**Available strategies:**
- `"simple"` (default): Conservative strategy preserving all images
- `"latest_image_only"` (experimental): Aggressive strategy keeping only latest image

**Note:** Advanced configuration options (token limits, thresholds) use default values and cannot be customized through settings. If you need custom thresholds, you can still set the truncation strategy factory directly on the agent during initialization.

## Cost Implications

**Anthropic Claude API Pricing (approximate):**
- Input tokens: ~$3 per million tokens
- Output tokens: ~$15 per million tokens

**Cost comparison for a 20-step task:**

SimpleTruncationStrategy:
```
20 screenshots × 2,000 tokens = 40,000 tokens
Additional context = 10,000 tokens
Total = 50,000 tokens
Cost = $0.15 per execution
```

LatestImageOnlyTruncationStrategy:
```
1 screenshot × 2,000 tokens = 2,000 tokens
Additional context = 10,000 tokens
Total = 12,000 tokens
Cost = $0.036 per execution
Savings = $0.114 per execution (76% reduction)
```

For applications running thousands of executions, these savings are substantial.

## Troubleshooting

### Token limit errors

**Symptom:** `MaxTokensExceededError` or API context length errors

**Solutions:**
1. Lower `input_token_truncation_threshold` for earlier truncation
2. Reduce `max_input_tokens` for more aggressive truncation
3. Try `LatestImageOnlyTruncationStrategy` for dramatic reduction

### Agent loses context during long conversations

**Symptom:** Agent forgets earlier actions or repeats steps

**Solutions:**
1. Increase `input_token_truncation_threshold` to preserve more history
2. Include critical information in system prompts, not just conversation
3. Break long tasks into smaller subtasks

### Performance degrades with LatestImageOnlyTruncationStrategy

**Symptom:** Agent makes mistakes or fails tasks

**Solutions:**
1. Revert to `SimpleTruncationStrategy` for those tasks
2. Restructure tasks to require less historical visual context
3. Add explicit text descriptions of previous screens in tool results

## Best Practices

1. **Start with the default:** Use `SimpleTruncationStrategy` for new projects
2. **Monitor costs:** If token usage is high, test `LatestImageOnlyTruncationStrategy`
3. **Test thoroughly:** Verify agent success rates with the experimental strategy
4. **Use selectively:** Apply `LatestImageOnlyTruncationStrategy` only where appropriate

## See Also

- [Using Models](using-models.md) - Learn about AI models and their capabilities
- [Caching](caching.md) - Speed up repeated tasks with action caching
- [Observability](observability.md) - Monitor and debug agent behavior
