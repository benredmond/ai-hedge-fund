# Systems Analysis: Validation Flow & Symphony Logic Audit Insertion Point

**Research Task**: Map validation stages in strategy creation workflow and identify optimal insertion point for Symphony Logic Audit.

**Status**: Complete research analysis with architectural recommendations

---

## Executive Summary

The validation system operates across **two major phases**:

1. **Phase 1: Candidate Generation (Stage 1)**
   - Location: `src/agent/stages/candidate_generator.py:_validate_semantics()`
   - Scope: All 5 candidates validated simultaneously
   - Focus: Structural correctness (syntax, weights, logic_tree coherence)
   - Timing: Pre-selection (before Edge Scoring)

2. **Phase 2: Deployment (Stage 5)**
   - Location: `src/agent/stages/composer_deployer.py:_deploy_once()` → `_build_symphony_json()` → `_build_if_structure()`
   - Scope: Single winner strategy only
   - Focus: Symphony schema compliance
   - Timing: Post-charter (immediately before Composer API call)

**Key Finding**: Symphony Logic Audit should run **between Charter Generation (Stage 4) and Deployment (Stage 5)** to catch semantic issues that structural validation misses, with optional re-insertion in CandidateGenerator for early warnings.

---

## Execution Flow: Complete Validation Chain

### Stage 1: Candidate Generation
**File**: `/Users/ben/dev/ai-hedge-fund/src/agent/workflow.py:186-222`

```
Entry Point: workflow.py line 189
  └─> candidates = await candidate_gen.generate(market_context, model)

      Inside CandidateGenerator.generate():
      └─> Line 700: validation_errors = self._validate_semantics(candidates, market_context)
          │
          └─> _validate_semantics() runs 6 checks (lines 977-1165):
              1. Syntax validation (line 1000)
                 └─> weights sum to 1.0
                 └─> logic_tree structure correct if non-empty
                 └─> all assets in logic_tree exist in global list

              2. Concentration validation (line 1004)
                 └─> single asset not >30% (unless HIGH_CONVICTION)
                 └─> sector not >50% (unless SECTOR_FOCUS)
                 └─> minimum 2 assets (unless HIGH_CONVICTION)

              3. Leverage justification (line 1008)
                 └─> 2x/3x ETF usage explained in thesis
                 └─> convexity/decay/drawdown/benchmark analysis

              4. Archetype-logic_tree coherence (line 1012)
                 └─> momentum + rotation claims → logic_tree required
                 └─> volatility archetype → logic_tree typically required

              5. Thesis-logic_tree value coherence (line 1016)
                 └─> thesis numeric thresholds match logic_tree.condition
                 └─> VIX > 25 in thesis ≈ VIX > 30 in logic_tree (±20% tolerance)

              6. Weight derivation coherence (line 1020)
                 └─> weights not arbitrary round numbers
                 └─> weights match thesis justification
```

**Output**: List of validation errors (empty if all pass)
- If errors: LLM retry with detailed fix guidance
- If pass: Candidates proceed to Stage 2 (Edge Scoring)

**Critical Detail** (line 425-438):
```python
validated_candidates = []
for candidate in candidates:
    errors = self._validate_semantics([candidate], market_context)
    if errors:
        # Retry with guidance
        candidate = await self._retry_single_candidate(...)
    validated_candidates.append(candidate)
```

---

### Stage 2: Edge Scoring
**File**: `/Users/ben/dev/ai-hedge-fund/src/agent/workflow.py:224-263`

```
Entry Point: workflow.py line 228-231
  └─> scoring_tasks = [edge_scorer.score(candidate, ...) for candidate in candidates]
  └─> scorecards = await asyncio.gather(*scoring_tasks)

      No validation here - purely evaluation of strategic quality
      (thesis quality, edge economics, risk framework, etc.)
```

**No validation logic inserted here** - this stage is pure scoring/evaluation.

---

### Stage 3: Winner Selection
**File**: `/Users/ben/dev/ai-hedge-fund/src/agent/workflow.py:265-289`

```
Entry Point: workflow.py line 268
  └─> winner, reasoning = await selector.select(candidates, scorecards, ...)

      Uses composite ranking:
      1. Edge Scorecard scores (50%)
      2. LLM multi-factor evaluation (50%)
```

**No validation logic here** - this is selection/reasoning only.

---

### Stage 4: Charter Generation
**File**: `/Users/ben/dev/ai-hedge-fund/src/agent/workflow.py:291-321`

