# MCP Compression Architecture Analysis

**Task ID**: fCNOYm3Ee_VoIYMXJwQBp
**Date**: 2025-11-02
**Status**: Intelligence Gathering Complete
**Priority**: High - Data Loss Issue

---

## Executive Summary

The MCP tool result compression system is losing **99.2% of time-series data** (3535 tokens → 27 tokens) due to an aggressive 30-token hard limit in the LLM summarization prompt. This compression reduces 217 daily FRED observations to just 4 fields (series_id, latest_value, date, trend), eliminating critical historical context needed for market regime analysis, volatility detection, and strategy creation.

**Key Finding**: Compression is currently **DISABLED by default** post-refactor (commit 367ad8b), so fixing it may have minimal immediate impact unless explicitly re-enabled per workflow stage.

**Recommended Solution**: Implement tiered, context-aware compression that preserves 30-90 days of time-series data using statistical aggregation and smart sampling, while maintaining token budget targets (~52-57k per workflow).

---

## Problem Statement

### Current Behavior

**File**: `src/agent/tool_result_summarizer.py:48`

```python
# THE ROOT CAUSE:
"Maximum 30 tokens in your response (HARD LIMIT)"
```

**Example Compression**:

**Before** (3535 tokens):
```json
{
  "series_id": "DGS10",
  "title": "Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity",
  "units": "Percent",
  "frequency": "Daily",
  "observation_range": "1962-01-02 to 2025-10-30",
  "total_observations": 217,
  "data": [
    {"date": "2025-01-01", "value": null},
    {"date": "2025-01-02", "value": 4.57},
    {"date": "2025-01-03", "value": 4.6},
    // ... 214 more observations
  ]
}
```

**After** (27 tokens):
```json
{
  "series_id": "DGS10",
  "name": "10-Yr Treasury Yield",
  "latest": 4.11,
  "date": "2025-10-30",
  "trend": "down"
}
```

**Data Lost**:
- Historical observations (216 data points)
- Volatility patterns
- Regime transitions
- Statistical context (min, max, mean, stddev)
- Temporal gaps and data quality indicators

### Impact on Strategy Creation

The AI hedge fund workflow requires:
- **Volatility analysis**: Need range, not just trend
- **Pattern recognition**: Need historical shape (30-90 days)
- **Regime detection**: Need multi-month context for transitions
- **Statistical analysis**: Need distribution, not point estimate

Current compression makes these analyses impossible.

---

## Intelligence Gathering Results

### Pattern Search: ZERO Matches

**APEX Pattern Database**: No patterns found for:
- Data compression strategies
- Token management refactoring
- Tiered/context-aware architecture
- Time-series data preservation

**Conclusion**: Manual first-principles approach required. This refactoring will CREATE patterns for future tasks.

### Similar Historical Tasks

**Task YKjkbdRhklQQOSk_J09sE**: EdgeScorecard field schema migration
- **Similarity**: 35% (schema refactoring with validation)
- **Key Learning**: "Grep-first discovery prevents missed updates"
- **Approach**: Systematic field mapping, sequential file validation

**Task 4FMT56blMcJh8UqIWw7ja**: Candidate generation validation fix
- **Similarity**: 33% (validation refactoring)
- **Key Learning**: "Simple solutions preferred over complex batch retry logic"

### Web Research: Best Practices

#### Production-Tested Strategies

1. **Tiered Compression** (Factory.ai)
   - 26-54% token reduction while preserving performance
   - Dual thresholds: T_max (compress above) / T_retained (preserve below)
   - Incremental updates avoid redundant re-summarization

2. **Restorable Compression** (Manus)
   - Preserve references (URLs, IDs, file paths)
   - Compress content but enable recovery
   - Critical: series_id matters more than all 5000 observations

3. **Statistical Aggregation** (Time-series research)
   - Preserve min/max/mean/stddev/percentiles vs raw truncation
   - Maintains distributional properties for decision-making

4. **Temporal Aggregation** (Academic consensus)
   - Daily→weekly aggregation increases signal/noise ratio
   - Chow-Lin method preserves movement patterns (7x reduction)

#### Anti-Patterns Identified

