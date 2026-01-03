# Validation Flow Diagram

Visual representation of validation stages and Symphony Logic Audit insertion points.

---

## Complete Workflow with Validation Points

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STRATEGY CREATION WORKFLOW (5 STAGES)                    │
└─────────────────────────────────────────────────────────────────────────────┘

                              MARKET CONTEXT
                        (Macro, Regime, Events)
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ STAGE 1: CANDIDATE GENERATION (5 candidates in parallel)     │
    │ File: candidate_generator.py                                │
    │ Lines: 178-438                                              │
    ├─────────────────────────────────────────────────────────────┤
    │                                                              │
    │  Generate 5 candidates with distinct personas:              │
    │  • Macro regime strategist                                  │
    │  • Quantitative factor researcher                           │
    │  • Tail risk manager                                        │
    │  • Sector rotation analyst                                  │
    │  • Trend follower                                           │
    │                                                              │
    │  Output: 5 Strategy objects with:                           │
    │  ├─ thesis_document                                         │
    │  ├─ rebalancing_rationale                                   │
    │  ├─ assets, weights                                         │
    │  └─ logic_tree (empty {} or conditional)                    │
    │                                                              │
    │  ┌─ VALIDATION ──────────────────────────────────┐          │
    │  │ _validate_semantics()                          │          │
    │  │ ├─ syntax (weights sum, logic_tree structure)  │          │
    │  │ ├─ concentration (single asset, sector)        │          │
    │  │ ├─ leverage (2x/3x justification)              │          │
    │  │ ├─ archetype (type matches structure)          │          │
    │  │ ├─ thesis-logic coherence (numbers align)      │          │
    │  │ └─ weight derivation (justified, not random)   │          │
    │  │                                                 │          │
    │  │ Result: List[str] errors                        │          │
    │  │ ├─ If errors: Retry with fix guidance          │          │
    │  │ └─ If pass: Proceed to Stage 2                 │          │
    │  └──────────────────────────────────────────────────┘          │
    │                                                              │
    │  CHECKPOINT: Save 5 validated candidates                    │
    │                                                              │
    └─────────────────────────────────────────────────────────────┘
                                  │
                        ✓ 5 candidates validated
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ STAGE 2: EDGE SCORECARD EVALUATION (5 in parallel)          │
    │ File: edge_scorer.py                                        │
    │ Lines: (see workflow.py 224-263)                            │
    ├─────────────────────────────────────────────────────────────┤
    │                                                              │
    │  Score each candidate on 5 dimensions:                      │
    │  ├─ Thesis Quality (clarity, market fit)                    │
    │  ├─ Edge Economics (sustainable advantage)                  │
    │  ├─ Risk Framework (downside protection)                    │
    │  ├─ Regime Awareness (market fit)                           │
    │  └─ Strategic Coherence (logic_tree aligns with thesis)     │
    │                                                              │
    │  Output: 5 EdgeScorecard objects with total_score (0-5)     │
    │                                                              │
    │  NO VALIDATION IN THIS STAGE                                │
    │  (Pure evaluation)                                          │
    │                                                              │
    │  CHECKPOINT: Save 5 scorecards                              │
    │                                                              │
    └─────────────────────────────────────────────────────────────┘
                                  │
                    ✓ 5 candidates scored
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ STAGE 3: WINNER SELECTION                                   │
    │ File: winner_selector.py                                    │
    │ Lines: (see workflow.py 265-289)                            │
    ├─────────────────────────────────────────────────────────────┤
    │                                                              │
    │  Composite ranking: 50% scorecard + 50% LLM eval            │
    │  Select top candidate as winner                             │
    │                                                              │
    │  Output:                                                    │
    │  ├─ winner: Strategy (1 of 5)                               │
    │  └─ reasoning: SelectionReasoning                           │
    │     ├─ why_selected                                         │
    │     ├─ alternatives_rejected                                │
    │     ├─ tradeoffs_accepted                                   │
    │     └─ conviction_level                                     │
    │                                                              │
    │  NO VALIDATION IN THIS STAGE                                │
    │  (Pure reasoning)                                           │
    │                                                              │
    │  CHECKPOINT: Save winner + reasoning                        │
    │                                                              │
    └─────────────────────────────────────────────────────────────┘
                                  │
                      ✓ 1 winner selected
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ STAGE 4: CHARTER GENERATION                                 │
    │ File: charter_generator.py                                  │
    │ Lines: 26-230                                               │
    ├─────────────────────────────────────────────────────────────┤
    │                                                              │
    │  Generate 5-section charter:                                │
    │  ├─ Section 1: Market Thesis (tool-cited)                   │
    │  ├─ Section 2: Strategy Selection (w/ alternatives)         │
    │  ├─ Section 3: Expected Behavior (3 scenarios)              │
    │  ├─ Section 4: Failure Modes (3-8 measurable)              │
    │  └─ Section 5: 90-Day Outlook (milestones)                  │
    │                                                              │
    │  ┌─ NEW: SYMPHONY LOGIC AUDIT (OPTION B) ────────┐          │
    │  │ _audit_symphony_logic() [IF winner.logic_tree] │          │
    │  │                                                 │          │
    │  │ Run 5 checks:                                   │          │
    │  │ ├─ Condition Validity                           │          │
    │  │ ├─ Branch Completeness                          │          │
    │  │ ├─ Asset Consistency                            │          │
    │  │ ├─ Regime Applicability ← With charter context  │          │
    │  │ └─ Charter Alignment ← Failure modes            │          │
    │  │                                                 │          │
    │  │ Result: SymphonyLogicAuditResult                │          │
    │  │ ├─ warnings: List[str] (non-blocking)           │          │
    │  │ ├─ regime_applicability: dict                   │          │
    │  │ └─ checks_performed: List[str]                  │          │
    │  │                                                 │          │
    │  │ Action: Log warnings, continue (non-blocking)   │          │
    │  └──────────────────────────────────────────────────┘          │
    │                                                              │
    │  CHECKPOINT: Save charter                                   │
    │                                                              │
    └─────────────────────────────────────────────────────────────┘
                                  │
                    ✓ Charter created (± warnings)
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ STAGE 5: DEPLOYMENT TO COMPOSER                             │
    │ File: composer_deployer.py                                  │
    │ Lines: 463-608                                              │
    ├─────────────────────────────────────────────────────────────┤
    │                                                              │
    │  Step 1: Get LLM confirmation                               │
    │  ├─ LLM evaluates: ready to deploy?                         │
    │  └─ LLM suggests: symphony_name, description                │
    │                                                              │
    │  ┌─ NEW: SYMPHONY LOGIC AUDIT (OPTION C) ────────┐          │
    │  │ _audit_symphony_logic_for_deployment()         │          │
    │  │ [IF winner.logic_tree]                         │          │
    │  │                                                 │          │
    │  │ Run 3 strict checks:                            │          │
    │  │ ├─ Composer-compatible syntax (no AND/OR)       │          │
    │  │ ├─ All assets available                         │          │
    │  │ └─ Weights valid per branch                     │          │
    │  │                                                 │          │
    │  │ Result: List[str] errors                        │          │
    │  │                                                 │          │
    │  │ IF errors NOT EMPTY:                            │          │
    │  │ └─ BLOCK deployment, return (None, None, None)  │          │
    │  │    (Checkpoint preserved, can retry from Stage 4)         │
    │  │                                                 │          │
    │  │ IF errors EMPTY:                                │          │
    │  │ └─ Continue to Step 2                           │          │
    │  └──────────────────────────────────────────────────┘          │
    │                                                              │
    │  Step 2: Build symphony JSON (Python, no LLM)               │
    │  ├─ If logic_tree: Call _build_if_structure()               │
    │  ├─ Else: Build wt-cash-equal structure                     │
    │  └─ Output: Composer-compatible JSON                        │
    │                                                              │
    │  Step 3: Call Composer API                                  │
    │  ├─ save_symphony(symphony_json)                            │
    │  └─ Return: symphony_id or None                             │
    │                                                              │
    │  Step 4: Extract result                                     │
    │  ├─ If symphony_id: SUCCESS                                 │
    │  │  ├─ CHECKPOINT: Save symphony_id, deployed_at            │
    │  │  └─ Clear checkpoint (workflow complete)                 │
    │  └─ Else: FAIL (return None, None, None)                   │
    │     └─ CHECKPOINT: Preserved for retry                      │
    │                                                              │
    └─────────────────────────────────────────────────────────────┘
                                  │
                 ✓ Symphony deployed OR ⚠️ Deployment blocked
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ FINAL RESULT: WorkflowResult                                │
    │                                                              │
    │  ├─ strategy: Strategy (selected winner)                    │
    │  ├─ charter: Charter (with all 5 sections)                  │
    │  ├─ all_candidates: List[Strategy] (5 total)                │
    │  ├─ scorecards: List[EdgeScorecard] (5 total)               │
    │  ├─ selection_reasoning: SelectionReasoning                 │
    │  ├─ symphony_id: str (or None)                              │
    │  ├─ deployed_at: str ISO timestamp (or None)                │
    │  └─ strategy_summary: str (or None)                         │
    │                                                              │
    │  PERSISTENCE: Save to data/cohorts/{cohort_id}/strategies.json
    │                                                              │
    └─────────────────────────────────────────────────────────────┘
