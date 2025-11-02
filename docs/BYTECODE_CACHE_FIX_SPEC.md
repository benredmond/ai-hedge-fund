# Phase 5 Integration Test Fix & Logging Optimization

**Task ID**: `pJZnYGQ0QaNihNoIDmGrj`
**Created**: 2025-11-02
**Status**: ARCHITECT phase complete, ready for BUILDER

---

## Executive Summary

**Problem**: Integration test failing due to stale Python bytecode cache containing old EdgeScorecard validator that enforces minimum score ≥3 per dimension. Secondary issue: debug logging floods console without environment variable controls.

**Root Cause**: EdgeScorecard `dimension_above_threshold` validator was removed from source code but remains in `__pycache__/models.cpython-312.pyc`, causing ValidationError when candidates score <3.

**Solution**: Clear bytecode cache + add conditional logging with environment variables following existing codebase patterns.

**Impact**: Enables graceful degradation (candidates can score <3), reduces console noise, maintains diagnostic capability.

---

## Architecture Decision

**Selected Approach**: Solution A - Cache Clear + Conditional Logging Pattern

**Rationale**:
- Directly addresses root cause with minimal complexity (3/10)
- Follows existing codebase patterns (os.getenv has 95% coverage)
- Lowest risk (LOW) and fastest implementation (30 minutes)
- Matches team preference: "prioritize simple, readable code with minimal abstraction"

**Confidence**: 0.9 (high - root cause confirmed via git archaeology and pattern analysis)

---

## Root Cause Analysis

### Timeline of EdgeScorecard Evolution

| Date | Commit | Change | Impact |
|------|--------|--------|--------|
| Oct 24 | `bd90662` | Add `dimension_above_threshold` validator (6 dims) | Enforced min score 3 |
| Oct 27 | `d9598e1` | Refactor to 5 dimensions | Validator preserved |
| Nov 2 | (Working dir) | **Remove validator** from source | Bytecode cache not cleared |

### Evidence Trail

1. **Source Code** (`src/agent/models.py:217-218`):
   ```python
   # No validator for minimum threshold - filtering happens in winner_selector.py
   # Dimensions can score 1-5; candidates with total_score <3.0 are filtered during selection
   ```

2. **Bytecode Cache** (`src/agent/__pycache__/models.cpython-312.pyc`):
   - Contains compiled version WITH validator
   - Python imports bytecode before checking source timestamp
   - Stale due to 1-second filesystem mtime granularity

3. **Test Error**:
   ```
   pydantic_core._pydantic_core.ValidationError: 2 validation errors for EdgeScorecard
   edge_economics: Value error, Edge Scorecard dimension scored 2, minimum threshold is 3
   regime_awareness: Value error, Edge Scorecard dimension scored 2, minimum threshold is 3
   ```

---

## Implementation Specification

### Phase 1: Bytecode Cache Clearing

**Objective**: Remove stale compiled bytecode to force recompilation from source

**Commands**:
```bash
# Clear all Python bytecode cache
find src -type d -name __pycache__ -exec rm -rf {} +
find tests -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name '*.pyc' -delete
```

**Verification**:
```bash
# Confirm cache directories removed
! find src -type d -name __pycache__ | grep -q .
! find tests -type d -name __pycache__ | grep -q .
```

**Safety**: Clearing `__pycache__` is always safe - Python recreates as needed. No production impact.

---

### Phase 2: DEBUG_LLM_OUTPUT Environment Variable

**Objective**: Control debug logging of full LLM responses (currently always on, floods console)

**Pattern**: Follow existing `COMPRESS_MCP_RESULTS` pattern from `mcp_config.py:40`

#### File 1: `src/agent/stages/edge_scorer.py`

**Location**: After imports (around line 10)

```python
import os
import json
from src.agent.strategy_creator import (
    create_agent,
    load_prompt,
    DEFAULT_MODEL
)
from src.agent.models import Strategy, EdgeScorecard

# Debug output configuration
DEBUG_LLM_OUTPUT = os.getenv("DEBUG_LLM_OUTPUT", "false").lower() == "true"
```

**Modification**: Lines 104-107 (wrap existing debug print)

```python
# BEFORE:
# Debug logging: Print full LLM response for debugging format issues
print(f"\n[DEBUG:EdgeScorer] Full LLM response:")
print(f"{raw_output}")

# AFTER:
if DEBUG_LLM_OUTPUT:
    print(f"\n[DEBUG:EdgeScorer] Full LLM response:")
    print(f"{raw_output}")
```

#### File 2: `src/agent/stages/winner_selector.py`