❌ **Naive truncation** (first/last N records) - Loses middle context
❌ **100% compression** (aggregates only) - Forces costly re-fetching
❌ **Single-pass irreversible** - Permanent information loss
❌ **Context-agnostic** - Simple Q&A tolerates 90%+ compression; analysis needs <50%
❌ **Equal temporal treatment** - Recent data has higher information value

### Codebase Implementation Patterns

#### Current Compression Pipeline

**File**: `src/agent/mcp_config.py:44-176`

```python
async def compress_tool_result(ctx, call_tool_func, name, args):
    """Compress large tool results before adding to conversation history."""

    # Step 1: Check if compression enabled
    if not COMPRESS_MCP_RESULTS:
        return await call_tool_func(name, args)

    # Step 2: Execute tool call
    result = await call_tool_func(name, args)

    # Step 3: Filter - only compress data-heavy tools
    data_heavy_tools = [
        "fred_get_series",      # Returns long time series
        "fred_search",          # Returns many search results
        "stock_get_historical_stock_prices",  # Returns price history
    ]
    if name not in data_heavy_tools:
        return result

    # Step 4: Size threshold check (200 chars)
    result_str = json.dumps(result)
    if len(result_str) < 200:
        return result  # Too small to compress

    # Step 5: LLM summarization with 30-token target
    summary_data = await summarizer.summarize(name, result)
    summary_content = summary_data["summary"]

    # Step 6: Hard cap safety net (600 chars = ~150 tokens)
    result_str = json.dumps(summary_content)
    if len(result_str) > 600:
        # Emergency truncation to prevent token overflow
        summary_content = truncate_to_600_chars(summary_content)

    return summary_content
```

#### Token Budget Management

**Per-Stage History Limits** (`src/agent/strategy_creator.py:93-144`):

```python
def create_history_processor(max_messages: int = 20):
    """
    Different workflow stages have different iteration needs:
    - Candidate Generation: 20 messages (iterative with tools)
    - Edge Scoring: 10 messages (single evaluation)
    - Winner Selection: 10 messages (single-pass reasoning)
    - Charter Generation: 20 messages (complex synthesis)
    """
```

**Current Token Budget**:
- Candidate Generation: 12-15k tokens
- Edge Scoring: 15k tokens (5 candidates in parallel)
- Winner Selection: 5k tokens
- Charter Generation: 10-12k tokens
- **Total Workflow**: 42-47k tokens

**Result**: 30% reduction from initial 2-phase architecture

#### Project Conventions

- **Environment Variables**: `COMPRESS_MCP_RESULTS=true`, `SUMMARIZATION_MODEL=openai:gpt-5-mini`
- **Tool Prefixing**: `fred_*`, `stock_*`, `composer_*`
- **Pydantic Models**: All structured outputs (Strategy, Charter, EdgeScorecard)
- **Async Context Managers**: MCP server lifecycle via AsyncExitStack
- **Error Handling**: Defensive fallback to original result on compression failure

### Git History Analysis

**Repository Age**: 9 days (extremely young codebase)

**Compression Timeline**:

1. **Oct 24, 2025** (Commit 57332af) - Initial commit
   - Baseline MCP integration (FRED, yfinance, Composer)
   - No compression
   - Token usage: Unknown

2. **Nov 1, 2025** (Commit 69246c4) - **Compression introduced**
   - LLM-based summarization: 97% reduction (1578 → 50 tokens)
   - Hard cap at 150 tokens (~600 chars)
   - Target: 30 tokens per result
   - MCP timeouts increased: 5s → 30s

3. **Nov 1, 2025** (Commit 576724e) - **Infinite loop bug fix**
   - **Issue**: Agent repeatedly searching same queries after context loss
   - **Root Cause**: 10-message history limit caused forgetting
   - **Fix**: Increased max_messages from 10 → 20
   - **Insight**: Compression working (97% reduction), but history window too short

4. **Nov 1, 2025** (Commit 367ad8b) - **Compression disabled by default**
   - Phase 1 research elimination reduced tool usage by 90%
   - Context pack strategy minimizes MCP tool calls
   - Compression available but not critical
   - **Current state**: `COMPRESS_MCP_RESULTS=true` but not enforced per stage

**Key Takeaway**: Architecture still evolving rapidly (5 workflow refactors in 9 days). High experimental churn suggests patterns not yet stable.

---

## Risk Analysis

