# Token Management Strategy

This document explains token optimization strategies used in the AI trading workflow.

## Overview

The 4-stage workflow (candidate generation, edge scoring, winner selection, charter generation) can generate 52-57k tokens with proper management, or exceed 200k+ tokens without optimization. Two key strategies manage token usage:

1. **Adaptive History Limiting** - Controls conversation length
2. **Tool Result Compression** - Reduces large API responses (FRED, yfinance)

---

## Strategy 1: Adaptive History Limiting

### What It Does

Keeps only the most recent N messages in agent conversation history, preventing unbounded memory growth during multi-turn interactions.

### Implementation

**Location:** `src/agent/strategy_creator.py:86-125`

```python
def adaptive_history_processor(ctx: RunContext, messages: list) -> list:
    """
    Keep ~20 messages on average, rely on tool result compression
    to manage token count rather than aggressive message trimming.
    """
    max_messages = 20

    if len(messages) <= max_messages:
        return messages

    # Keep only most recent messages
    result = messages[-max_messages:]

    # Ensure we end with ModelRequest (pydantic-ai requirement)
    if result and not isinstance(result[-1], _messages.ModelRequest):
        result.append(_messages.ModelRequest(parts=[]))

    return result
```

### Current Settings Per Stage

| Stage | Max Messages | Reasoning |
|-------|-------------|-----------|
| Candidate Generation | 20 | May make multiple tool calls during generation |
| Edge Scoring | 20 | Single evaluation per candidate (5 parallel) |
| Winner Selection | 20 | Composite ranking + reasoning generation |
| Charter Generation | 20 | May use tools for fresh market data |

### Why 20 Messages?

Increased from 10 → 20 because:
- Tool result compression reduces each result by ~97% (1578 → 50 tokens)
- Agent was looping due to forgetting previous search attempts
- With compression, 20 messages ≈ same tokens as 10 uncompressed messages

### Configuration

History limiting is **always enabled** (not configurable) to prevent infinite loops and token overflow.

---

## Strategy 2: Tool Result Compression

### What It Does

Intercepts large MCP tool responses (FRED time series, yfinance price data) and compresses them using an LLM summarizer before adding to conversation history.

**Example:**
```
Before: {"observations": [{"date": "2020-01", "value": 1.5}, ...]} (2000+ tokens)
After:  {"latest_value": 5.33, "trend": "increasing", "date": "2025-10"} (30 tokens)
```

**Compression ratio:** ~97% (1578 → 50 tokens)

### Implementation

**Location:** `src/agent/mcp_config.py:49-156`

```python
async def compress_tool_result(
    ctx: RunContext[Any],
    call_tool_func,
    name: str,
    args: dict[str, Any]
) -> Any:
    """Compress large tool results before they're added to conversation history."""

    # Only compress data-heavy tools
    data_heavy_tools = [
        'fred_get_series',  # Returns long time series
        'fred_search',      # Returns many search results with descriptions
        'stock_get_historical_stock_prices',  # Returns price history
    ]

    if name not in data_heavy_tools:
        return result  # No compression

    # Check result size (compress if > 200 chars)
    if len(result_str) < 200:
        return result  # Too small to bother

    # Use LLM summarizer to extract essential info
    summary_data = await summarizer.summarize(name, result)

    # Hard cap: Never exceed 600 chars (~150 tokens)
    return truncate_if_needed(summary_data['summary'])
```

### Which Tools Are Compressed?

**Compressed (data-heavy):**
- ✅ `fred_get_series` - Returns 100+ time series observations
- ✅ `fred_search` - Returns many search results with descriptions
- ✅ `stock_get_historical_stock_prices` - Returns daily price history

**Not compressed (already concise):**
- ❌ `fred_browse` - Returns category metadata (small)
- ❌ `stock_get_stock_info` - Returns single company summary
- ❌ `composer_*` - Strategy data already structured and compact

### Configuration

**Environment Variables:**
```bash
# Enable/disable compression (default: true)
COMPRESS_MCP_RESULTS=true

# LLM model for summarization (default: openai:gpt-5-mini)
SUMMARIZATION_MODEL=openai:gpt-5-mini
```

**Current Policy (Post-Refactor):**

Compression is **documented but disabled by default** in most stages:
- **Candidate Generation:** Compression available but not critical (context pack provides most data)
- **Edge Scoring:** No tool usage (no compression needed)
- **Winner Selection:** No tool usage (no compression needed)
- **Charter Generation:** May use tools; compression disabled by default (let AI see full context)

**Why disable by default?**
- Phase 1 elimination reduced tool usage by ~90%
- Context pack provides pre-analyzed data (no redundant FRED/yfinance calls)
- Compression adds complexity and potential information loss
- Enable only when proven necessary (token overflow in production)

### How to Enable Compression Per Stage

If a stage experiences token overflow, enable compression:

```python
# In stage class (e.g., charter_generator.py)
import os

# Override compression setting for this stage
os.environ["COMPRESS_MCP_RESULTS"] = "true"

# Create agent (compression active)
agent_ctx = await create_agent(...)
```

---

## Token Budget Per Stage (Estimated)

**With optimizations (context pack + single-phase + disabled compression):**