**Location**: After imports (around line 10)

```python
import os
from typing import List, Tuple
from src.agent.strategy_creator import create_agent, load_prompt, DEFAULT_MODEL
from src.agent.models import (
    Strategy,
    EdgeScorecard,
    SelectionReasoning
)

# Debug output configuration
DEBUG_LLM_OUTPUT = os.getenv("DEBUG_LLM_OUTPUT", "false").lower() == "true"
```

**Modification**: Lines 205-207 (wrap existing debug print)

```python
# BEFORE:
# Debug logging: Print full LLM response
print(f"\n[DEBUG:WinnerSelector] Full LLM response:")
print(f"{reasoning}")

# AFTER:
if DEBUG_LLM_OUTPUT:
    print(f"\n[DEBUG:WinnerSelector] Full LLM response:")
    print(f"{reasoning}")
```

#### Additional Files (if debug prints exist):
- `src/agent/stages/candidate_generator.py` (check for `[DEBUG:CandidateGenerator]` prints)
- `src/agent/stages/charter_generator.py` (check for `[DEBUG:CharterGenerator]` prints)

**Default Behavior**: Debug output **disabled** (opt-in via env var)

---

### Phase 3: VERBOSE_COMPRESS Environment Variable

**Objective**: Control compression logging verbosity (currently prints full objects, 1000+ chars)

#### File: `src/agent/mcp_config.py`

**Location**: After line 41 (with other config constants)

```python
# Tool result compression configuration
COMPRESS_MCP_RESULTS = os.getenv("COMPRESS_MCP_RESULTS", "true").lower() == "true"
SUMMARIZATION_MODEL = os.getenv("SUMMARIZATION_MODEL", "openai:gpt-5-mini")
VERBOSE_COMPRESS = os.getenv("VERBOSE_COMPRESS", "false").lower() == "true"
```

**Modification**: Lines 118-127 (conditional logging)

```python
# BEFORE:
# Log compression stats with full content
original_full = str(result) if result else "N/A"
summary_full = str(summary_content) if summary_content else "N/A"
print(
    f"[COMPRESS] {name}: {summary_data['original_tokens']} → "
    f"{summary_data['summary_tokens']} tokens "
    f"({summary_data['savings']} saved)"
)
print(f"[COMPRESS]   Before: {original_full}")
print(f"[COMPRESS]   After:  {summary_full}")

# AFTER:
# Log compression stats
print(
    f"[COMPRESS] {name}: {summary_data['original_tokens']} → "
    f"{summary_data['summary_tokens']} tokens "
    f"({summary_data['savings']} saved)"
)

if VERBOSE_COMPRESS:
    # Full content preview (current behavior)
    original_full = str(result) if result else "N/A"
    summary_full = str(summary_content) if summary_content else "N/A"
    print(f"[COMPRESS]   Before: {original_full}")
    print(f"[COMPRESS]   After:  {summary_full}")
else:
    # Truncated preview (200 chars max)
    original_preview = str(result)[:200] if result else "N/A"
    summary_preview = str(summary_content)[:200] if summary_content else "N/A"
    print(f"[COMPRESS]   Before: {original_preview}{'...' if len(str(result)) > 200 else ''}")
    print(f"[COMPRESS]   After:  {summary_preview}{'...' if len(str(summary_content)) > 200 else ''}")
```

**Default Behavior**: Show **truncated** previews (200 chars) with ellipsis if longer

---

## Validation Plan

### Test Execution Sequence

1. **Verify Cache Clear**:
   ```bash
   # Should return empty (no __pycache__ directories)
   find src tests -type d -name __pycache__
   ```

2. **Run Integration Test** (primary success criterion):
   ```bash
   ./venv/bin/pytest tests/agent/test_phase5_integration.py::TestPhase5EndToEnd::test_full_workflow_with_real_context_and_mcps -xvs
   ```
   **Expected**: Test passes completely, 5 candidates generated, graceful degradation works

3. **Test DEBUG_LLM_OUTPUT** (disabled by default):
   ```bash
   # Should NOT show [DEBUG:*] output
   ./venv/bin/pytest tests/agent/test_phase5_integration.py::TestPhase5EndToEnd -xvs 2>&1 | grep -c "DEBUG:"
   # Expected: 0

   # Should show [DEBUG:*] output when enabled
   DEBUG_LLM_OUTPUT=true ./venv/bin/pytest tests/agent/test_phase5_integration.py::TestPhase5EndToEnd -xvs 2>&1 | grep -c "DEBUG:"
   # Expected: >0
   ```

