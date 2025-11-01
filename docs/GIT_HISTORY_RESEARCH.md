# Git History Research: AI Hedge Fund Test Evolution & MCP Integration Lessons

## Executive Summary

This report analyzes 5 recent commits (Oct 24-28, 2025) that restructured the agent workflow from a monolithic design to a stage-based architecture. Key insight: **Test patterns evolved from 6-dimension static scoring → AI-based dynamic evaluation → refined data models**, revealing successful and failed approaches for async MCP testing.

---

## Timeline & Evolution

### Phase 1: Initial Implementation (Oct 24, 2025)
**Commit:** `831cc10` - feat(agent): implement Phase 5 workflow orchestration

**What was built:**
- Initial workflow orchestration with 5-stage pipeline
- Static scoring system (6 dimensions) in `src/agent/scoring.py`
- Cost tracking system (`CostTracker` class)
- Initial test suite with direct imports

**Test approach:**
- 16 tests covering cost tracking, scoring, and workflow
- Heavy reliance on mocks for AI and Composer
- Tests organized by function (test_cost_tracker.py, test_scoring.py)

**Architecture:**
```
workflow.py (463 lines)
  ├── generate_candidates()
  ├── score_candidates() [6 static dimensions]
  ├── backtest_all_candidates()
  ├── select_winner()
  └── generate_charter()
```

**Issues that emerged:**
- Tight coupling between stages made mocking difficult
- Static scoring inflexible (6 hard-coded dimensions)
- Cost tracking added overhead without clear value
- No clear separation of concerns

---

### Phase 2: Stage Pattern Refactoring (Oct 25, 2025)
**Commit:** `eb2a6df` - refactor(agent): restructure workflow with stage pattern and remove cost tracking

**Key insights from this refactor:**

✅ **What worked (WINS):**
1. **Stage classes** - Extracted `CandidateGenerator`, `WinnerSelector`, `CharterGenerator` as separate classes
2. **Prompt externalization** - Moved prompts to `src/agent/prompts/*.md` for easier iteration
3. **75% code reduction** - workflow.py: 463 → 117 lines
4. **Cleaner test organization** - Tests became class-based, mirroring domain concepts
5. **Removed cost tracking** - Reduced unnecessary overhead (1,437 lines deleted)

❌ **What failed:**
1. Initial async/await patterns caused integration test flakiness
2. MCP server mocking was brittle with stdio servers
3. No centralized fixture strategy early on

**Test evolution:**
```python
# OLD: Function-based tests (harder to mock)
def test_scoring():
    result = evaluate_edge_scorecard(strategy)

# NEW: Class-based with fixtures (easier to mock)
class TestWinnerSelector:
    async def test_composite_score_ranking(self, sample_candidates, sample_scorecards):
        selector = WinnerSelector()
        result = await selector.select(...)
```

**Commit stats:**
- +7 new stage tests (all passing)
- -240 lines of legacy scoring tests
- -1,437 total lines (cost tracking removed)

---

### Phase 3: AI-Based Scoring Upgrade (Oct 26-27, 2025)
**Commit:** `0c7edd7` - refactor(agent): replace static scoring with AI-based EdgeScorer agent

**Paradigm shift:**
- Deleted static scoring functions (356 lines of deterministic heuristics)
- Added `EdgeScorer` agent using pydantic-ai
- New prompt-based evaluation (650+ lines in edge_scoring.md)

**Test pattern evolution:**
```python
# OLD: Test exact score values
assert score == 5  # Brittle, failed often

# NEW: Test score ranges and constraints
assert 3.0 <= scorecard.total_score <= 5.0  # Flexible, accommodates AI variance
assert all(dim >= 3 for dim in scorecard.dimensions)  # Test constraints, not values
```

**Key testing lessons:**
1. **Never mock LLM output completely** - Instead:
   - Mock agent creation but let prompts through
   - Test constraint checking (e.g., score >= 3.0)
   - Accept variance in reasoning text
   