```

---

## Validation Intensity Heatmap

```
STAGE      EFFORT      VALIDATES                BLOCKS?  CONTEXT
─────────────────────────────────────────────────────────────────
1          HIGH        Syntax, structure         YES      Single candidate
           (per 5x)    Semantic coherence                 (parallel)

2          MEDIUM      (None - pure scoring)     NO       All 5 candidates
           (per 5x)

3          MEDIUM      (None - pure reasoning)   NO       All 5 candidates

4          MEDIUM      ← NEW: Logic semantics    NO       Single winner +
           (per 1x)    ← Charter alignment              charter context

5          LOW         ← NEW: Composer schema    YES      Single winner
           (per 1x)    ← Deployment readiness          (gate only)
```

---

## Data Flow: logic_tree Through Workflow

```
┌────────────┐
│ AI Agent   │
│ (Stage 1)  │
└──────┬─────┘
       │
       │ Generates Strategy with:
       │ • logic_tree = {} (static) or
       │ • logic_tree = {condition, if_true, if_false} (dynamic)
       │
       ▼
┌────────────────────────────────┐
│ PYDANTIC VALIDATION            │
│ (models.py:128-150)            │
│                                │
│ If non-empty:                  │
│ ├─ Must have required keys     │
│ ├─ if_true has assets/weights  │
│ └─ if_false has assets/weights │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ SEMANTIC VALIDATION            │
│ (candidate_generator.py:977)   │
│                                │
│ ├─ Thesis-value coherence      │
│ ├─ Archetype alignment         │
│ ├─ Weight derivation           │
│ └─ Branch completeness         │
└────────┬───────────────────────┘
         │
         ├─ Errors? Retry ──────────────────────┐
         │                                      │
         └─ Pass ─────────────────────────────────────┐
                                                     │
                          ┌─ Stage 1 ─┐              │
                          │ Complete  │◄─────────────┘
                          └────┬──────┘
                               │
                               │ Strategy.logic_tree
                               │ (unchanged)
                               │
                          ┌────▼──────┐
                          │ Stage 2-3  │ (no validation)
                          └────┬──────┘
                               │
                               │ winner.logic_tree
                               │ (unchanged)
                               │
                          ┌────▼──────────────────┐
                          │ Stage 4: Charter Gen  │
                          │                       │
                          │ NEW: Audit ─────────┐ │
                          │ ├─ Regime analysis  │ │
                          │ ├─ Charter align    │ │
                          │ └─ Warnings only    │ │
                          │                     │ │
                          └────┬────────────────┘ │
                               │                  │
                               │ Charter          │
                               │ (references      │
                               │  logic_tree)     │
                               │                  │
                          ┌────▼──────────────────┐
                          │ Stage 5: Deployment   │
                          │                       │
                          │ NEW: Audit ──────────┐│
                          │ ├─ Composer syntax   ││
                          │ ├─ Asset availability││
                          │ └─ Block if invalid  ││
                          │                      ││
                          ├─ Pass audit ────────┐││
                          │                     │││
                          │ _build_symphony_json()
                          │ ├─ _build_if_structure()
                          │ │  └─ _parse_condition()
                          │ │  └─ Extract assets/weights
                          │ │
                          │ └─ Output Composer JSON
                          │
                          ├─ Call Composer API
                          │
                          └─ DEPLOYED (symphony_id)