### Critical Risks

| Risk | Likelihood | Impact | Severity | Priority |
|------|-----------|--------|----------|----------|
| Token budget explosion | Medium | High | **CRITICAL** | P0 |
| Edge cases (quarterly data, gaps) | High | Medium | **HIGH** | P1 |
| Test coverage gaps | High | Medium | **HIGH** | P1 |
| Information loss still occurring | Medium | High | **HIGH** | P1 |
| Breaking consumers of format | Low | Medium | **MEDIUM** | P2 |
| Performance degradation | Low | Low | **LOW** | P3 |

### Risk 1: Token Budget Explosion (CRITICAL)

**Scenario**: Decompressing from 27 tokens → 300-900 tokens breaks stage budgets.

**Evidence**:
- Current workflow: 42-47k tokens
- Charter Generation: 10-12k tokens (20-message history)
- If 5 `fred_get_series` calls with 90d windows: 5 × 900 = 4,500 tokens
- With 20-message history: 4,500 × 20 = **90k tokens** (exceeds budget)

**Triggers**:
- AI makes 5+ tool calls in Charter stage
- Each returns 90 days × 12 tokens/observation
- Conversation history accumulates uncompressed results

**Mitigation**:
1. **Adaptive compression** based on call count and budget
   - First 3 calls: Preserve 90 days (moderate)
   - Calls 4-7: Preserve 30 days (aggressive)
   - Calls 8+: Latest + trend only (maximum)

2. **Budget monitoring** with warnings at 80% utilization

3. **Sliding window compression**:
   - Latest 7 days: Full granularity
   - Last 30 days: Weekly samples
   - Last 90 days: Monthly samples
   - Statistical summary (min/max/mean/trend)

### Risk 2: Edge Cases in Time Series

**Scenario**: Different series have varying frequencies and gaps.

**FRED Series Types**:
- **Daily**: VIX, 10Y Treasury (365 points/year)
- **Weekly**: Jobless Claims (52 points/year)
- **Monthly**: CPI, Unemployment (12 points/year)
- **Quarterly**: GDP (4 points/year)
- **Irregular**: FOMC announcements

**Current Issue**: Compression is frequency-agnostic (treats all equally).

**Example Problems**:

1. **Over-compression of quarterly GDP**:
   - 90 days = 0-1 observations
   - Compressing 1 point to "trend" loses all context

2. **Under-sampling daily VIX**:
   - 90 days = 90 observations
   - Weekly samples miss daily volatility spikes

3. **Missing data gaps**:
   - Market holidays create gaps
   - Compression may mislead AI about trend continuity

**Mitigation**:

1. **Frequency-aware compression**:
   ```python
   def detect_frequency(observations):
       intervals = [obs2.date - obs1.date for obs1, obs2 in zip(obs[:-1], obs[1:])]
       median_interval = statistics.median(intervals)

       if median_interval <= 1: return "daily"
       elif median_interval <= 7: return "weekly"
       elif median_interval <= 35: return "monthly"
       else: return "quarterly"
   ```

2. **Preserve outliers + representative samples**:
   - Keep latest 7 days (full)
   - Keep outliers (>2 std dev)
   - Keep regime transitions
   - Fill gaps with equally-spaced samples

3. **Gap detection & annotation**:
   ```python
   {
       "observations": [...],
       "gaps": [{"start": "2024-11-02", "end": "2024-11-10", "duration_days": 8}],
       "note": "Series has 3 gaps > expected interval"
   }
   ```

### Risk 3: Test Coverage Gaps (HIGH)

**Current State**: ZERO compression tests exist.

```bash
$ rg "test.*compress|test.*summariz" tests/**/*.py
# No files found
```

**Risks Without Tests**:
- Silent failures (compression breaks, workflow continues)
- Regressions (future changes break compression)
- Edge cases missed (quarterly data, gaps, outliers)
- Token budget violations (no automated enforcement)

**Mitigation**:

1. **Unit Tests for Compression**:
   ```python
   @pytest.mark.parametrize("series_type,expected_tokens", [
       ("daily_90d", 300),
       ("monthly_90d", 100),
       ("quarterly_90d", 50)
   ])
   def test_compress_by_frequency(series_type, expected_tokens):
       observations = generate_test_series(series_type)
       compressed = compress_time_series_smart(observations, max_tokens=500)
       actual_tokens = len(json.dumps(compressed)) // 4
       assert actual_tokens <= expected_tokens * 1.2
   ```