| Stage | Tokens | Details |
|-------|--------|---------|
| 1. Candidate Generation | 12-15k | Context pack provided; tools optional |
| 2. Edge Scoring (×5) | 15k | 3k per candidate × 5 (parallel) |
| 3. Winner Selection | 5k | Composite ranking + reasoning |
| 4. Charter Generation | 10-12k | Full context synthesis |
| **Total** | **42-47k** | **~40% reduction from removing backtest stage** |

**Previous architecture (2-phase candidate generation):**
- Total: ~70-80k tokens
- Phase 1 Research alone: ~15-20k tokens (mostly redundant with context pack)

---

## Best Practices

### For Workflow Developers

1. **Provide comprehensive context packs** to minimize tool usage
   - Pre-compute regime analysis (macro, market, sector)
   - Include manual examples (Composer patterns)
   - Add recent events and benchmark data

2. **Make tool usage optional, not forced**
   - Default: Use provided context
   - Tools: Available for gaps in context
   - Result: Fewer tool calls = lower token usage

3. **Use parallel execution where possible**
   - Edge scoring: 5 agents in parallel (not sequential)

4. **Monitor token usage in production**
   - Enable `TRACK_TOKENS=true` for detailed reports
   - Watch for token overflow (>100k in single stage)
   - Enable compression if overflow occurs

### For Prompt Engineers

1. **Keep prompts concise but complete**
   - Avoid repeating context already in system prompt
   - Use structured formats (JSON, markdown tables)
   - Reference context pack sections instead of duplicating

2. **Instruct AI to cite context pack data**
   - Example: "VIX 18.6 per context pack" (not "VIX is around 18")
   - Reduces need for verification tool calls

3. **Provide clear tool usage guidelines**
   - When to use tools (gaps in context)
   - When NOT to use tools (data already provided)
   - Example queries (efficient API usage patterns)

---

## Debugging Token Issues

### Symptoms of Token Overflow

- ❌ API errors: "Context length exceeded"
- ❌ Agent loops: Repeatedly asking same questions
- ❌ Slow responses: LLM processing huge contexts

### Diagnostic Steps

1. **Enable token tracking:**
   ```bash
   export TRACK_TOKENS=true
   ```

2. **Review token report after run:**
   ```
   TOKEN ESTIMATE (Candidate Generation - BEFORE API CALL)
   ================================================================
   Label: Candidate Generation
   System Prompt: 2,500 tokens
   User Prompt: 15,000 tokens
   Tool Definitions: 8,000 tokens (estimate)
   ----------------------------------------------------------------
   Estimated Total: 25,500 tokens
   ```

3. **Identify culprit:**
   - System prompt too large? → Split into system + recipe
   - User prompt huge? → Shorten context pack or summarize
   - Tool definitions? → Reduce number of available tools
   - History too long? → Lower max_messages

4. **Apply fixes:**
   - Enable compression: `COMPRESS_MCP_RESULTS=true`
   - Reduce history: Lower `max_messages` in `adaptive_history_processor`
   - Optimize context pack: Remove verbose event descriptions
   - Exclude unused tools: `include_composer=False` if not needed

---

## Compression vs Context Trade-offs

### When Compression Helps

✅ **Use compression when:**
- Making many tool calls (10+ per stage)
- Tools return large datasets (time series, search results)
- Stage experiences token overflow (>100k)
- Historical data not critical (only need latest/trend)

### When Compression Hurts

❌ **Avoid compression when:**
- Detailed historical context matters (regime transitions)
- Few tool calls (1-3) with small results
- AI needs to see full time series (pattern recognition)
- Information loss risk outweighs token savings

### Current Recommendation

**Post-refactor (Phase 1 eliminated):**
- Default: Compression **disabled** (context pack reduces tool usage)
- Override: Enable if specific stage overflows
- Monitor: Track token usage in production, enable selectively

**Why?** Phase 1 elimination reduced tool calls by ~90%. Compression adds complexity without clear benefit unless token overflow occurs.

---

## Future Optimizations

### Potential Improvements

1. **Streaming tool results** - Process results incrementally instead of loading full response
2. **Smart caching** - Cache frequently-fetched data (SPY prices, Fed Funds rate)
3. **Lazy loading** - Fetch data only when AI explicitly requests it
4. **Semantic chunking** - Split large contexts into focused chunks per stage

### Monitoring & Tuning

Track these metrics in production:
- Tokens per stage (avg, p95, p99)
- Tool calls per stage (count, which tools)
- Compression ratio achieved (if enabled)
- Information loss incidents (AI asks for data that was compressed)

Tune based on:
- Cost (token usage × API pricing)
- Quality (strategy success rate)
- Latency (time per stage)

---

## Summary

**Key Takeaways:**

1. **History limiting (20 messages)** - Always enabled, prevents loops and overflow
2. **Tool result compression (97% reduction)** - Documented but disabled by default post-refactor
3. **Context pack strategy** - Primary optimization, eliminates redundant tool calls
4. **Single-phase generation** - Saves ~15-20k tokens vs 2-phase approach
5. **Opt-in compression** - Enable per-stage if token overflow occurs

**Token savings achieved:**
- Phase 1 elimination: ~15-20k tokens saved (~30% reduction)
- Total workflow: 52-57k tokens (vs 70-80k with 2-phase)
- Compression available if needed: ~10-15k additional savings

**Philosophy:** Optimize for **clarity first, tokens second**. Use comprehensive context packs and clear prompts. Apply compression only when necessary to avoid information loss.