```

---

## Checkpoint/Resume Flow with Audit

```
SCENARIO: Workflow fails at Stage 4 (Charter generation)

Initial Run:
  Stage 1 ✓ → Checkpoint saved
  Stage 2 ✓ → Checkpoint saved
  Stage 3 ✓ → Checkpoint saved
  Stage 4 ✓ → Checkpoint saved (+ NEW audit warnings logged)
  Stage 5 ✗ → ERROR

Resume:
  checkpoint.load(cohort_id)
    ├─ last_completed_stage = CHARTER
    ├─ candidates = [5 strategies]
    ├─ winner = selected strategy
    ├─ charter = generated charter
    └─ symphony_id = None (not yet deployed)

  create_strategy_workflow(..., resume_checkpoint=checkpoint)
    ├─ resume_stage = DEPLOYMENT (next stage)
    │
    ├─ Skip Stage 1: Use checkpoint.candidates
    ├─ Skip Stage 2: Use checkpoint.scorecards
    ├─ Skip Stage 3: Use checkpoint.winner + reasoning
    ├─ Skip Stage 4: Use checkpoint.charter
    │  └─ Note: Audit already ran on initial creation
    │            No need to re-run (warnings already logged)
    │
    └─ Run Stage 5: Deployment
       ├─ Run NEW audit (validation check)
       ├─ If errors: Block, return (None, None, None)
       ├─ If OK: Proceed to deployment
       └─ DEPLOYED