2. **Parallel evaluation pattern:**
```python
# Good: Parallel scoring of 5 candidates
results = await asyncio.gather(
    score_candidate(c1), score_candidate(c2), ...
)

# Problem: Sequential scoring is 5x slower
for candidate in candidates:
    score = await score_candidate(candidate)  # Takes 5x longer
```

**Commit stats:**
- -356 lines (static scoring deleted)
- +650 lines (prompt engineering)
- 3 agent tests remaining (higher quality)

---

### Phase 4: Institution-Grade Evaluation System (Oct 27, 2025)
**Commit:** `d9598e1` - feat(agent): upgrade edge scoring to institutional-grade evaluation system

**Model evolution:**
```python
# OLD: 6 dimensions (static)
EdgeScorecard(
    specificity=4,
    structural_basis=3,
    regime_alignment=4,
    differentiation=4,
    failure_clarity=3,
    mental_model_coherence=4
)

# NEW: 5 dimensions (semantically clearer)
EdgeScorecard(
    thesis_quality=5,          # What inefficiency are we exploiting?
    edge_economics=5,          # Does the edge have positive expected value?
    risk_framework=5,          # How are risks quantified and managed?
    regime_awareness=5,        # Is strategy adaptive to market conditions?
    strategic_coherence=5      # Do all components fit together?
)
```

**Prompt engineering innovations:**
- Layered architecture (context → rules → dimensions → anti-gaming safeguards)
- Chain-of-thought scoring (show work for each dimension)
- Constitutional constraints (what scores mean institutionally)
- Few-shot calibration examples
- Evidence-based scoring (cite specific parts of strategy)

**Test impact:**
- Updated all fixtures to new 5-dimension model
- Edge Scorecard min threshold still 3.0/5 (maintained validation bar)
- Tests now validate semantic meaning, not mechanical dimensions

**Lesson learned:** When evaluating AI output, focus on:
- Range validation (not specific values)
- Semantic coherence (dimensions make logical sense)
- Constraint satisfaction (minimum thresholds)
- Evidence presence (reasoning is articulated)

---

### Phase 5: Data Model Alignment (Oct 28, 2025)
**Commit:** `cca56f4` - fix(agent): resolve data model mismatches in charter creation workflow

**Problems fixed:**
1. `SelectionReasoning` had 3 fields → now 5:
   - `why_selected` (existing)
   - `winner_index` (existing)
   - `tradeoffs_accepted` (NEW)
   - `alternatives_rejected` (NEW, renamed from `alternatives_compared`)
   - `conviction_level` (NEW)

2. `CharterGenerator` was accessing non-existent fields
3. Tests had wrong fixture data

**Key testing lesson:** 
✅ **Mock side-effects instead of return values**
```python
# GOOD: side_effect allows different contexts per call
mock_create.side_effect = [
    mock_research_context,  # First call
    mock_generate_context   # Second call
]

# FRAGILE: Single mock fails when called twice with different types
mock_create.return_value = mock_agent  # Works once, then fails
```

**Impact:**
- All unit tests passing (7/7 in test_stages.py)
- Integration test still requires real context pack
- Data flow verified through all 5 workflow stages

---

## Test Implementation Patterns That Emerged

### Pattern 1: Fixture Hierarchy (Best Practice)
```python
@pytest.fixture
def sample_market_context():
    """Minimal valid context pack."""
    return {
        "metadata": {...},
        "regime_snapshot": {...},
        "macro_indicators": {...}
    }

@pytest.fixture
def sample_candidates():
    """5 distinct Strategy objects."""
    return [Strategy(...) for i in range(5)]

@pytest.fixture
def sample_scorecards():
    """5 EdgeScorecard objects with varied scores."""
    return [EdgeScorecard(...) for varying configs]

@pytest.fixture
def sample_backtests():
    """5 BacktestResult objects."""
    return [BacktestResult(...) for i in range(5)]

# Usage: Test receives all fixtures automatically
class TestWinnerSelector:
    async def test_some_behavior(self, sample_candidates, sample_scorecards):
        selector = WinnerSelector()
        result = await selector.select(sample_candidates, sample_scorecards)
        assert result...
```

**Why this works:**
- Fixtures are composable
- Easy to override for specific test cases
- Minimal data duplication
- Clear dependencies