2. **Integration Tests with Real Data**:
   ```python
   @pytest.mark.integration
   async def test_fred_compression_real_data():
       result = await fred_mcp.get_series("VIXCLS", observation_start="2024-08-01")
       compressed = compress_tool_result(result)
       assert len(json.dumps(compressed)) // 4 <= 500
       assert "observations" in compressed or "latest_value" in compressed
   ```

3. **Property-Based Tests**:
   ```python
   from hypothesis import given, strategies as st

   @given(observations=st.lists(st.fixed_dictionaries({
       "date": st.dates(),
       "value": st.floats(min_value=-1000, max_value=1000)
   }), min_size=1, max_size=365))
   def test_compression_always_valid_json(observations):
       compressed = compress_time_series_smart(observations, max_tokens=500)
       json_str = json.dumps(compressed)
       assert json.loads(json_str) == compressed
   ```

---

## Recommended Solution

### Tiered Context-Aware Compression

**Design Principles**:
1. **Preserve essential time-series structure** (not just latest value)
2. **Maintain token budget** (~52-57k per workflow)
3. **Context-aware** (different stages have different needs)
4. **Backward compatible** (existing stages continue working)
5. **Observable** (metrics for information preservation)

### Compression Levels

```yaml
compression_levels:
  MINIMAL:  # Debug, critical analysis
    max_points: 1000
    strategy: "smart_sampling"
    metadata: "full"
    use_case: "Development, debugging"

  BALANCED:  # Default for production (RECOMMENDED)
    max_points: 100
    strategy: "dual_level"
    recent_days: 30
    recent_resolution: "daily"
    historical_resolution: "weekly"
    stats: ["mean", "min", "max", "stddev"]
    metadata: "full"
    use_case: "Charter generation, strategy creation"

  AGGRESSIVE:  # Token-constrained scenarios
    max_points: 20
    strategy: "statistical_summary"
    resolution: "monthly"
    stats: ["mean", "min", "max", "p50", "current"]
    metadata: "essential_only"
    use_case: "High tool usage, budget pressure"
```

### Implementation Architecture

#### 1. Compression Strategy Selector

```python
# src/agent/compression/strategy.py

def select_compression_strategy(
    tool_name: str,
    series_id: str,
    observations: List[dict],
    context: CompressionContext
) -> str:
    """
    Select compression level based on:
    - Tool usage frequency (call_count)
    - Budget remaining (token_budget)
    - Series characteristics (frequency, length)
    """

    # Detect series frequency
    frequency = detect_frequency(observations)

    # Check budget pressure
    budget_utilization = context.current_usage / context.budget_limit

    # Adaptive selection
    if context.call_count <= 2 and budget_utilization < 0.5:
        return "BALANCED"  # First few calls, plenty of budget
    elif context.call_count <= 5 or budget_utilization < 0.8:
        return "BALANCED"  # Moderate usage
    else:
        return "AGGRESSIVE"  # Heavy usage or budget pressure
```

#### 2. Time-Series Compression Engine

```python
# src/agent/compression/timeseries.py

def compress_time_series_balanced(
    observations: List[dict],
    max_tokens: int = 500
) -> dict:
    """
    Balanced compression: Preserve recent detail + historical summary.

    Strategy:
    - Latest 7 days: Full granularity (daily observations)
    - Last 30 days: Weekly samples (every 7th day)
    - Last 90 days: Monthly samples (every 30th day)
    - Statistical summary: min/max/mean/stddev/trend
    """

    # Preserve recent detail
    latest_7d = observations[-7:] if len(observations) >= 7 else observations

    # Weekly samples for 30-day window
    last_30d_weekly = observations[-30::7] if len(observations) >= 30 else []

    # Monthly samples for 90-day window
    last_90d_monthly = observations[-90::30] if len(observations) >= 90 else []

    # Calculate statistics
    values = [obs["value"] for obs in observations if obs["value"] is not None]
    stats = {
        "mean": statistics.mean(values),
        "min": min(values),
        "max": max(values),
        "stddev": statistics.stdev(values) if len(values) > 1 else 0,
        "trend": calculate_trend(observations)
    }

    # Detect gaps
    gaps = detect_gaps(observations)

    return {
        "latest_7d": latest_7d,
        "last_30d_weekly": last_30d_weekly,
        "last_90d_monthly": last_90d_monthly,
        "stats_90d": stats,
        "gaps": gaps,
        "frequency": detect_frequency(observations),
        "compression_level": "BALANCED"
    }
```