KEY POINT: Audit in Stage 4 doesn't affect checkpoint/resume.
           Audit is metadata/logging, not part of strategy state.
```

---

## Validation Decision Tree

```
                    ┌─ STRATEGY INPUT
                    │
         ┌──────────▼─────────────┐
         │ Has logic_tree?        │
         │ (not empty dict)       │
         └──┬───────────┬──────────┘
            │ NO        │ YES
            │           │
      ┌─────▼──┐    ┌───▼─────────────────────┐
      │ STATIC │    │ CONDITIONAL             │
      │        │    │                         │
      │ Skip   │    ├─ Stage 1: Syntax check  │
      │ audit  │    │ └─ Required keys        │
      │        │    │ └─ Asset/weight vals    │
      │        │    │                         │
      │        │    ├─ Stage 1: Semantic      │
      │        │    │ └─ Thesis-value match   │
      │        │    │ └─ Archetype alignment  │
      │        │    │                         │
      │        │    ├─ Stage 4: Smart audit   │
      │        │    │ └─ Regime applicability │
      │        │    │ └─ Charter alignment    │
      │        │    │ └─ Asset consistency    │
      │        │    │ └─ WARNINGS (no block)  │
      │        │    │                         │
      │        │    └─ Stage 5: Strict audit  │
      │        │      └─ Composer syntax      │
      │        │      └─ Asset availability   │
      │        │      └─ ERRORS (blocks)      │
      │        │                             │
      └─────┬─┴───────────┬────────────────────┘
            │ ALL PASS    │ FAIL
            │             │
      ┌─────▼─────┐ ┌─────▼────────┐
      │ DEPLOY    │ │ BLOCK        │
      │ (Static   │ │ (Conditional)│
      │  or       │ │ RETRY (S1)   │
      │  Valid)   │ │ HALT (S4/5)  │
      │           │ │              │
      └───────────┘ └──────────────┘
```

---

## Audit Severity Matrix

```
AUDIT        STAGE    TIMING              SEVERITY    ACTION
─────────────────────────────────────────────────────────────
Syntax       1        Stage 1             BLOCKING    Retry
Coherence    1        Stage 1             BLOCKING    Retry