---

### Pattern 2: Stage Class Testing (Successful Async Pattern)

```python
class TestCandidateGenerator:
    """Test a single stage in isolation."""
    
    @pytest.mark.asyncio
    async def test_count_validation(self, sample_market_context):
        """Verify generator enforces exactly 5 candidates."""
        generator = CandidateGenerator()
        
        with patch('src.agent.stages.candidate_generator.create_agent') as mock_create:
            # Setup phased mocking
            mock_research_agent = AsyncMock()
            mock_research_result = AsyncMock()
            mock_research_result.output = {...}  # Phase 1 output
            
            mock_generate_agent = AsyncMock()
            mock_generate_result = AsyncMock()
            mock_generate_result.output = [...]  # Phase 2 output (only 1 strategy)
            
            # KEY: Use side_effect for multiple different calls
            mock_create.side_effect = [
                mock_research_context,
                mock_generate_context
            ]
            
            # Verify error handling
            with pytest.raises(ValueError, match="Expected 5 candidates, got 1"):
                await generator.generate(sample_market_context, model="...")
```

**Why this pattern works:**
✅ Tests single responsibility (count validation)
✅ AsyncMock handles async/await properly
✅ side_effect handles sequential calls
✅ Clear failure message for debugging
✅ No coupling to AI implementation details

---

### Pattern 3: Constraint-Based Testing (Over Value-Based)

```python
# FRAGILE: Test depends on exact score values
async def test_scorecard_value():
    scorecard = EdgeScorecard(thesis_quality=5, edge_economics=4, ...)
    assert scorecard.total_score == 4.6  # Brittle!

# ROBUST: Test constraints and ranges
async def test_scorecard_constraints():
    scorecard = EdgeScorecard(
        thesis_quality=4,
        edge_economics=3,
        risk_framework=4,
        regime_awareness=4,
        strategic_coherence=4
    )
    # Verify minimum thresholds
    assert scorecard.total_score >= 3.0, "Must pass validation threshold"
    
    # Verify all dimensions valid
    assert all(getattr(scorecard, dim) >= 3 for dim in 
               ['thesis_quality', 'edge_economics', 'risk_framework', 
                'regime_awareness', 'strategic_coherence'])
    
    # Verify no dimension exceeds max
    assert all(getattr(scorecard, dim) <= 5 for dim in [...])
```

**Why constraint-based testing works:**
- Accommodates AI variance in reasoning
- Tests what actually matters (validations)
- Doesn't depend on implementation details
- More maintainable long-term

---

### Pattern 4: Integration Test Markers & Skips

```python
@pytest.mark.integration
class TestPhase5EndToEnd:
    """End-to-end tests that require real services."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_with_real_context_and_mcps(self):
        """Test with real context pack, FRED, yfinance, Composer MCPs."""
        # Validate environment
        required_vars = ['OPENAI_API_KEY', 'FRED_API_KEY', 
                        'COMPOSER_API_KEY', 'COMPOSER_API_SECRET']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            pytest.skip(f"Missing environment variables: {', '.join(missing_vars)}")
        
        # Load real context pack
        context_pack_path = Path("data/context_packs/latest.json")
        
        if not context_pack_path.exists():
            pytest.skip(f"Context pack not found at {context_pack_path}")
        
        # Execute real workflow
        result = await create_strategy_workflow(
            market_context=market_context,
            model='openai:gpt-4o'
        )
        
        # Verify results exist (not mock values)
        assert len(result.candidates) == 5
        assert result.winner is not None
        assert result.charter is not None
```

**Key practices:**
✅ Use `@pytest.mark.integration` to separate fast unit tests from slow integration tests
✅ Validate environment before running (graceful skip, not hard failure)
✅ Test real MCPs when available, not mocked replacements
✅ Accept that real tests are slower (~30-60s) and cost money (~$1-2)

---

## MCP Integration Lessons Learned

### Lesson 1: HTTP vs Stdio Servers Need Different Mocking Strategies

