# Symphony Logic Audit - Research Documentation Index

Complete systems analysis of validation flow and optimal insertion point for Symphony Logic Audit.

**Research Task**: Map where validation runs in strategy creation workflow and identify optimal insertion point for Symphony Logic Audit.

**Status**: ✅ Complete

**Date**: 2025-12-30

---

## Documents Overview

### 1. RESEARCH_SUMMARY.md (14 KB)
**Start here if you want the executive summary**

Quick reference guide covering:
- Key findings (validation stages, lifecycle, optimal insertion)
- Data flow summary
- Recommended hybrid approach
- Integration points
- Code references
- Risk assessment
- Token cost impact
- Implementation recommendations

**Read time**: 10 minutes
**Audience**: Decision makers, technical leads

---

### 2. SYSTEMS_ANALYSIS_VALIDATION_FLOW.md (23 KB)
**Comprehensive technical analysis**

Detailed mapping of the complete validation system:
- Execution flow (5 stages with line-by-line references)
- Data flow through stages (logic_tree lifecycle)
- Validation gaps identified
- Three insertion point options (A: early, B: recommended, C: safety gate)
- Hybrid approach architecture
- Implementation invariants (5 constraints to preserve)
- Code cross-references

**Read time**: 25 minutes
**Audience**: Architects, senior engineers

---

### 3. EXECUTION_FLOW_DETAILED.md (34 KB)
**Line-by-line execution trace**

Complete walkthrough of workflow execution:
- Entry/exit points for each stage
- Data structures (Strategy, Charter, Checkpoint)
- Validation entry points (3 locations)
- Resume/checkpoint flow
- Symphony Logic Audit integration points (Option B & C)

**Read time**: 30 minutes
**Audience**: Implementers, debuggers

---

### 4. SYMPHONY_LOGIC_AUDIT_INTEGRATION.md (27 KB)
**Implementation guide with code samples**

Ready-to-implement specifications:
- Recommended approach (hybrid: Stage 4 + Stage 5)
- Stage 4 implementation details (method signatures, checks)
- Stage 5 implementation details (blocking audit)
- Audit check implementations (with code examples)
- Testing template (pytest fixtures and cases)
- Error messages and recovery procedures
- Implementation checklist

**Read time**: 40 minutes
**Audience**: Implementers, QA engineers

---

### 5. VALIDATION_FLOW_DIAGRAM.md (33 KB)
**Visual representations**

ASCII diagrams and visualizations:
- Complete workflow with validation points
- Validation intensity heatmap
- Data flow through logic_tree
- Checkpoint/resume flow
- Validation decision tree
- Audit severity matrix
- Recommended insertion visualization
- Data structures at each stage

**Read time**: 20 minutes
**Audience**: Visual learners, documentation consumers

---

## Quick Navigation

### "I want to understand what's happening"
→ Start with **RESEARCH_SUMMARY.md**

### "I need technical details"
→ Read **SYSTEMS_ANALYSIS_VALIDATION_FLOW.md**

### "I'm going to implement this"
→ Follow **SYMPHONY_LOGIC_AUDIT_INTEGRATION.md**

### "I need to trace execution flow"
→ Use **EXECUTION_FLOW_DETAILED.md**

### "I learn better with diagrams"
→ Study **VALIDATION_FLOW_DIAGRAM.md**

---

## Key Findings Summary

### Validation Stages in Workflow

| Stage | Name | Validates | Location | Blocks? |
|-------|------|-----------|----------|---------|
| 1 | Candidate Generation | Syntax, coherence | candidate_generator.py:977 | ✅ YES (retry) |
| 2 | Edge Scoring | (None - evaluation only) | edge_scorer.py | ❌ NO |
| 3 | Winner Selection | (None - reasoning only) | winner_selector.py | ❌ NO |
| 4 | Charter Generation | **← NEW: Symphony Logic** | charter_generator.py | ⚠️ WARN (non-block) |
| 5 | Deployment | **← NEW: Deployment Check** | composer_deployer.py | ✅ YES (block) |

**Note:** `logic_tree` may be empty (static), conditional (`condition/if_true/if_false`), or filter-only (`filter + assets`). Weighting leaves are supported inside conditional branches.