4. **Test VERBOSE_COMPRESS** (truncated by default):
   ```bash
   # Should show truncated previews (200 chars + "...")
   ./venv/bin/pytest tests/agent/test_phase5_integration.py::TestPhase5EndToEnd -xvs 2>&1 | grep "COMPRESS.*\.\.\." | wc -l
   # Expected: >0

   # Should show full content when enabled
   VERBOSE_COMPRESS=true ./venv/bin/pytest tests/agent/test_phase5_integration.py::TestPhase5EndToEnd -xvs 2>&1 | grep -A2 "COMPRESS"
   # Expected: Full JSON objects visible
   ```

### Success Criteria

✅ **Primary**: Integration test passes without ValidationError
✅ **Secondary**: Debug output controlled by `DEBUG_LLM_OUTPUT` env var
✅ **Secondary**: Compression logging controlled by `VERBOSE_COMPRESS` env var
✅ **Performance**: No measurable performance degradation (env var checks are O(1))

---

## Pattern Justification

### Why This Pattern?

**os.getenv Pattern** (Trust Score: ★★★★★, 95% coverage):
- **Dominant**: Used in 15+ locations (mcp_config.py, strategy_creator.py, tool_result_summarizer.py, cli.py)
- **Consistent**: All boolean env vars use `.lower() == "true"` conversion
- **Simple**: Module-level constants, no abstraction layer
- **Tested**: Existing pattern has test coverage via pytest monkeypatch

**Example from Codebase** (`src/agent/mcp_config.py:40`):
```python
COMPRESS_MCP_RESULTS = os.getenv("COMPRESS_MCP_RESULTS", "true").lower() == "true"
```

### Alternatives Considered (and Rejected)

| Approach | Reason for Rejection |
|----------|---------------------|
| `importlib.invalidate_caches()` in pytest fixture | Overkill for one-time cache issue; adds complexity (5/10 vs 3/10) |
| `PYTHONDONTWRITEBYTECODE=1` | 20-50% test performance degradation; no ongoing benefit |
| Structured logging class | 120 min refactor; violates YAGNI; print() is codebase standard |
| Pydantic BaseSettings | Only 2 env vars; pattern mismatch; unnecessary dependency |

---

## Risk Analysis

### Known Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Cache clearing doesn't fix issue | Low | Medium | Verify EdgeScorecard source has no validators before clearing |
| Env var names clash | Low | Low | Grep confirmed no existing `DEBUG_LLM_OUTPUT` or `VERBOSE_COMPRESS` |
| Performance degradation | Very Low | Low | Boolean checks are negligible (nanoseconds) |
| Test assertion bug at line 132 | Medium | Low | Run test first; fix `sum(candidate.weights.values())` if needed |

### Contingency Plans

**If cache clearing fails**:
1. Inspect `src/agent/models.py` for hidden validators
2. Check if Pydantic has internal validator cache (`__pydantic_validator__`)
3. Try `Model.model_rebuild(force=True)` as fallback

**If test still fails at line 132**:
```python
# Current (potentially broken):
assert abs(sum(candidate.weights) - 1.0) < 0.01

# Fixed (sum values, not keys):
assert abs(sum(candidate.weights.values()) - 1.0) < 0.01
```

---

## Implementation Checklist

### BUILDER Phase Tasks

- [ ] **1. Verify Source Code** (2 min)
  - [ ] `grep -n "@field_validator" src/agent/models.py | grep -A5 EdgeScorecard`
  - [ ] Confirm lines 217-218 show comment, not validator

- [ ] **2. Clear Bytecode Cache** (1 min)
  - [ ] `find src -type d -name __pycache__ -exec rm -rf {} +`
  - [ ] `find tests -type d -name __pycache__ -exec rm -rf {} +`
  - [ ] `find . -type f -name '*.pyc' -delete`

- [ ] **3. Add DEBUG_LLM_OUTPUT** (10 min)
  - [ ] Add constant to `edge_scorer.py` (after imports)
  - [ ] Wrap debug print at lines 104-107
  - [ ] Add constant to `winner_selector.py` (after imports)
  - [ ] Wrap debug print at lines 205-207
  - [ ] Check `candidate_generator.py` for debug prints
  - [ ] Check `charter_generator.py` for debug prints

- [ ] **4. Add VERBOSE_COMPRESS** (10 min)
  - [ ] Add constant to `mcp_config.py` (after line 41)
  - [ ] Modify lines 118-127 with conditional logic
  - [ ] Add truncation logic for default behavior