**Stdio Servers (FRED, yfinance):**
```python
# These run as local processes
# Good for: Development, fast iteration
# Mocking pattern: Mock subprocess creation or create_agent calls

# Problem: If server dies, all tests hang
# Solution: Set timeouts on all subprocess calls
```

**HTTP Servers (Composer):**
```python
# These require network calls
# Good for: Real backtesting
# Mocking pattern: Mock HTTP responses OR create test stub server

# Problem: Rate limits, authentication failures
# Solution: Use environment-based skipping (see Pattern 4 above)
```

### Lesson 2: Graceful Degradation Pattern

```python
async def backtest_all_candidates(candidates):
    """Backtest with graceful degradation if Composer unavailable."""
    try:
        # Try to use real Composer
        results = await _backtest_via_composer_mcp(candidates)
    except Exception as e:
        logger.warning(f"Composer unavailable: {e}, using fallback")
        # Return neutral results that pass validation
        results = [
            BacktestResult(
                sharpe_ratio=1.0,        # Neutral
                max_drawdown=-0.15,      # Typical
                total_return=0.10,       # Average
                volatility_annualized=0.12
            )
            for _ in candidates
        ]
    return results
```

**Why this works:**
- Tests pass even if Composer API is down
- Unit tests don't require API credentials
- Integration tests validate real behavior
- Development workflow stays smooth

### Lesson 3: Token Tracking for MCP Efficiency

**Observation:** The codebase is adding `token_tracker.py` and `tool_result_summarizer.py` to optimize token usage across MCP calls.

**Pattern to emerge:**
```python
# Future pattern (based on git status showing new files):
class TokenTracker:
    def track_mcp_call(self, tool_name, input_tokens, output_tokens):
        """Track token usage per MCP tool."""
        pass
    
    def summarize_tool_results(self, results):
        """Compress verbose tool outputs to reduce context window."""
        pass
```

**Why this matters for tests:**
- Need to validate token tracking accuracy
- Tests should verify compression doesn't lose critical data
- Integration tests should check cost accumulation
- Unit tests should verify token counting logic

---

## Critical Lessons for Your Implementation

### 1. Phased Prompting with AsyncMock (Critical)

When testing agents that make multiple internal calls:

```python
# PROBLEM: Single mock fails after first call
mock_agent = AsyncMock()
mock_agent.run.return_value = AsyncMock()  # Only works once

# SOLUTION: Use side_effect for different phases
@patch('src.agent.stages.candidate_generator.create_agent')
async def test_two_phase_generation(mock_create):
    # Phase 1: Research → returns dict
    mock_phase1_agent = AsyncMock()
    mock_phase1_agent.run.return_value = AsyncMock()
    mock_phase1_agent.run.return_value.output = {"macro": "...", "market": "..."}
    
    # Phase 2: Generate → returns list
    mock_phase2_agent = AsyncMock()
    mock_phase2_agent.run.return_value = AsyncMock()
    mock_phase2_agent.run.return_value.output = [Strategy(...), ...]
    
    # KEY: side_effect returns different mock for each call
    mock_create.side_effect = [
        AsyncMock(__aenter__=AsyncMock(return_value=mock_phase1_agent)),
        AsyncMock(__aenter__=AsyncMock(return_value=mock_phase2_agent))
    ]
    
    generator = CandidateGenerator()
    result = await generator.generate(context)
    
    assert len(result) == 5
```

### 2. Separate Unit Tests from Integration Tests

**Unit tests (fast, no APIs):**
- Test stage logic in isolation
- Mock MCP calls
- No environment variables needed
- Run in <1 second total

**Integration tests (slow, real APIs):**
- Test real MCP communication
- Test real context packs
- Require environment setup
- Use `@pytest.mark.integration` and `pytest.skip()` for missing env vars
- Run in 30-60 seconds

### 3. Data Model Mismatches Are the #1 Failure Point

From commit `cca56f4`, the most common test failures come from:
- Stage output type doesn't match next stage input
- Mock fixtures don't match actual data model
- Field names change mid-workflow