### Optimal Insertion Point

**Recommendation**: **Hybrid Approach (Stage 4 + Stage 5)**

- **Primary**: Stage 4 (Charter Generation) - Non-blocking audit with full context
  - File: `src/agent/stages/charter_generator.py`
  - After line: 117
  - Method: `_audit_symphony_logic()`
  - Cost: ~550 tokens
  - Impact: Warnings logged, workflow continues

- **Safety Gate**: Stage 5 (Deployment) - Blocking validation before API call
  - File: `src/agent/stages/composer_deployer.py`
  - Before line: 581
  - Method: `_audit_symphony_logic_for_deployment()`
  - Cost: ~100 tokens
  - Impact: Errors block deployment, checkpoint preserved

### Why Stage 4 is Optimal

```
✓ Has full charter context (failure modes, expected behavior)
✓ Runs on single winner only (efficient)
✓ Still before deployment (actionable)
✓ Non-blocking (graceful degradation)
✓ Compatible with checkpoint/resume
✓ Low token cost
```

### Data Available at Stage 4

- `strategy.logic_tree` (finalized from Stage 1)
- `strategy.thesis_document` (finalized)
- `charter` (5 sections with failure modes)
- `market_context` (regime, events, benchmarks)
- `selection_reasoning` (why selected)

### What Gets Audited

**Stage 4 Checks** (Non-blocking):
1. Condition Validity - Syntax parseable?
2. Branch Completeness - Assets & weights present?
3. Asset Consistency - Logical for scenario?
4. Regime Applicability - Likely to activate?
5. Charter Alignment - Failure modes mention branches?

**Stage 5 Checks** (Blocking):
1. Composer Compatibility - No AND/OR operators?
2. Asset Availability - All supported by Composer?
3. Weight Validity - Sum to 1.0 per branch?

---

## Implementation Path

### Phase 1 (Immediate - 2-3 hours)
Implement Stage 4 audit in CharterGenerator:

```python
# In charter_generator.py, after line 117:
if winner.logic_tree:
    audit_result = await self._audit_symphony_logic(
        strategy=winner,
        charter=charter,
        market_context=market_context,
        model=model
    )
    # Log warnings, continue
```

### Phase 2 (Optional - 1-2 hours)
Add Stage 5 safety gate in ComposerDeployer:

```python
# In composer_deployer.py, before line 581:
if strategy.logic_tree:
    audit_errors = await self._audit_symphony_logic_for_deployment(
        strategy=strategy,
        market_context=market_context
    )
    if audit_errors:
        return None, None, None  # Block deployment
```

---

## Token Cost Impact

**Current Workflow**: ~52-57k tokens per run

**With Audit**:
- Stage 4 audit: ~550 tokens
- Stage 5 audit: ~100 tokens
- **Total increase**: ~650 tokens (~1.2%)

**Overall**: Negligible impact on token budget

---

## Invariants to Preserve

These constraints must hold after audit insertion:

1. **Stage Ordering**: Stages run sequentially (Candidates → ... → Deployment)
2. **Data Immutability**: Once Stage 1 complete, strategy.logic_tree is read-only
3. **Checkpoint Compatibility**: Audit is metadata only, doesn't affect stored state
4. **Error Propagation**: Stage 1 blocks via retry, Stage 4 warns, Stage 5 blocks deploy
5. **Single Winner**: Only one strategy proceeds past Stage 3

---

## Risk Assessment

### Current Risks (Without Audit)
- Medium: Logically broken condition (never triggers in current regime)
- Low: Invalid condition syntax for Composer
- Low: Branch assets don't match scenario

### Mitigated Risks (With Hybrid Audit)
- Stage 4 detects + warns about logic issues
- Stage 5 prevents Composer API failures
- Residual risk: Minimal (warned before deployment, prevented at API boundary)

---

## References to Key Code

### Workflow Orchestration
- **File**: `/Users/ben/dev/ai-hedge-fund/src/agent/workflow.py`
- **Lines**: 74-380
- **Key functions**: `create_strategy_workflow()`, `_create_checkpoint()`

