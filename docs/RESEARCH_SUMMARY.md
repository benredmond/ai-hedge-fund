# Research Summary: Symphony Logic Audit Insertion Point

**Task**: Map validation flow in strategy creation workflow and identify optimal insertion point for Symphony Logic Audit.

**Status**: Complete ✓

---

## Key Findings

### 1. Validation Stages Identified

**Stage 1: Candidate Generation** (Lines 186-222 in workflow.py)
- Runs `_validate_semantics()` on all 5 candidates in parallel
- Validates: syntax, concentration, leverage, archetype, thesis-logic coherence, weight derivation
- Produces: List of validation errors, triggers retry with guidance
- Data available: Strategy only (no charter context)

**Stage 2: Edge Scoring** (Lines 224-263 in workflow.py)
- Parallel evaluation of all candidates
- No validation - pure scoring

**Stage 3: Winner Selection** (Lines 265-289 in workflow.py)
- Composite ranking (50% scorecard + 50% LLM evaluation)
- No validation - pure selection

**Stage 4: Charter Generation** (Lines 291-321 in workflow.py)
- Creates comprehensive charter with 5 sections
- Passes `winner.logic_tree` to charter context (line 81 in charter_generator.py)
- No validation currently
- **← RECOMMENDED INSERTION POINT (Stage 4)**

**Stage 5: Deployment** (Lines 323-357 in workflow.py)
- Converts `strategy.logic_tree` → Composer symphony JSON
- Calls Composer API
- No validation before API call
- **← SECONDARY INSERTION POINT (Stage 5, as safety gate)**

### 2. Logic Tree Lifecycle

```
Creation (Stage 1):
  - LLM generates Strategy.logic_tree as dict
  - Empty {} for static allocation
  - OR {condition, if_true, if_false} for conditional

Validation (Stage 1):
  - Pydantic model validator checks structure
  - Semantic validator checks thesis-value coherence
  - Thesis mentions "VIX > 25" ≈ logic_tree has "VIX > 25" (±20%)

Selection (Stages 2-3):
  - logic_tree unchanged
  - Used to distinguish between strategies

Charter (Stage 4):
  - Referenced in selection_context (informational only)
  - Not modified or validated further

Deployment (Stage 5):
  - Passed to _build_symphony_json()
  - Converted to Composer IF structure
  - Sent to Composer API
```

### 3. Optimal Insertion Points (Ranked)

#### Option B (Recommended): Stage 4 Charter Generation
**Location**: After charter synthesis in `charter_generator.py`