```
Entry Point: workflow.py line 294
  └─> charter = await charter_gen.generate(winner, reasoning, ...)

      Location: src/agent/stages/charter_generator.py:40-200

      Input to charter_gen:
      - winner: Strategy object (already passed Stage 1 validation)
      - reasoning: SelectionReasoning (why this candidate)
      - candidates: All 5 (for comparison context)
      - scorecards: All 5 Edge Scorecards
      - market_context: Market regime data

      Charter references logic_tree (line 81):
      selection_context["winner"]["logic_tree"] = winner.logic_tree
```

**Data Available at This Stage**:
- `winner.logic_tree` (guaranteed syntactically valid from Stage 1)
- `winner.thesis_document` (now finalized, won't change)
- `winner.assets` and `winner.weights` (finalized)
- `winner.rebalance_frequency` (finalized)
- Full market context (regime, benchmarks, events)

**No validation logic here** - this is charter synthesis only.

---

### Stage 5: Deployment
**File**: `/Users/ben/dev/ai-hedge-fund/src/agent/workflow.py:323-357`

```
Entry Point: workflow.py line 326
  └─> symphony_id, deployed_at, strategy_summary = await deployer.deploy(winner, charter, ...)

      Location: src/agent/stages/composer_deployer.py:463-608

      Sub-flow inside deployer.deploy():

      1. Line 491: await self._run_with_retries(...) → _deploy_once()
         │
         2. Line 570: confirmation = await self._get_llm_confirmation(...)
         │   (LLM confirms deployment ready, suggests symphony_name & description)
         │
         3. Line 581: symphony_json = _build_symphony_json(
         │       name=...,
         │       description=...,
         │       tickers=strategy.assets,
         │       rebalance=strategy.rebalance_frequency.value,
         │       logic_tree=strategy.logic_tree  # PASSED HERE
         │   )
         │
         │   Inside _build_symphony_json() (line 305-395):
         │   └─> Check if logic_tree is conditional (lines 333-339)
         │       if has_conditional_logic:
         │           └─> if_node = _build_if_structure(logic_tree, rebalance)
         │               (lines 204-302)
         │
         4. Line 595: response = await _call_composer_api(symphony_json)
         │   └─> Direct API call to Composer (line 402-440)
         │   └─> No LLM hallucination in JSON building
         │
         5. Line 598: symphony_id = self._extract_symphony_id(response)
         └─> Return (symphony_id, deployed_at, description)
```

**Critical Control Point** (line 586):
```python
symphony_json = _build_symphony_json(
    name=confirmation.symphony_name,
    description=confirmation.symphony_description,
    tickers=strategy.assets,
    rebalance=strategy.rebalance_frequency.value,
    logic_tree=strategy.logic_tree,  # <-- LOGIC_TREE PASSED HERE
)
```

**Validation Status**:
- Syntax checked ✓ (Stage 1)
- Structural form validated ✓ (Stage 1)
- Composer schema compliance checked ~ (Stage 5, implicit)

---

## Data Flow: Logic Tree Lifecycle

### Creation Phase (Stage 1: CandidateGenerator)

```
LLM generates Strategy object with:
  - logic_tree: Dict[str, Any]
  - Empty dict {} for static allocation
  - OR full structure for conditional: {
      "condition": "VIX > 25",
      "if_true": {"assets": [...], "weights": {...}},
      "if_false": {"assets": [...], "weights": {...}}
    }

Validation (Stage 1):
  1. Pydantic model validator (models.py:128-150)
     └─> If non-empty: must have {condition, if_true, if_false}
  2. Semantic validation (candidate_generator.py:977-1165)
     └─> Checks thesis-logic_tree coherence
     └─> Validates numeric thresholds match
     └─> Confirms archetype aligns with structure
```

### Charter Phase (Stage 4: CharterGenerator)

```
Charter created with reference to logic_tree:
  selection_context["winner"]["logic_tree"] = winner.logic_tree

Used for strategic narrative but NOT modified:
  - Charter is INFORMATIONAL only
  - Doesn't validate or transform logic_tree
  - References it in "winner" context
```

### Deployment Phase (Stage 5: ComposerDeployer)

```
Deployment converts logic_tree → Composer IF structure:

_build_symphony_json():
  └─> Checks: logic_tree has {condition, if_true, if_false}
  └─> IF CHECK PASSES: Calls _build_if_structure()
      └─> Extracts condition, if_true, if_false branches
      └─> Calls _parse_condition() to extract field names
      └─> Builds branch_assets() for each branch
      └─> Builds weight_node() for each branch
      └─> Returns IF node structure

Composer API receives symphony_json with IF node

FAILURE POINT: If logic_tree is invalid Composer JSON,
it fails at API call (line 595), not earlier.
```

---

## Validation Gaps: Where Symphony Logic Audit Fits

### Gap 1: Semantic Validation in Stage 1 is Limited

**Current validation** (candidate_generator.py:977-1165):
```
✓ Syntax: weights sum to 1.0, keys present
✓ Coherence: thesis mentions "VIX > 25" ≈ logic_tree has "VIX > 25"
✗ Execution Logic: Does condition actually select assets correctly?
✗ Regime Applicability: Does logic activate in realistic market regimes?
✗ Asset Liquidity: Do branch assets support conditional execution?
```

**Why Gap Exists**:
- Symphony Logic Audit requires market context to assess regime
- Semantic validation runs per-candidate in parallel
- Full execution simulation would be expensive in Stage 1

### Gap 2: Deployment Assumes logic_tree is Correct

**Current deployment** (composer_deployer.py:581-608):
```
Line 581-587: _build_symphony_json(logic_tree=strategy.logic_tree)
              └─> Trusts logic_tree is valid
              └─> Converts to Composer JSON

Line 595: response = await _call_composer_api(symphony_json)
          └─> If JSON is malformed, Composer API fails
          └─> No human-readable error at this stage
```

**Why Gap Exists**:
- Deployment is point of no return
- Logic_tree came from Stage 1 validation (assumed correct)
- No semantic re-check before expensive API call

---

## Optimal Insertion Points for Symphony Logic Audit

### Option A: Insert in Stage 1 (CandidateGenerator) - EARLY WARNING

**Location**: `candidate_generator.py:_validate_semantics()` after line 1021

```python
def _validate_semantics(self, candidates: List[Strategy], market_context: dict):
    # ... existing validation code (lines 1000-1021)

    # NEW: Run Symphony Logic Audit for all candidates with logic_tree
    for idx, strategy in enumerate(candidates, 1):
        if strategy.logic_tree:  # Only audit conditional strategies
            logic_audit_errors = self._audit_symphony_logic(
                strategy=strategy,
                market_context=market_context,
                stage="candidate_generation"
            )
            errors.extend(logic_audit_errors)

    return errors
```

**Pros**:
- Catches logic errors early before selection/charter
- Allows retry with full context while candidate is being refined
- Provides concrete feedback ("condition never triggers in current regime")

**Cons**:
- Expensive: runs audit on all 5 candidates (parallel execution helps)
- May reject valid strategies that only work in future regimes
- Could increase token usage significantly

**When to use**: If you want strict early validation and don't mind higher costs

---

### Option B: Insert in Stage 4 (CharterGenerator) - OPTIMAL

**Location**: New method in `charter_generator.py` after `generate()` completes

```python
class CharterGenerator:
    async def generate(self, winner, reasoning, candidates, scorecards, market_context, model):
        charter = await self._generate_charter_document(...)

        # NEW: Audit symphony logic before returning
        if winner.logic_tree:
            audit_result = await self._audit_symphony_logic(
                strategy=winner,
                charter=charter,
                market_context=market_context,
                model=model
            )

            if not audit_result.is_valid:
                # Log warnings but don't block
                print(f"⚠️  Symphony Logic Audit warnings for {winner.name}:")
                for warning in audit_result.warnings:
                    print(f"  - {warning}")

        return charter
```

**Pros**:
- Audit runs on single winner only (efficient)
- Has full charter context (failure modes, expected behavior)
- Can correlate logic with charter's regime analysis
- Still before deployment (can inform deployment-time decisions)
- Low token cost (single strategy, after major work done)

**Cons**:
- Runs after selection (can't retry candidates)
- Only catches issues too late to fix easily

**When to use**: Recommended - good balance of safety and efficiency

---

### Option C: Insert in Stage 5 (ComposerDeployer) - LATE SAFETY GATE

**Location**: `composer_deployer.py:_deploy_once()` before `_build_symphony_json()`

```python
async def _deploy_once(self, strategy, charter, market_context, model):
    confirmation = await self._get_llm_confirmation(...)

    # NEW: Final symphony logic audit before building JSON
    if strategy.logic_tree:
        audit_errors = await self._audit_symphony_logic_for_deployment(
            strategy=strategy,
            market_context=market_context
        )

        if audit_errors:
            print(f"❌ Symphony Logic Audit FAILED for {strategy.name}:")
            for error in audit_errors:
                print(f"  - {error}")
            return None, None, None  # Block deployment

    # Continue with deployment...
    symphony_json = _build_symphony_json(...)
```

**Pros**:
- Final safety gate before Composer API
- Prevents deployment of logically broken strategies
- Catches issues created during charter generation

**Cons**:
- Too late to fix (workflow already complete)
- Would require restarting from Stage 4 or earlier
- Blocks deployment without recovery path

**When to use**: If you want to prevent bad deployments but accept that it halts workflow

---

## Recommended Architecture: Hybrid Approach

**Recommendation**: **Option B (Charter Stage) as primary + Option C (Deployment) as safety gate**

### Implementation Plan

1. **Stage 4: Charter Generation** (Primary Audit)
   - Location: `charter_generator.py` after charter synthesis
   - Non-blocking: Logs warnings but continues
   - Provides context-aware validation with full charter
   - Allows graceful degradation

2. **Stage 5: Deployment** (Safety Gate)
   - Location: `composer_deployer.py` before `_build_symphony_json()`
   - Blocking: Prevents deployment if critical issues
   - Acts as final guard against Composer API failures
   - Returns None, None, None to halt (can be resumed from Stage 4)

### Data Available at Each Stage

| Data | Stage 1 | Stage 4 | Stage 5 |
|------|---------|---------|---------|
| `strategy.logic_tree` | ✓ (syntactically valid) | ✓ (unchanged) | ✓ (unchanged) |
| `strategy.assets` | ✓ | ✓ | ✓ |
| `strategy.weights` | ✓ | ✓ | ✓ |
| `strategy.thesis_document` | ✓ (may need retry) | ✓ (finalized) | ✓ (finalized) |
| `charter` | ✗ | ✓ (full document) | ✓ (finalized) |
| `market_context` | ✓ (regime, events) | ✓ | ✓ |
| Can modify strategy? | ✓ (via retry) | ✗ (read-only) | ✗ (read-only) |
| Can modify charter? | N/A | ✓ (in progress) | ✗ (finalized) |

---

## Implementation Invariants (Must Preserve)

These constraints must hold after Symphony Logic Audit insertion:

### 1. Stage Ordering Invariant
```
CANDIDATES (Stage 1)
    ↓ validation: _validate_semantics()
    ↓
SCORING (Stage 2)
    ↓ no validation
    ↓
SELECTION (Stage 3)
    ↓ no validation
    ↓
CHARTER (Stage 4)
    ↓ NEW: audit_symphony_logic() [non-blocking]
    ↓
DEPLOYMENT (Stage 5)
    ↓ NEW: audit_symphony_logic_for_deployment() [blocking]
    ↓
COMPLETE
```

### 2. Data Immutability Invariant
- Once Stage 1 validation completes, `strategy.logic_tree` is read-only
- Later stages can audit but cannot modify
- Audit in Stage 4+ cannot trigger strategy retry (would require re-selection)

### 3. Checkpoint Compatibility Invariant
- `WorkflowCheckpoint` stores candidates after Stage 1
- On resume, strategy.logic_tree must match original (integrity check)
- Audit doesn't modify stored state

### 4. Error Propagation Invariant
```
Stage 1: Validation errors → Retry with guidance
Stage 4: Audit warnings → Log and continue
Stage 5: Audit errors → Block deployment, return (None, None, None)
```

### 5. Charter Document Invariant
- Charter references `winner.logic_tree` (read-only)
- Charter is finalized in Stage 4, not modified by audit
- Audit is informational to charter context, not prescriptive

---

## Code Cross-References

### Key Files and Line Numbers

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Workflow orchestration | `src/agent/workflow.py` | 74-380 | Stage sequencing, checkpoint management |
| Candidate generation | `src/agent/stages/candidate_generator.py` | 178-438 | Generate & validate 5 candidates |
| Semantic validation | `src/agent/stages/candidate_generator.py` | 977-1165 | Thesis-logic_tree coherence |
| Strategy model | `src/agent/models.py` | 70-250 | Strategy definition, Pydantic validators |
| Charter generation | `src/agent/stages/charter_generator.py` | 26-200 | Generate charter document |
| Deployment | `src/agent/stages/composer_deployer.py` | 463-608 | Deploy to Composer |
| Symphony JSON builder | `src/agent/stages/composer_deployer.py` | 305-395 | Build Composer JSON (no hallucination) |
| IF structure builder | `src/agent/stages/composer_deployer.py` | 204-302 | Convert logic_tree to Composer IF nodes |
| Condition parser | `src/agent/stages/composer_deployer.py` | ~170 | Parse condition string to field names |

---

## Symphony Logic Audit: Input/Output Contract

### Input Data Required

```python
audit_input = {
    "strategy": Strategy,          # The strategy with logic_tree
    "market_context": dict,        # Current market regime
    "charter": Charter | None,     # Optional: for Stage 4 only
    "stage": Literal["candidate_generation", "charter", "deployment"]
}
```

### Output Format

```python
@dataclass
class SymphonyLogicAuditResult:
    is_valid: bool                          # False if critical issues
    audit_type: Literal["semantic", "deployment"]
    checks_performed: List[str]             # What was audited
    warnings: List[str]                     # Non-blocking issues
    errors: List[str]                       # Blocking issues (deployment stage only)
    regime_applicability: dict = None       # Which regimes activate condition?
    branch_analysis: dict = None            # Per-branch asset analysis
```

### Checks to Perform

1. **Condition Validity**
   - Syntactically parseable (VIX, momentum, drawdown, price ratios)
   - References valid market indicators
   - Thresholds are realistic

2. **Branch Asset Consistency**
   - Both branches have assets
   - Assets overlap not excessive
   - Weights sum to 1.0 in both branches

3. **Regime Applicability** (Stage 4+ only)
   - Condition likely to activate/deactivate in current regime
   - Branches cover bull/bear cases or high/low vol scenarios
   - Not dead logic (condition never triggers)

4. **Deployment Feasibility** (Stage 5 only)
   - All assets deployable to Composer
   - Rebalance frequency matches branch structure
   - No schema violations that would break Composer API

---

## Risk Assessment

### Current Risks (Without Symphony Logic Audit)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| Logically broken condition (never triggers) | Medium | High (strategy doesn't execute intent) | Add Stage 4 audit |
| Invalid condition syntax for Composer | Low | High (deployment fails) | Add Stage 5 audit |
| Branch assets not available in market | Low | Medium (execution error) | Stage 5 audit + market check |
| Weights don't sum to 1.0 in branches | Very Low | High (Composer JSON invalid) | Pydantic validators already catch |

### Residual Risks (With Recommended Audit)

| Risk | Stage 4 Audit | Stage 5 Audit | Residual |
|------|--------------|--------------|----------|
| Dead logic in current regime | Detects | Confirms | Low (warned before deploy) |
| Composer API schema violation | Warns | Blocks | Minimal (gates deployment) |
| Market regime changes mid-90days | N/A | N/A | Inherent (requires board meetings) |

---

## Implementation Checklist

### Before Coding

- [ ] Decide: Option B (Stage 4 only) vs Option B+C (Hybrid)?
- [ ] Define audit check priorities (condition validity, regime applicability, etc.)
- [ ] Design audit result schema and logging format
- [ ] Determine acceptable warning thresholds

### Stage 4 Implementation (charter_generator.py)

- [ ] Add `audit_symphony_logic()` async method
- [ ] After charter synthesis, call audit if `strategy.logic_tree`
- [ ] Log warnings to console, don't modify charter
- [ ] Return charter unchanged
- [ ] Test with conditional and static strategies

### Stage 5 Implementation (composer_deployer.py)

- [ ] Add `audit_symphony_logic_for_deployment()` async method
- [ ] Call before `_build_symphony_json()`
- [ ] If audit.errors: print errors, return (None, None, None)
- [ ] If audit.warnings: print but continue
- [ ] Test failure cases (invalid condition, missing assets)

### Testing

- [ ] Unit tests: audit logic for valid/invalid conditions
- [ ] Integration tests: Stage 4 + Stage 5 together
- [ ] Checkpoint/resume: Verify audit doesn't break persistence
- [ ] End-to-end: Full workflow with conditional strategies

---

## Summary

**Symphony Logic Audit** should be inserted at **Stage 4 (Charter Generation)** as the primary audit with optional blocking gate at **Stage 5 (Deployment)**.

This approach:
1. Catches semantic issues with full charter context
2. Provides useful warnings before deployment
3. Maintains workflow integrity and checkpoint compatibility
4. Offers graceful degradation (warnings don't block Stage 4)
5. Provides final safety gate at Stage 5 without requiring retry

The recommended hybrid approach balances early detection with efficient execution, providing both context-aware validation and final deployment safety.