#### 3. Metadata Preservation

```python
def preserve_metadata(fred_result: dict) -> dict:
    """
    Always preserve critical metadata regardless of compression level.
    """
    return {
        "series_id": fred_result.get("id"),
        "title": fred_result.get("title"),
        "units": fred_result.get("units"),
        "frequency": fred_result.get("frequency"),
        "seasonal_adjustment": fred_result.get("seasonal_adjustment"),
        "observation_range": {
            "start": fred_result.get("observation_start"),
            "end": fred_result.get("observation_end")
        },
        "source": "Federal Reserve Economic Data (FRED)"
    }
```

#### 4. Domain-Specific Compression

```python
def compress_fred_series_smart(
    series_id: str,
    observations: List[dict],
    compression_level: str
) -> dict:
    """
    Apply domain-specific compression based on series type.
    """

    # VIX: Preserve volatility spikes and regime changes
    if series_id == "VIXCLS":
        return compress_volatility_series(observations, compression_level)

    # Unemployment: Preserve trend changes
    elif series_id == "UNRATE":
        return compress_trend_series(observations, compression_level)

    # Fed Funds Rate: Preserve policy changes
    elif series_id in ["DFF", "FEDFUNDS"]:
        return compress_policy_series(observations, compression_level)

    # Default: Balanced compression
    else:
        return compress_time_series_balanced(observations)
```

### Configuration System

#### Environment Variables

```bash
# Enable/disable compression globally
COMPRESS_MCP_RESULTS=true

# Default compression level (MINIMAL, BALANCED, AGGRESSIVE)
DEFAULT_COMPRESSION_LEVEL=BALANCED

# Time-series window sizes (days)
COMPRESSION_WINDOW_RECENT=7
COMPRESSION_WINDOW_SHORT=30
COMPRESSION_WINDOW_LONG=90

# Token budget per stage
CANDIDATE_GENERATION_TOKEN_BUDGET=15000
CHARTER_GENERATION_TOKEN_BUDGET=12000

# Summarization model (for fallback LLM compression)
SUMMARIZATION_MODEL=openai:gpt-5-mini
```

#### Per-Stage Overrides