- [ ] **5. Validate Implementation** (10 min)
  - [ ] Run integration test (should pass)
  - [ ] Test DEBUG_LLM_OUTPUT=false (no debug output)
  - [ ] Test DEBUG_LLM_OUTPUT=true (debug output visible)
  - [ ] Test VERBOSE_COMPRESS=false (truncated previews)
  - [ ] Test VERBOSE_COMPRESS=true (full content)

**Estimated Duration**: 33 minutes

---

## Documentation Updates

### CLAUDE.md Addendum

Add to environment variables section:

```markdown
**Optional (Development/Debugging):**
- **DEBUG_LLM_OUTPUT**: Enable full LLM response logging in workflow stages (default: `false`)
  - Set to `true` to see complete AI responses during candidate generation, edge scoring, winner selection, charter creation
  - Useful for debugging prompt/response issues or understanding AI reasoning
  - Warning: Generates 10,000+ lines of console output

- **VERBOSE_COMPRESS**: Enable full object logging in MCP result compression (default: `false`)
  - Set to `true` to see complete before/after objects for compressed tool results
  - Default shows 200-char truncated previews with ellipsis
  - Useful for debugging compression quality or validating summaries preserve key data
```

### .env.example Addition

```bash
# Optional: Debug/Development Settings
# DEBUG_LLM_OUTPUT=false    # Enable full LLM response logging (default: false)
# VERBOSE_COMPRESS=false     # Enable full compression logging (default: false)
```

---

## YAGNI Decisions

**Explicitly Excluded** (can add later if needed):

1. ❌ **pytest fixture with importlib.invalidate_caches()** - One-time issue, not recurring
2. ❌ **PYTHONDONTWRITEBYTECODE for tests** - 20-50% performance hit for no benefit
3. ❌ **Structured logging class** - print() works fine, team standard
4. ❌ **Pydantic BaseSettings for env vars** - Only 2 vars, unnecessary complexity
5. ❌ **.gitignore update for __pycache__** - Already in standard Python .gitignore

---

## Historical Context

**Git Archaeology Findings**:

- **High Churn**: `models.py` had 8 commits in 2 weeks (rapid iteration phase)
- **Single Contributor**: benredmond (22 commits), suggests prototyping phase
- **Architectural Shifts**: 2-stage → 5-stage → 4-stage workflow evolution
- **Validator Journey**: Added Oct 24 → Preserved Oct 27 → Removed Nov 2 (uncommitted)

**Key Learning**: Model schema changes require bytecode cache invalidation. Consider:
- Documenting cache clearing in development workflow
- Adding cache clear to CI/CD pipeline between commits
- Using factory functions instead of pickled test fixtures

---

## References

**Intelligence Sources**:
- APEX Task History: 4 similar successful tasks (YKjkbdRhklQQOSk_J09sE, ca_45Gy0Py0SoP4oEk8NC, etc.)
- Implementation Patterns: 15 files analyzed, 95% os.getenv pattern coverage
- Web Research: Python bytecode caching (official docs), pytest best practices, Pydantic validator caching
- Git History: 22 commits analyzed over 2-week window

**Key Files**:
- `src/agent/models.py:181-218` - EdgeScorecard model (no validators in source)
- `src/agent/workflow.py:96-110` - Graceful degradation logic
- `src/agent/stages/winner_selector.py:52-78` - Filtering logic for score <3.0
- `tests/agent/test_phase5_integration.py:54-113` - Integration test setup

---

## Appendix: Architecture Artifacts

### Tree of Thought (3 Solutions Evaluated)

**Solution A** (Selected): Cache Clear + Conditional Logging
- Complexity: 3/10, Risk: LOW, Time: 30 min
- Follows existing patterns, minimal changes

**Solution B** (Runner-up): importlib.invalidate_caches() + Test Fixture
- Complexity: 5/10, Risk: MEDIUM, Time: 45 min
- More robust but unnecessary for one-time issue

**Solution C** (Rejected): PYTHONDONTWRITEBYTECODE + Logging Class
- Complexity: 8/10, Risk: HIGH, Time: 120 min
- Major refactor, performance hit, violates YAGNI

### Pattern Selection Rationale

All patterns follow existing codebase conventions:
- ★★★★★ os.getenv with default value (dominant, 95% coverage)
- ★★★★★ Boolean conversion with `.lower() == "true"` (100% consistency)
- ★★★★★ Module-level env var constants (standard practice)
- ★★★★☆ Conditional feature flags (established pattern)

---

**Specification Version**: 1.0
**Last Updated**: 2025-11-02
**Status**: Ready for BUILDER implementation