### Stage 1: Candidate Generation
- **File**: `/Users/ben/dev/ai-hedge-fund/src/agent/stages/candidate_generator.py`
- **Lines**: 178-438 (generate), 977-1165 (validate)
- **Key functions**: `generate()`, `_validate_semantics()`

### Stage 4: Charter Generation
- **File**: `/Users/ben/dev/ai-hedge-fund/src/agent/stages/charter_generator.py`
- **Lines**: 26-230
- **Key function**: `generate()`
- **Insertion point**: After line 117

### Stage 5: Deployment
- **File**: `/Users/ben/dev/ai-hedge-fund/src/agent/stages/composer_deployer.py`
- **Lines**: 463-608 (deploy), 204-302 (if_structure), 305-395 (json_build)
- **Key functions**: `deploy()`, `_deploy_once()`, `_build_symphony_json()`
- **Insertion point**: Before line 581

### Strategy Model
- **File**: `/Users/ben/dev/ai-hedge-fund/src/agent/models.py`
- **Lines**: 70-250
- **Key class**: `Strategy` with `logic_tree` field

---

## FAQ

### Q: Why not implement audit at Stage 1?
**A**: Stage 1 already has structural validation. Stage 4 is better because:
- Has charter context for regime analysis
- Runs on single winner (efficient)
- Semantic checks benefit from full market context

### Q: Can Stage 4 audit block the workflow?
**A**: No - it's non-blocking by design. Warnings are logged but don't halt. This allows graceful degradation.

### Q: What if Stage 5 audit blocks deployment?
**A**: Checkpoint is preserved, allowing retry from Stage 4. No data is lost.

### Q: What about performance?
**A**: Negligible impact (~650 tokens, ~1% of workflow). Stage 4 runs once on single strategy after major work is done.

### Q: Will this break checkpoint/resume?
**A**: No - audit is metadata only. Checkpoint state unchanged.

### Q: Can I implement just Stage 4 without Stage 5?
**A**: Yes - Stage 4 stands alone. Stage 5 is optional, added later for extra safety.

---

## Implementation Checklist

- [ ] Read RESEARCH_SUMMARY.md
- [ ] Review SYSTEMS_ANALYSIS_VALIDATION_FLOW.md (sections 1-3)
- [ ] Choose implementation approach (Stage 4 only vs hybrid)
- [ ] Create implementation branch
- [ ] Code Stage 4 audit (refer to SYMPHONY_LOGIC_AUDIT_INTEGRATION.md)
- [ ] Write unit tests (pytest templates provided)
- [ ] Test with conditional strategies
- [ ] Test with static strategies (should skip audit)
- [ ] Run full workflow end-to-end
- [ ] Test checkpoint/resume
- [ ] Code review
- [ ] Optionally code Stage 5 safety gate
- [ ] Full integration test
- [ ] Deploy and monitor

---

## Document Maintenance

These documents are living specifications. Update when:

1. Workflow stages change (add/remove/reorder)
2. Strategy model changes (new fields)
3. Validation requirements change
4. Composition API changes (new indicators, operators)
5. Token budgets change (new cost estimates)

Last updated: 2025-12-30

---

## Contact & Questions

For clarifications on this analysis:
- Review relevant document sections (use navigation guide above)
- Check specific code examples in SYMPHONY_LOGIC_AUDIT_INTEGRATION.md
- Reference execution traces in EXECUTION_FLOW_DETAILED.md

---

## Document Statistics

| Document | Size | Read Time | Audience |
|----------|------|-----------|----------|
| RESEARCH_SUMMARY.md | 14 KB | 10 min | Decision makers |
| SYSTEMS_ANALYSIS_VALIDATION_FLOW.md | 23 KB | 25 min | Architects |
| EXECUTION_FLOW_DETAILED.md | 34 KB | 30 min | Implementers |
| SYMPHONY_LOGIC_AUDIT_INTEGRATION.md | 27 KB | 40 min | Implementers |
| VALIDATION_FLOW_DIAGRAM.md | 33 KB | 20 min | Visual learners |
| **Total** | **131 KB** | **2 hours** | All levels |

---

**Research Completed**: 2025-12-30
**Task ID**: 8EYHvJ3sC-PtLLiuqz2my
**Status**: ✅ Complete with all deliverables

All documents are ready for implementation planning.