```python
# src/agent/stages/charter_generator.py

# Charter generation needs detailed historical data
agent_ctx = await create_agent(
    model=model,
    output_type=Charter,
    system_prompt=system_prompt,
    history_limit=20,
    compression_config={
        "level": "BALANCED",
        "time_series_window": 30,  # 30 days of daily data
        "preserve_outliers": True,
        "preserve_regime_changes": True
    }
)
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1)

**Tasks**:
1. ✅ Create `src/agent/compression/` module structure
2. ✅ Implement compression strategy selector
3. ✅ Add budget monitoring and telemetry
4. ✅ Write unit tests for compression edge cases

**Deliverables**:
- `compression/strategy.py` - Strategy selection logic
- `compression/timeseries.py` - Time-series compression engine
- `compression/metadata.py` - Metadata preservation
- `tests/agent/test_compression.py` - Unit tests

**Validation**:
```bash
pytest tests/agent/test_compression.py -v
```

### Phase 2: Smart Compression (Week 2)

**Tasks**:
1. ✅ Implement frequency-aware compression
2. ✅ Add domain-specific compression (VIX, CPI, Fed Funds)
3. ✅ Implement outlier preservation and gap detection
4. ✅ Add compression quality scoring

**Deliverables**:
- `compression/frequency.py` - Frequency detection and handling
- `compression/domain.py` - Domain-specific strategies
- `compression/quality.py` - Quality metrics

**Validation**:
```bash
pytest tests/agent/test_compression.py::test_frequency_aware_compression -v
pytest tests/agent/test_compression.py::test_domain_specific_compression -v
```

### Phase 3: Integration (Week 3)

**Tasks**:
1. ✅ Update `mcp_config.py` to use new compression system
2. ✅ Update `tool_result_summarizer.py` prompts
3. ✅ Add configuration system (env vars, per-stage overrides)
4. ✅ Run integration tests

**Deliverables**:
- Updated `mcp_config.py` with new compression pipeline
- Updated `tool_result_summarizer.py` with tiered prompts
- Configuration documentation

**Validation**:
```bash
pytest tests/agent/test_fred_mcp.py -v
pytest tests/agent/test_phase5_integration.py -v
```

### Phase 4: Validation (Week 4)

**Tasks**:
1. ✅ Run A/B tests (current vs new compression)
2. ✅ Compare charter quality (edge scorecard metrics)
3. ✅ Tune compression parameters based on results
4. ✅ Update TOKEN_MANAGEMENT.md documentation

**Deliverables**:
- A/B test results report
- Tuned compression parameters
- Updated documentation

**Success Metrics**:
- Token usage < 60k per workflow (vs target 52-57k)
- Charter pass rate ≥ 80% (thesis ≥3, edge ≥3, risk ≥3)
- Information preservation quality score ≥ 0.7

---

## Success Criteria

### Quantitative Metrics

**Before Fix**:
- Compression ratio: 99.2% (3535 → 27 tokens)
- Data points preserved: 1 (latest only)
- Test coverage: 0 tests
- Quality score: N/A (no metrics)

**After Fix (Target)**:
- Compression ratio: 85-90% (3535 → 300-500 tokens)
- Data points preserved: 30-100 (BALANCED level)
- Test coverage: 20+ tests (unit + integration)
- Quality score: ≥0.7 (trend, regime, outliers preserved)
- Token budget: < 60k per workflow (vs 42-47k baseline)
- Charter pass rate: Maintain ≥80%

### Qualitative Goals

✅ AI can detect market regime transitions (bull → bear)
✅ AI can identify volatility patterns and clustering
✅ AI can perform statistical analysis (mean, stddev, range)
✅ AI can cite specific dates and values in charter reasoning
✅ AI can detect correlation breakdowns and outliers

---

## Monitoring & Observability

### Production Telemetry

```python
# Log compression decisions
log_compression_metrics({
    "tool_name": "fred_get_series",
    "series_id": "VIXCLS",
    "original_tokens": 3535,
    "compressed_tokens": 327,
    "compression_ratio": 0.092,  # 90.8% reduction
    "compression_level": "BALANCED",
    "quality_score": 0.72,
    "outliers_preserved": 5,
    "gaps_detected": 2
})

# Log budget status
log_budget_metrics({
    "stage": "charter_generation",
    "budget_limit": 12000,
    "current_usage": 8400,
    "utilization": 0.70,  # 70%
    "approaching_limit": False
})