**Pros**:
- Has full charter context (failure modes, market thesis, expected behavior)
- Runs on single winner only (efficient)
- Correlates logic with charter's regime analysis
- Still before deployment (can inform decisions)
- Low token cost (~400 tokens/strategy)
- Non-blocking (doesn't halt workflow)

**Cons**:
- Runs after selection (can't retry candidates)
- Audit warnings don't trigger fixes

**Implementation**: Add `_audit_symphony_logic()` method that returns warnings (non-blocking)

---

#### Option C (Safety Gate): Stage 5 Deployment
**Location**: Before `_build_symphony_json()` in `composer_deployer.py`

**Pros**:
- Final gate before Composer API
- Can prevent deployment failures
- Catches issues created during charter generation
- Very cheap (~100 tokens/strategy)

**Cons**:
- Too late to fix (workflow already complete)
- Would require restarting from Stage 4
- Blocks deployment without recovery

**Implementation**: Add `_audit_symphony_logic_for_deployment()` method that returns errors (blocking)

---

### 4. Recommended Approach: Hybrid (B + C)

**Primary Audit at Stage 4**: Context-aware, non-blocking warnings
- Assesses regime applicability
- Correlates with charter failure modes
- Flags potential issues before deployment
- Provides actionable feedback

**Safety Gate at Stage 5**: Strict blocking validation
- Ensures Composer API won't fail on symphony JSON
- Prevents invalid syntax from reaching API
- Returns (None, None, None) to block deployment

This hybrid approach:
1. Catches semantic issues early with full context
2. Provides final safety gate before expensive API call
3. Maintains workflow flexibility (Stage 4 doesn't block)
4. Preserves checkpoint/resume capability

---

## Data Flow Summary

### Stage 1 Validation (Existing)

```
Stage 1: CandidateGenerator
├─> _validate_semantics(candidates, market_context)
│   ├─> _validate_syntax()
│   ├─> _validate_concentration()
│   ├─> _validate_leverage_justification()
│   ├─> _validate_archetype_logic_tree()
│   ├─> _validate_thesis_logic_tree_coherence()
│   └─> _validate_weight_derivation_coherence()
│
└─> RETURN: List[str] errors
    ├─> IF errors: Retry with fix guidance
    └─> IF pass: Continue to Stage 2
```

**What it validates**:
- ✓ Logic_tree structure valid if non-empty
- ✓ Thesis mentions "VIX > 25" ≈ logic_tree has "VIX > 25"
- ✓ Archetype matches structure (e.g., momentum + rotation → logic_tree required)
- ✗ **Does NOT**: Check if condition makes market sense, activates in current regime

### Stage 4 Audit (Recommended New)

```
Stage 4: CharterGenerator
├─> charter = await self._generate_charter_document(...)
│
├─> IF winner.logic_tree:
│   └─> _audit_symphony_logic(strategy, charter, market_context)
│       ├─> _validate_condition_syntax()
│       ├─> _validate_branch_completeness()
│       ├─> _validate_asset_consistency()
│       ├─> _assess_regime_applicability()
│       └─> _validate_charter_alignment()
│
│   └─> RETURN: SymphonyLogicAuditResult
│       ├─> warnings: List[str]
│       ├─> checks_performed: List[str]
│       └─> regime_applicability: dict
│
│   └─> Log warnings (non-blocking)
│
└─> RETURN: charter (unchanged)
    └─> Continue to Stage 5
```

**What it validates**:
- ✓ Condition syntax valid for Composer parsing
- ✓ Branch assets make logical sense for scenario (e.g., defensive if VIX > 25)
- ✓ Condition likely to activate in current/near-term market regime
- ✓ Failure modes mention relevant branch assets

### Stage 5 Audit (Optional Safety Gate)

```
Stage 5: ComposerDeployer._deploy_once()
├─> confirmation = await _get_llm_confirmation(...)
│
├─> IF strategy.logic_tree:
│   └─> _audit_symphony_logic_for_deployment(strategy, market_context)
│       ├─> _is_composer_compatible_condition()
│       ├─> _check_asset_availability()
│       └─> _validate_weights_per_branch()
│
│   └─> RETURN: List[str] errors
│
│   ├─> IF errors NOT EMPTY:
│   │   └─> RETURN (None, None, None)  # BLOCK deployment
│   │
│   └─> IF errors EMPTY:
│       └─> Continue to symphony_json build
│
└─> symphony_json = _build_symphony_json(...)
```

**What it validates**:
- ✓ No AND/OR operators in condition (Composer limitation)
- ✓ All assets available in Composer
- ✓ Weights sum to 1.0 per branch
- ✓ No schema violations before API call

---

## Invariants (Must Preserve)

### 1. Stage Ordering
Stages must run in order: Candidates → Scoring → Selection → Charter → Deployment

Audit insertion doesn't change this. Both Stage 4 and Stage 5 audits run within their respective stages.

### 2. Data Immutability
Once Stage 1 completes, `strategy.logic_tree` is read-only. Later stages can audit but not modify.

**Consequence**: Audit in Stage 4+ cannot trigger strategy retry. It can only warn/inform.

### 3. Checkpoint Compatibility
- Checkpoints save strategy state after each stage
- On resume, strategy must match original
- Audit doesn't modify stored state

**Consequence**: Audit is metadata only - doesn't affect checkpoint integrity

### 4. Error Propagation
```
Stage 1: validation_errors → Retry with guidance
Stage 4: audit_warnings → Log and continue (non-blocking)
Stage 5: audit_errors → Block deployment, return (None, None, None)
```

### 5. Single Winner Constraint
Only one strategy proceeds past Stage 3. Audit runs only on winner.

**Consequence**: Stage 4/5 audits are cheap (single strategy, not 5)

---

## Integration Points

### File: `/Users/ben/dev/ai-hedge-fund/src/agent/stages/charter_generator.py`
**Line**: After 117 (after `generate()` completes)
**Method**: New async method `_audit_symphony_logic()`
**Signature**:
```python
async def _audit_symphony_logic(
    self,
    strategy: Strategy,
    charter: Charter,
    market_context: dict,
    model: str = DEFAULT_MODEL
) -> SymphonyLogicAuditResult:
```

### File: `/Users/ben/dev/ai-hedge-fund/src/agent/stages/composer_deployer.py`
**Line**: Before 581 (in `_deploy_once()`)
**Method**: New async method `_audit_symphony_logic_for_deployment()`
**Signature**:
```python
async def _audit_symphony_logic_for_deployment(
    self,
    strategy: Strategy,
    market_context: dict
) -> List[str]:
```

---

## Code References

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Workflow orchestration | `src/agent/workflow.py` | 74-380 | Stage sequencing, checkpoint management |
| Candidate generation | `src/agent/stages/candidate_generator.py` | 178-438 | Generate & validate 5 candidates |
| Semantic validation | `src/agent/stages/candidate_generator.py` | 977-1165 | Thesis-logic_tree coherence checks |
| Strategy model | `src/agent/models.py` | 70-250 | Strategy definition, Pydantic validators |
| Charter generation | `src/agent/stages/charter_generator.py` | 26-200 | Generate charter document |
| Deployment | `src/agent/stages/composer_deployer.py` | 463-608 | Deploy to Composer |
| Symphony JSON builder | `src/agent/stages/composer_deployer.py` | 305-395 | Build Composer JSON (no LLM hallucination) |
| IF structure builder | `src/agent/stages/composer_deployer.py` | 204-302 | Convert logic_tree to Composer IF nodes |

---

## Documents Created

1. **SYSTEMS_ANALYSIS_VALIDATION_FLOW.md** (this analysis)
   - Complete validation flow mapping
   - Data flow through stages
   - Validation gaps identified
   - Recommended hybrid approach with invariants

2. **EXECUTION_FLOW_DETAILED.md**
   - Line-by-line execution trace
   - Entry/exit points for each stage
   - Data structures involved
   - Checkpoint/resume flow

3. **SYMPHONY_LOGIC_AUDIT_INTEGRATION.md**
   - Specific implementation code
   - Method signatures and docstrings
   - Check implementations with examples
   - Testing templates
   - Error message examples
   - Implementation checklist

---

## Risk Assessment

### Current Risks (Without Audit)
| Risk | Likelihood | Impact | After Audit |
|------|------------|--------|-------------|
| Logically broken condition (never triggers) | Medium | High | Stage 4 detects + warns |
| Invalid condition syntax for Composer | Low | High | Stage 5 blocks |
| Branch assets don't match scenario | Low | Medium | Stage 4 detects + warns |

### Residual Risks (With Hybrid Audit)
| Risk | Stage 4 Audit | Stage 5 Audit | Residual |
|------|--------------|--------------|----------|
| Dead logic in current regime | Warns | Confirms | Low (warned before deploy) |
| Composer API schema violation | Detects | Blocks | Minimal (prevents API failure) |
| Market regime changes mid-90days | N/A | N/A | Inherent (requires board meetings) |

---

## Token Cost Impact

### Stage 4 Audit
- Condition validation: ~50 tokens
- Branch completeness: ~50 tokens
- Asset consistency: ~100 tokens
- Regime applicability: ~200 tokens
- Charter alignment: ~150 tokens
- **Total**: ~550 tokens per workflow (once at Stage 4)

### Stage 5 Audit
- Syntax validation: ~20 tokens
- Asset availability: ~50 tokens
- Weight validation: ~30 tokens
- **Total**: ~100 tokens per workflow (once at Stage 5)

### Overall Impact
- Current workflow: ~52-57k tokens
- With hybrid audit: ~52-58k tokens
- **Increase**: ~1% (negligible)

---

## Implementation Recommendation

### For Immediate Deployment
**Implement Stage 4 audit only** (primary recommendation):
- 2-3 hours of work
- Provides valuable context-aware warnings
- Non-blocking (doesn't halt workflow)
- Low token cost
- Easy to test and iterate

### For Production Hardening
**Add Stage 5 safety gate later**:
- 1-2 additional hours of work
- Provides final safety before Composer API
- Prevents deployment failures
- Can be added independently

### Phase 1 (Immediate)
1. Implement `_audit_symphony_logic()` in CharterGenerator
2. Run full workflow tests with conditional strategies
3. Verify warnings are helpful and actionable
4. Monitor token usage

### Phase 2 (After Phase 1 Stable)
1. Implement `_audit_symphony_logic_for_deployment()` in ComposerDeployer
2. Test deployment blocking scenarios
3. Verify checkpoint/resume works with blocked deployments
4. Document recovery procedures

---

## Next Steps

1. **Review this analysis** with domain expert (Ben)
2. **Choose implementation approach**:
   - Stage 4 only (recommended immediate)
   - Stage 4 + Stage 5 hybrid (recommended long-term)
3. **Create implementation branch** from `SYMPHONY_LOGIC_AUDIT_INTEGRATION.md`
4. **Implement and test** one audit method at a time
5. **Deploy to production** with monitoring
6. **Iterate based on feedback** from real strategies

---

## Questions for Follow-up

1. Should Stage 4 audit have severity levels (warning vs info)?
2. Should warnings trigger retries in Stage 4 or just inform?
3. What constitutes a "dead logic" condition that should be flagged?
4. Should Stage 5 audit be async or sync (simpler, faster)?
5. How should failed Stage 5 deployments be communicated to stakeholders?

---

## Appendix: File Path Reference

All absolute file paths for reference:

- `/Users/ben/dev/ai-hedge-fund/src/agent/workflow.py` - Main orchestration
- `/Users/ben/dev/ai-hedge-fund/src/agent/stages/candidate_generator.py` - Stage 1
- `/Users/ben/dev/ai-hedge-fund/src/agent/stages/edge_scorer.py` - Stage 2
- `/Users/ben/dev/ai-hedge-fund/src/agent/stages/winner_selector.py` - Stage 3
- `/Users/ben/dev/ai-hedge-fund/src/agent/stages/charter_generator.py` - Stage 4 (insertion point)
- `/Users/ben/dev/ai-hedge-fund/src/agent/stages/composer_deployer.py` - Stage 5 (insertion point)
- `/Users/ben/dev/ai-hedge-fund/src/agent/models.py` - Data models
- `/Users/ben/dev/ai-hedge-fund/src/agent/persistence.py` - Checkpoint management

---

**Research Completed By**: Systems Researcher Agent
**Task ID**: 8EYHvJ3sC-PtLLiuqz2my
**Date**: 2025-12-30