Regime Fit   4        Stage 4 (charter)   WARNING     Log only
Alignment    4        Stage 4 (charter)   WARNING     Log only
Consistency  4        Stage 4 (charter)   WARNING     Log only

Composer     5        Stage 5 (deploy)    BLOCKING    Return None
Syntax                                                 (halt)

Assets       5        Stage 5 (deploy)    BLOCKING    Return None
Available                                             (halt)
```

---

## Recommended Insertion Visualization

```
CURRENT WORKFLOW (Without Audit)
═════════════════════════════════════

Stage 1: Generate ─► Validate ─┐
                                │
Stage 2: Score ◄────────────────┘
           │
Stage 3: Select
           │
Stage 4: Charter
           │
Stage 5: Deploy ──► Composer API ──► (May fail here)
           │
           └─► Result


HYBRID WORKFLOW (WITH AUDIT) - RECOMMENDED
════════════════════════════════════════════════

Stage 1: Generate ─► Validate (Syntax, Semantic) ─┐
                                                   │
Stage 2: Score ◄──────────────────────────────────┘
           │
Stage 3: Select
           │
Stage 4: Charter ─► Audit (Regime, Alignment) ─┐ (Warnings only)
           │                                     │
           └─────────────────────────────────────┘
           │
Stage 5: Deploy ─► Audit (Composer Schema) ─┐ (Blocks if error)
           │                                 │
           ├─ If OK: Build JSON ────────────┘
           │         │
           │         └─► Composer API ──► (Unlikely to fail)
           │
           └─► Result
```

---

## Data Structures at Each Stage

```
┌─────────────┬──────────────────┬──────────────┬─────────────────┐
│ Stage       │ Input Type       │ Validation   │ Output Type     │
├─────────────┼──────────────────┼──────────────┼─────────────────┤
│ 1: Generate │ (none - prompt)  │ ✓ Semantic   │ Strategy[5]     │
│             │                  │             │ + errors list   │
├─────────────┼──────────────────┼──────────────┼─────────────────┤
│ 2: Score    │ Strategy[5]      │ (none)       │ EdgeScorecard[5]│
├─────────────┼──────────────────┼──────────────┼─────────────────┤
│ 3: Select   │ Strategy[5]      │ (none)       │ Strategy (1)    │
│             │ EdgeScorecard[5] │             │ + SelectReason  │
├─────────────┼──────────────────┼──────────────┼─────────────────┤
│ 4: Charter  │ Strategy (1)     │ ✓ NEW Audit  │ Charter         │
│             │ SelectReason     │ (warnings)   │ + audit result  │
│             │ Charter (draft)  │             │                 │
├─────────────┼──────────────────┼──────────────┼─────────────────┤
│ 5: Deploy   │ Strategy (1)     │ ✓ NEW Audit  │ symphony_id     │
│             │ Charter          │ (errors OK)  │ or None         │
└─────────────┴──────────────────┴──────────────┴─────────────────┘
```

---

## Summary: Why Stage 4 is Optimal

```
                  STAGE 1    STAGE 4    STAGE 5
                  ────────────────────────────
Costs             ✓ HIGH      ✓ MEDIUM   ✓ LOW
                  (5 cands)   (1 cand)   (1 cand)

Context Available
  • Strategy      ✓ YES       ✓ YES      ✓ YES
  • Charter       ✗ NO        ✓ YES      ✓ YES
  • Market data   ✓ YES       ✓ YES      ✓ YES

Can Modify        ✓ YES       ✗ NO       ✗ NO
Strategy?

Can Block         ✓ YES       ✗ NO       ✓ YES
Workflow?         (via retry) (warnings) (block deploy)

Regime Analysis   ✓ NO        ✓ YES      ✓ MAYBE
Feasible?         (early)     (full)     (limited)

RECOMMENDATION   Stage 1     OPTIMAL    Safety gate
                 (existing)   (add)      (optional)
```

---

**Visual Summary**: Stage 4 (Charter Generation) is optimal for Symphony Logic Audit because it provides full context (charter, market data, selected strategy) while still being before deployment, and runs efficiently on a single strategy. Stage 5 (Deployment) serves as a safety gate to prevent Composer API failures.