# Log charter quality
log_charter_quality({
    "compression_enabled": True,
    "compression_level": "BALANCED",
    "edge_scorecard": {
        "thesis_quality": 3.5,
        "edge_economics": 3.2,
        "risk_framework": 3.1
    },
    "passed": True,
    "tool_calls_made": 6,
    "avg_compression_ratio": 0.11
})
```

### Alerts

**Alert 1**: Token budget at 95% → Compression insufficient
**Alert 2**: Compression quality < 0.5 → Information loss risk
**Alert 3**: Charter failure with compression → Investigate correlation

### Dashboard Metrics

- Token usage per stage (p50, p95, p99)
- Compression ratio distribution
- Quality score distribution
- Charter pass rate (with/without compression)
- Budget overflow incidents

---

## Open Questions

1. **Window Size Preference**: 30d vs 60d vs 90d?
   - **30d**: ~300 tokens (conservative, lowest risk)
   - **60d**: ~600 tokens (moderate, balanced)
   - **90d**: ~900 tokens (comprehensive, highest quality)
   - **Recommendation**: Start with 30d, measure, scale up if budget allows

2. **Compression Strategy**: LLM vs Algorithmic vs Hybrid?
   - **LLM**: Semantic understanding, readable, costs ~$0.001/call
   - **Algorithmic**: Deterministic, fast, no hallucination
   - **Hybrid**: Algorithmic structure + LLM summarization
   - **Recommendation**: Hybrid approach (this proposal uses algorithmic)

3. **Enable Per-Stage or Global**?
   - Currently disabled by default
   - **Recommendation**: Enable only in Charter Generation (highest tool usage)

4. **Scope**: FRED only or also yfinance?
   - **FRED**: `fred_get_series` (time series)
   - **yfinance**: `stock_get_historical_stock_prices` (OHLCV data)
   - **Recommendation**: Start with FRED, extend to yfinance after validation

---

## References

### Files Modified

**Core Implementation**:
- `src/agent/mcp_config.py:44-176` - Compression callback
- `src/agent/tool_result_summarizer.py:24-181` - LLM summarization
- `src/agent/token_tracker.py:43-272` - Token tracking

**Workflow Integration**:
- `src/agent/stages/charter_generator.py:60-65` - Uses compression
- `src/agent/stages/candidate_generator.py:91-92` - Uses compression
- `src/agent/workflow.py:24-142` - Orchestrates workflow

**Documentation**:
- `docs/TOKEN_MANAGEMENT.md` - Token optimization strategies
- `CLAUDE.md:98-101` - Project architecture overview

### External Resources

**Production Systems**:
- Factory.ai: ACON framework (arXiv:2510.00615)
- Manus: Context engineering lessons (https://manus.im/blog)

**Research**:
- Time-series aggregation (Chow-Lin method)
- LLM context window optimization
- Statistical summarization techniques

---

## Appendix: Code Examples

### Example 1: Frequency Detection

```python
def detect_frequency(observations: List[dict]) -> str:
    """
    Infer series frequency from observation spacing.

    Returns: "daily", "weekly", "monthly", "quarterly", "unknown"
    """
    if len(observations) < 2:
        return "unknown"

    # Calculate intervals between consecutive observations
    intervals = []
    for obs1, obs2 in zip(observations[:-1], observations[1:]):
        if obs1.get("value") is not None and obs2.get("value") is not None:
            date1 = datetime.fromisoformat(obs1["date"])
            date2 = datetime.fromisoformat(obs2["date"])
            intervals.append((date2 - date1).days)

    if not intervals:
        return "unknown"

    median_interval = statistics.median(intervals)

    if median_interval <= 1:
        return "daily"
    elif median_interval <= 7:
        return "weekly"
    elif median_interval <= 35:
        return "monthly"
    else:
        return "quarterly"
```

### Example 2: Outlier Preservation

```python
def preserve_outliers(
    observations: List[dict],
    threshold_stddev: float = 2.0
) -> List[dict]:
    """
    Identify and preserve statistical outliers.

    Args:
        threshold_stddev: Number of standard deviations for outlier detection

    Returns:
        List of outlier observations with metadata
    """
    values = [obs["value"] for obs in observations if obs["value"] is not None]

    if len(values) < 3:
        return []

    mean = statistics.mean(values)
    stddev = statistics.stdev(values)

    outliers = []
    for obs in observations:
        if obs["value"] is not None:
            z_score = abs((obs["value"] - mean) / stddev) if stddev > 0 else 0
            if z_score >= threshold_stddev:
                outliers.append({
                    **obs,
                    "z_score": z_score,
                    "percentile": calculate_percentile(obs["value"], values)
                })

    return outliers
```

### Example 3: Gap Detection

```python
def detect_gaps(
    observations: List[dict],
    expected_frequency: str = None
) -> List[dict]:
    """
    Detect and annotate data gaps in time series.

    Returns:
        List of gaps with start/end dates and duration
    """
    if expected_frequency is None:
        expected_frequency = detect_frequency(observations)

    expected_interval = {
        "daily": 1,
        "weekly": 7,
        "monthly": 30,
        "quarterly": 90
    }.get(expected_frequency, 1)

    gaps = []
    for obs1, obs2 in zip(observations[:-1], observations[1:]):
        date1 = datetime.fromisoformat(obs1["date"])
        date2 = datetime.fromisoformat(obs2["date"])
        interval = (date2 - date1).days

        # Gap detected if interval > 2x expected
        if interval > expected_interval * 2:
            gaps.append({
                "start": obs1["date"],
                "end": obs2["date"],
                "duration_days": interval,
                "expected_days": expected_interval
            })

    return gaps
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-02
**Author**: Claude (via APEX Intelligence Gathering)
**Status**: Ready for Architecture Phase