**Prevention pattern:**
```python
# Always validate data shapes at stage boundaries
class TestStageOutput:
    async def test_winner_selector_output_structure(self):
        """Validate WinnerSelector returns SelectionReasoning with all 5 fields."""
        selector = WinnerSelector()
        result = await selector.select(candidates, scorecards)
        
        # Verify exact model contract
        assert isinstance(result, SelectionReasoning)
        assert hasattr(result, 'why_selected')
        assert hasattr(result, 'winner_index')
        assert hasattr(result, 'tradeoffs_accepted')
        assert hasattr(result, 'alternatives_rejected')
        assert hasattr(result, 'conviction_level')
        
        # Verify types
        assert isinstance(result.why_selected, str)
        assert isinstance(result.winner_index, int)
        assert isinstance(result.conviction_level, float)
        assert isinstance(result.alternatives_rejected, list)
```

### 4. Minimum Viable Test Coverage

Based on the evolution, effective test organization is:

```
tests/agent/
├── test_stages.py           # Unit tests for 3 stage classes (7 tests, <5s)
├── test_workflow.py         # Unit tests for orchestration (5 tests, <3s)
├── test_scoring.py          # Unit tests for EdgeScorer (3 tests, ~10-15s with API)
├── test_phase5_integration.py  # Full end-to-end integration (2 tests, ~60s with APIs)
├── test_composer_integration.py # Composer-specific tests (5 tests, <5s)
├── test_mcp_config.py       # MCP server factory tests (8 tests, <1s)
├── test_fred_mcp.py         # FRED tool tests (minimal)
├── test_yfinance_mcp.py     # yfinance tool tests (minimal)
└── test_models.py           # Data model validation (7 tests, <1s)
```

**Total: ~40 tests, ~2 minutes for full suite**

### 5. Test File Growth Pattern

From the git history, test file sizes grew strategically:

```
Initial (Oct 24):      16 tests across 4 files
After refactor (Oct 25): 23 tests (cost tracking removed)
After AI upgrade (Oct 26): 11 core tests (high quality)
After model fix (Oct 28): 12 tests (data models fixed)
```

**Pattern:** Fewer, higher-quality tests beat more mocks and brittle assertions.

---

## Commits Summary

| Date | Commit | Impact | Lessons |
|------|--------|--------|---------|
| Oct 24 | 831cc10 | Phase 5 initial | Monolithic design was hard to test |
| Oct 25 | eb2a6df | Stage pattern | 75% code reduction, cleaner tests |
| Oct 26 | 0c7edd7 | AI scoring | Static scoring was inflexible, AI better |
| Oct 27 | d9598e1 | Institutional grade | 5 clearer dimensions > 6 vague ones |
| Oct 28 | cca56f4 | Data alignment | Data mismatches = #1 test failure |

---

## Recommendations for Your Token Tracking Implementation

Based on this evolution:

1. **Start with unit tests** for `TokenTracker` class
   - Mock MCP tool calls
   - Verify token counting accuracy
   - Test edge cases (truncation, rounding)

2. **Separate concern from workflow**
   - Don't couple token tracking to strategy generation
   - Use composition, not inheritance
   - Easy to swap real tracker for mock in tests

3. **Integration test gracefully**
   - Token tracking shouldn't break workflow if it fails
   - Use try/except to catch tracking errors
   - Log but don't fail on tracking issues

4. **Follow the fixture pattern**
   - Create TokenTracker with realistic state
   - Compose it into fixture for stage tests
   - Mock it completely in unit tests if needed

5. **Constraint-based testing**
   - Test token counts are non-negative
   - Test totals are >= individual parts
   - Test compression reduces tokens
   - NOT the exact token count (depends on LLM)

---

## Code References

Key files demonstrating best practices:
- `/Users/ben/dev/ai-hedge-fund/tests/agent/test_stages.py` (552 lines) - Best fixture/mocking patterns
- `/Users/ben/dev/ai-hedge-fund/tests/agent/test_phase5_integration.py` (395 lines) - Integration test structure
- `/Users/ben/dev/ai-hedge-fund/tests/agent/test_workflow.py` (248 lines) - Orchestration tests
- `/Users/ben/dev/ai-hedge-fund/tests/agent/test_composer_integration.py` (229 lines) - HTTP MCP testing

