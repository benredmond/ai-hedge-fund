# Stage-by-Stage Token Analysis

Analysis of token usage and history requirements for each workflow stage.

## Stage 1: Candidate Generation

**Characteristics:**
- Single-phase generation with optional tool usage
- May make 0-10 tool calls (Composer search, specific asset lookups)
- Iterative: AI may refine candidates based on diversity checks

**Current History Limit:** 20 messages

**Optimal History Limit:** 20 messages ✓

**Reasoning:**
- Needs room for iterative refinement ("generated 5, checking diversity, adjusting...")
- Tool calls add messages (request + response per call)
- Risk of loops if limit too low (forgets previous attempts)

**Token Impact:**
- Typical: 12-15k tokens
- With many tool calls: Could reach 20-25k
- History: ~3-5k tokens (20 messages with compression)

---

## Stage 2: Edge Scoring (per candidate)

**Characteristics:**
- Single structured evaluation per candidate
- No tool usage (scoring based on strategy attributes)
- Non-iterative: Input → output, no back-and-forth

**Current History Limit:** 20 messages

**Optimal History Limit:** 10 messages ✓

**Reasoning:**
- Simple evaluation shouldn't need iteration
- No tool calls (fewer messages generated)
- 10 messages = safety buffer for unexpected multi-turn

**Token Impact:**
- Typical: 3k tokens per candidate
- History: ~1-2k tokens (10 messages, no compression needed)
- **Savings: ~1k tokens per candidate × 5 = ~5k total**

---

## Stage 3: Backtesting (per candidate)

**Characteristics:**
- Single tool call to Composer backtest
- Minimal conversation (prompt → tool call → parse)
- Uses separate agent per backtest (isolated context)

**Current History Limit:** 20 messages

**Optimal History Limit:** 5 messages ✓

**Reasoning:**
- Extremely simple: Just wraps a single tool call
- No iteration needed
- Each agent is short-lived (one backtest)

**Token Impact:**
- Typical: 2k tokens per candidate
- History: ~500 tokens (5 messages)
- **Savings: ~500 tokens per candidate × 5 = ~2.5k total**

---

## Stage 4: Winner Selection

**Characteristics:**
- Structured input (5 candidates + scores + backtests)
- Generates SelectionReasoning output
- Non-iterative: Composite ranking → AI reasoning

**Current History Limit:** 20 messages

**Optimal History Limit:** 10 messages ✓

**Reasoning:**
- Selection is single-pass (input → reasoning)
- May need a few turns for structured output validation
- 10 messages = comfortable buffer

**Token Impact:**
- Typical: 5k tokens
- History: ~1-2k tokens (10 messages)
- **Savings: ~1k tokens**

---

## Stage 5: Charter Generation

**Characteristics:**
- Uses full context pack as the anchor-dated source; tools only for gaps or added color
- Synthesizes full context (winner + reasoning + scores)
- Potentially iterative (context review -> analysis -> charter sections; tools optional)

**Current History Limit:** 20 messages

**Optimal History Limit:** 20 messages ✓

**Reasoning:**
- Most complex stage - needs full context
- Tool usage optional and limited to gaps
- Charter has 5 sections (may iterate per section)

**Token Impact:**
- Typical: 10-12k tokens
- History: ~3-5k tokens (20 messages with optional compression)
- No change (already optimal)

---

## Summary: Recommended History Limits

| Stage | Current | Recommended | Savings | Reasoning |
|-------|---------|-------------|---------|-----------|
| 1. Candidate Generation | 20 | **20** | 0 | Iterative, tool usage |
| 2. Edge Scoring | 20 | **10** | ~5k total | Simple evaluation, no tools |
| 3. Backtesting | 20 | **5** | ~2.5k total | Single tool call per agent |
| 4. Winner Selection | 20 | **10** | ~1k | Single-pass reasoning |
| 5. Charter Generation | 20 | **20** | 0 | Complex synthesis, context-pack-first; tools only for gaps |

**Total Potential Savings:** ~8.5k tokens per workflow run

---

## Implementation Strategy

### Option A: Per-Stage History Processors (Recommended)

Create configurable history processor factory:

```python
def create_history_processor(max_messages: int):
    """Factory for adaptive history processors with configurable limits."""
    def processor(ctx: RunContext, messages: list) -> list:
        if len(messages) <= max_messages:
            return messages
        result = messages[-max_messages:]
        if result and not isinstance(result[-1], _messages.ModelRequest):
            result.append(_messages.ModelRequest(parts=[]))
        return result
    return processor
```

Then in each stage:
```python
# edge_scorer.py
agent = Agent(
    model=model,
    output_type=EdgeScorecard,
    system_prompt=system_prompt,
    history_processors=[create_history_processor(max_messages=10)]
)
```

### Option B: Keep Global Default (Current)

Leave all stages at 20 messages:
- **Pros:** Simpler, safer (no unexpected truncation)
- **Cons:** Wastes ~8.5k tokens per run (~10% overhead)

---

## Recommendation

**Implement Option A** because:
1. Each stage has clearly different iteration needs
2. Savings (~8.5k tokens) is meaningful (~15% of total)
3. Implementation is straightforward (factory pattern)
4. No risk of information loss (limits sized for each stage's needs)

**Priority:**
- **High:** Backtesting (5 messages) - huge waste to use 20 for single tool call
- **Medium:** Edge Scoring (10 messages) - 5k tokens saved across 5 candidates
- **Low:** Winner Selection (10 messages) - smaller savings but clean

---

## Testing Strategy

After implementing per-stage limits:

1. **Functional tests:** Ensure all stages complete successfully
2. **Token tracking:** Compare before/after token reports
3. **Quality check:** Verify output quality unchanged
4. **Edge cases:** Test strategies that require max iterations

Expected result: ~8.5k token savings with no quality degradation.
