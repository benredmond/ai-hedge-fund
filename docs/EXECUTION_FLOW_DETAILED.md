# Detailed Execution Flow: Strategy Creation Workflow

Complete data flow with line-by-line references for Symphony Logic Audit integration.

---

## Complete Workflow Execution Sequence

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: CANDIDATE GENERATION (5 strategies in parallel)                    │
│ File: src/agent/workflow.py:186-222                                        │
│ File: src/agent/stages/candidate_generator.py:178-438                      │
└─────────────────────────────────────────────────────────────────────────────┘

Entry point:
  workflow.py:189
  ├─> candidates = await candidate_gen.generate(market_context, model)
  │
  └─> Inside CandidateGenerator.generate():
      ├─> Load system & recipe prompts (lines 1940-1960)
      │
      ├─> For each of 5 PROMPT_VARIATIONS (parallel execution):
      │   ├─> Call create_agent() with variation's persona
      │   ├─> Agent runs with optional tool calls (Composer, yfinance, FRED)
      │   └─> AI outputs Strategy object (JSON/Pydantic)
      │
      ├─> Quality scoring loop (lines 420-438):
      │   ├─> FOR each candidate:
      │   │   ├─> _evaluate_quality_score() (lines 440-520)
      │   │   │   └─> Returns QualityScore with 5 dimensions:
      │   │   │       - quantification (has Sharpe/alpha?)
      │   │   │       - coherence (thesis matches implementation?)
      │   │   │       - edge_frequency (archetype matches rebalancing?)
      │   │   │       - diversification (concentration risk?)
      │   │   │       - syntax (structure valid?)
      │   │   │
      │   │   └─> IF quality score < 0.6 OR any dimension < 0.3:
      │   │       └─> RETRY_LOOP (lines 548-730):
      │   │           ├─> Build fix prompt with validation_errors
      │   │           ├─> Agent retries with corrective guidance
      │   │           ├─> Validate data integrity preserved
      │   │           └─> MAX 2 retries per candidate
      │   │
      │   └─> END: Collect validated_candidates (5 total)
      │
      └─> RETURN: List[Strategy] (line 438)

VALIDATION IN STAGE 1:
  Line 425: errors = self._validate_semantics([candidate], market_context)
  │
  └─> _validate_semantics() runs 6 checks per candidate:
      Line 1000: _validate_syntax(strategy)
      │          └─> Check: weights sum ~1.0 (±0.01)
      │          └─> Check: logic_tree is conditional or filter leaf if non-empty
      │          └─> Check: all assets in logic_tree exist in global list
      │
      Line 1004: _validate_concentration(strategy)
      │          └─> Check: single asset not >30% (unless HIGH_CONVICTION)
      │          └─> Check: sector not >50% (unless SECTOR_FOCUS)
      │          └─> Check: min 2 assets (unless HIGH_CONVICTION)
      │
      Line 1008: _validate_leverage_justification(strategy)
      │          └─> Check: 2x/3x ETF use explained in thesis
      │          └─> Check: convexity/decay/drawdown/benchmark analysis
      │
      Line 1012: _validate_archetype_logic_tree(strategy, idx)
      │          └─> Check: momentum + rotation → logic_tree required
      │          └─> Check: volatility archetype → logic_tree typically required
      │
      Line 1016: _validate_thesis_logic_tree_coherence(strategy, idx)
      │          └─> Check: thesis VIX > 25 ≈ logic_tree VIX > 25 (±20%)
      │          └─> Check: numeric thresholds align
      │
      Line 1020: _validate_weight_derivation_coherence(strategy, idx)
                 └─> Check: weights not arbitrary round numbers
                 └─> Check: weights match thesis justification

ERROR HANDLING:
  IF validation_errors NOT EMPTY:
    ├─> Build detailed fix_prompt (lines 1540-1690)
    │   ├─> Include error details
    │   ├─> Include schema guidance
    │   ├─> Explain immutable fields (assets, weights can't be added)
    │   └─> Show CORRECT vs WRONG examples
    │
    └─> Retry (lines 700-810):
        ├─> Run _generate_with_retry(fix_prompt)
        ├─> Validate data integrity (fields preserved, assets unchanged)
        └─> IF retry count > 2: Give up, log failure

CHECKPOINT SAVED (if cohort_id provided):
  workflow.py:194-202
  ├─> WorkflowCheckpoint created with:
  │   ├─> last_completed_stage = WorkflowStage.CANDIDATES
  │   ├─> candidates = [list of 5 validated strategies]
  │   ├─> created_at, updated_at timestamps
  │   └─> model identifier
  │
  └─> save_checkpoint(checkpoint, cohort_id)


┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: EDGE SCORECARD EVALUATION (5 strategies in parallel)               │
│ File: src/agent/workflow.py:224-263                                        │
│ File: src/agent/stages/edge_scorer.py                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Entry point:
  workflow.py:227-231
  ├─> scoring_tasks = [edge_scorer.score(candidate, market_context, model)
  │                    for candidate in candidates]
  │
  └─> scorecards = await asyncio.gather(*scoring_tasks)
      │
      └─> For each candidate in parallel:
          ├─> EdgeScorer.score():
          │   ├─> Evaluate thesis_quality (clarity, market fit)
          │   ├─> Evaluate edge_economics (sustainable advantage)
          │   ├─> Evaluate risk_framework (downside protection)
          │   ├─> Evaluate regime_awareness (market fit)
          │   ├─> Evaluate strategic_coherence (logic_tree aligns with thesis)
          │   │
          │   └─> RETURN: EdgeScorecard with 5 scores + total_score
          │
          └─> Parallel execution via asyncio.gather()

NO VALIDATION IN STAGE 2 (Pure scoring/evaluation)

FILTERING AFTER SCORING:
  workflow.py:235-245
  ├─> FOR each scorecard:
  │   ├─> IF scorecard.total_score >= 3.0:
  │   │   └─> passing_indices.append(i)
  │   └─> ELSE:
  │       └─> Print warning with breakdown
  │
  └─> Filter candidates by passing_indices

OUTPUT:
  ├─> scorecards: List[EdgeScorecard] (5 total)
  └─> passing_indices: List[int] (typically 3-5 pass the 3.0 threshold)

CHECKPOINT SAVED (if cohort_id provided):
  workflow.py:250-260
  ├─> WorkflowCheckpoint updated with:
  │   ├─> last_completed_stage = WorkflowStage.SCORING
  │   ├─> candidates = [5 candidates]
  │   ├─> scorecards = [5 scorecards]
  │   └─> updated_at timestamp
  │
  └─> save_checkpoint(checkpoint, cohort_id)


┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: WINNER SELECTION                                                   │
│ File: src/agent/workflow.py:265-289                                        │
│ File: src/agent/stages/winner_selector.py                                  │
└─────────────────────────────────────────────────────────────────────────────┘

Entry point:
  workflow.py:268
  ├─> winner, reasoning = await selector.select(
  │       candidates, scorecards, market_context, model
  │   )
  │
  └─> Inside WinnerSelector.select():
      ├─> Composite ranking:
      │   ├─> 50% from Edge Scorecard scores
      │   ├─> 50% from LLM multi-factor evaluation
      │   └─> Factors: thesis clarity, edge strength, risk management, coherence
      │
      ├─> Rank candidates by composite score
      ├─> Select top candidate as winner
      │
      └─> RETURN:
          ├─> winner: Strategy (1 of 5 candidates)
          └─> reasoning: SelectionReasoning with:
              ├─> winner_index (0-4)
              ├─> why_selected (narrative)
              ├─> tradeoffs_accepted (what we gave up)
              ├─> alternatives_rejected (other options & why)
              └─> conviction_level (0-100)

NO VALIDATION IN STAGE 3 (Pure selection/reasoning)

CHECKPOINT SAVED (if cohort_id provided):
  workflow.py:274-286
  ├─> WorkflowCheckpoint updated with:
  │   ├─> last_completed_stage = WorkflowStage.SELECTION
  │   ├─> candidates = [5 candidates]
  │   ├─> scorecards = [5 scorecards]
  │   ├─> winner = winner strategy
  │   ├─> selection_reasoning = reasoning object
  │   └─> updated_at timestamp
  │
  └─> save_checkpoint(checkpoint, cohort_id)


┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: CHARTER GENERATION                                                 │
│ File: src/agent/workflow.py:291-321                                        │
│ File: src/agent/stages/charter_generator.py:26-230                         │
└─────────────────────────────────────────────────────────────────────────────┘

Entry point:
  workflow.py:294
  ├─> charter = await charter_gen.generate(
  │       winner, reasoning, candidates, scorecards, market_context, model
  │   )
  │
  └─> Inside CharterGenerator.generate():
      │
      ├─ Build selection_context (lines 73-117):
      │  ├─> winner: {name, assets, weights, rebalance_frequency,
      │  │            edge_type, archetype, logic_tree}  ◄── LOGIC_TREE HERE
      │  ├─> reasoning: {winner_index, why_selected, alternatives_rejected, ...}
      │  ├─> edge_scorecard: {thesis_quality, edge_economics, ...}
      │  ├─> all_candidates: [{name, assets, edge_type, archetype, is_winner, ...}]
      │  └─> market_context_summary: {anchor_date, regime_tags, regime_snapshot}
      │
      ├─ Create prompt with:
      │  ├─> System prompt (charter_creation_system_compressed.md)
      │  ├─> Recipe prompt (charter_creation_compressed.md)
      │  ├─> Selection context (JSON serialized)
      │  └─> Task instructions (Phase 1-2)
      │
      ├─ Call agent.run() with:
      │  ├─> Available tools: fred_get_series, stock_get_historical_stock_prices
      │  ├─> Instructions to ground Market Thesis in tool data
      │  └─> LLM generates Charter object
      │
      ├─ Parse LLM output:
      │  ├─> Section 1: Market Thesis (tool-cited, regime analysis)
      │  ├─> Section 2: Strategy Selection (integration of SelectionReasoning)
      │  ├─> Section 3: Expected Behavior (base/bear/bull cases)
      │  ├─> Section 4: Failure Modes (3-8 measurable conditions)
      │  └─> Section 5: 90-Day Outlook (milestones, red flags)
      │
      │  ◄── INSERTION POINT FOR SYMPHONY LOGIC AUDIT (OPTION B) ────┐
      │  │                                                            │
      │  │  NEW CODE HERE:                                           │
      │  │  if winner.logic_tree:                                    │
      │  │    audit_result = await self._audit_symphony_logic(      │
      │  │        strategy=winner,                                   │
      │  │        charter=charter,                                   │
      │  │        market_context=market_context,                     │
      │  │        model=model                                        │
      │  │    )                                                       │
      │  │    if audit_result.warnings:                              │
      │  │      print(f"⚠️  Audit warnings: {audit_result.warnings}") │
      │  │                                                            │
      └──► RETURN charter (unchanged)
           │
           └─> Charter object with 5 sections (immutable after generation)

NO MODIFICATION TO CHARTER or STRATEGY in audit
(Audit is informational only, doesn't trigger fixes)

CHECKPOINT SAVED (if cohort_id provided):
  workflow.py:305-318
  ├─> WorkflowCheckpoint updated with:
  │   ├─> last_completed_stage = WorkflowStage.CHARTER
  │   ├─> candidates = [5 candidates]
  │   ├─> scorecards = [5 scorecards]
  │   ├─> winner = winner strategy
  │   ├─> selection_reasoning = reasoning object
  │   ├─> charter = charter document
  │   └─> updated_at timestamp
  │
  └─> save_checkpoint(checkpoint, cohort_id)


┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 5: DEPLOYMENT TO COMPOSER                                             │
│ File: src/agent/workflow.py:323-357                                        │
│ File: src/agent/stages/composer_deployer.py:463-608                        │
└─────────────────────────────────────────────────────────────────────────────┘

Entry point:
  workflow.py:326
  ├─> symphony_id, deployed_at, strategy_summary = await deployer.deploy(
  │       winner, charter, market_context, model
  │   )
  │
  └─> Inside ComposerDeployer.deploy():
      │
      ├─ Check Composer credentials (lines 483-488):
      │  ├─> IF not COMPOSER_API_KEY or not COMPOSER_API_SECRET:
      │  │   └─> RETURN (None, None, None)  # Graceful degradation
      │  └─> ELSE: Continue
      │
      ├─ Call _run_with_retries() (line 491):
      │  └─> Exponential backoff retry (max 3 attempts)
      │     └─> On each attempt: call _deploy_once()
      │        │
      │        └─> _deploy_once():
      │           │
      │           ├─ Step 1: Get LLM confirmation (lines 570-578)
      │           │  ├─> _get_llm_confirmation():
      │           │  │   ├─> Agent evaluates strategy for deployment readiness
      │           │  │   ├─> Agent suggests symphony_name & description
      │           │  │   └─> RETURN: SymphonyConfirmation
      │           │  │       {ready_to_deploy, symphony_name, symphony_description}
      │           │  │
      │           │  └─> IF not ready_to_deploy:
      │           │      └─> RETURN (None, None, None)  # Decline to deploy
      │           │
      │           ├─ ◄── INSERTION POINT FOR SYMPHONY LOGIC AUDIT (OPTION C) ────┐
      │           │  │                                                            │
      │           │  │  NEW CODE HERE:                                           │
      │           │  │  if winner.logic_tree:                                    │
      │           │  │    audit_errors = await _audit_symphony_logic_deployment( │
      │           │  │        strategy=winner,                                   │
      │           │  │        market_context=market_context                      │
      │           │  │    )                                                       │
      │           │  │    if audit_errors:                                       │
      │           │  │      print(f"❌ Audit FAILED: {audit_errors}")             │
      │           │  │      return (None, None, None)  # Block deployment        │
      │           │  │                                                            │
      │           │  └─ Continue to Step 2
      │           │
      │           ├─ Step 2: Build symphony JSON (lines 581-587)
      │           │  ├─> _build_symphony_json(
      │           │  │       name=confirmation.symphony_name,
      │           │  │       description=confirmation.symphony_description,
      │           │  │       tickers=strategy.assets,
      │           │  │       rebalance=strategy.rebalance_frequency.value,
      │           │  │       logic_tree=strategy.logic_tree  ◄── PASSED HERE
      │           │  │   )
      │           │  │
      │           │  └─> Inside _build_symphony_json() (lines 305-395):
      │           │      ├─> Check if logic_tree is conditional or filter-only
      │           │      │  ├─> has_conditional_logic = (logic_tree AND
      │           │      │  │                            has {condition, if_true, if_false})
      │           │      │  ├─> has_filter_leaf = (logic_tree AND has {filter, assets})
      │           │      │  │
      │           │      │  └─> IF has_conditional_logic:
      │           │      │      ├─> Call _build_if_structure(logic_tree, rebalance)
      │           │      │      │  │
      │           │      │      │  └─> Inside _build_if_structure() (lines 204-302):
      │           │      │      │      ├─> condition = logic_tree["condition"]
      │           │      │      │      ├─> if_true = logic_tree["if_true"]
      │           │      │      │      ├─> if_false = logic_tree["if_false"]
      │           │      │      │      │
      │           │      │      │      ├─> condition_fields = _parse_condition(condition)
      │           │      │      │      │   └─> Extract: indicator name (VIXY), operator (>), threshold (25)
      │           │      │      │      │
      │           │      │      │      ├─> build_branch_assets(if_true)
      │           │      │      │      │   └─> For each ticker: {id, step, ticker, exchange, weight}
      │           │      │      │      │
      │           │      │      │      ├─> build_weight_node(if_true)
      │           │      │      │      │   └─> wt-cash-equal or wt-inverse-vol node
      │           │      │      │      │
      │           │      │      │      ├─> Build true_branch IF node (if_true, is-else=false)
      │           │      │      │      ├─> Build false_branch IF node (if_false, is-else=true)
      │           │      │      │      │
      │           │      │      │      └─> RETURN IF node structure
      │           │      │      │
      │           │      │      └─> symphony_score = {
      │           │      │          "step": "if",
      │           │      │          "children": [true_branch, false_branch]
      │           │      │      }
      │           │      │
      │           │      └─> ELSE (static strategy):
      │           │          └─> symphony_score = {
      │           │              "step": "wt-cash-equal",
      │           │              "children": [asset nodes for all assets]
      │           │          }
      │           │
      │           │  └─> RETURN symphony_json:
      │           │      {
      │           │          "symphony_score": symphony_score,
      │           │          "color": hex_color,
      │           │          "hashtag": hashtag_id,
      │           │          "asset_class": "EQUITIES" or "CRYPTO"
      │           │      }
      │           │
      │           ├─ Step 3: Call Composer API (lines 594-595)
      │           │  ├─> response = await _call_composer_api(symphony_json)
      │           │  │   │
      │           │  │   └─> Inside _call_composer_api() (lines 402-440):
      │           │  │       ├─> Create Composer MCP server
      │           │  │       ├─> Call server.direct_call_tool("save_symphony", symphony_json)
      │           │  │       │   └─> ACTUAL API CALL TO COMPOSER.TRADE
      │           │  │       │   └─> Returns: {symphony_id, version_id}
      │           │  │       │
      │           │  │       └─> RETURN response dict
      │           │  │
      │           │  └─> IF Composer API call fails:
      │           │      └─> Exception raised, caught by retry handler
      │           │
      │           ├─ Step 4: Extract symphony_id from response (line 598)
      │           │  ├─> symphony_id = self._extract_symphony_id(response)
      │           │  │
      │           │  ├─> IF symphony_id:
      │           │  │   ├─> deployed_at = datetime.now(timezone.utc).isoformat()
      │           │  │   └─> RETURN (symphony_id, deployed_at, description)
      │           │  │
      │           │  └─> ELSE:
      │           │      └─> RETURN (None, None, None)
      │           │
      │           └─> END _deploy_once()
      │
      └─> Retry handler (lines 525-552):
          ├─> IF _deploy_once() raises exception:
          │   ├─> Classify error type
          │   ├─> IF rate limit: wait with exponential backoff (2^attempt)
          │   ├─> IF auth/network: wait 5 seconds
          │   └─> Retry up to 3 times
          │
          └─> IF all retries exhausted: raise exception

DEPLOYMENT SUCCESS CRITERIA:
  ├─> symphony_id is not None (deployment succeeded)
  └─> RETURN (symphony_id, deployed_at, description)

DEPLOYMENT FAILURE CRITERIA:
  ├─> Credentials not set → RETURN (None, None, None)
  ├─> LLM declined → RETURN (None, None, None)
  ├─> Composer API call failed → RETURN (None, None, None)
  ├─> Symphony ID not extracted → RETURN (None, None, None)
  └─> Audit blocked deployment (Option C) → RETURN (None, None, None)

CHECKPOINT SAVED (if cohort_id AND symphony_id):
  workflow.py:335-351
  ├─> WorkflowCheckpoint updated with:
  │   ├─> last_completed_stage = WorkflowStage.DEPLOYMENT
  │   ├─> symphony_id = symphony_id
  │   ├─> deployed_at = deployed_at ISO timestamp
  │   ├─> strategy_summary = strategy_summary
  │   └─> updated_at timestamp
  │
  └─> save_checkpoint(checkpoint, cohort_id)

FINAL RESULT ASSEMBLY:
  workflow.py:360-368
  ├─> WorkflowResult:
  │   ├─> strategy = winner
  │   ├─> charter = charter
  │   ├─> all_candidates = candidates (5 total)
  │   ├─> scorecards = scorecards (5 total)
  │   ├─> selection_reasoning = reasoning
  │   ├─> symphony_id = symphony_id (or None if deployment skipped)
  │   ├─> deployed_at = deployed_at ISO timestamp (or None)
  │   └─> strategy_summary = strategy_summary (or None)
  │
  └─> RETURN WorkflowResult

PERSISTENCE (if cohort_id provided):
  workflow.py:372-378
  ├─> save_workflow_result(result, cohort_id, model=model)
  │   └─> Saves to: data/cohorts/{cohort_id}/strategies.json
  │
  ├─> IF symphony_id:
  │   └─> clear_checkpoint(cohort_id)  # Cleanup on success
  │
  └─> ELSE:
      └─> Preserve checkpoint (can resume from Stage 4)
```

---

## Key Data Structures

### Strategy Object (models.py:70-250)

```python
class Strategy(BaseModel):
    # Reasoning fields
    thesis_document: str = ""  # Investment thesis (0-2000 chars)
    rebalancing_rationale: str  # How rebalancing implements edge (150-1000 chars)

    # Classification fields
    edge_type: EdgeType  # behavioral, structural, informational, risk_premium
    archetype: StrategyArchetype  # momentum, mean_reversion, carry, etc.
    concentration_intent: ConcentrationIntent  # DIVERSIFIED, HIGH_CONVICTION, etc.

    # Execution fields
    name: str  # Strategy identifier (1-200 chars)
    assets: List[str]  # Tickers (1-50 assets)
    logic_tree: Dict[str, Any] = {}  # Conditional logic, filter leaf, or {}
    weights: Dict[str, float]  # Asset allocation (sums to 1.0)
    rebalance_frequency: RebalanceFrequency  # daily, weekly, monthly, quarterly, none

    # VALIDATORS
    @field_validator("logic_tree")
    def logic_tree_valid_structure(cls, v):
        """Non-empty logic_tree must be conditional or a filter leaf."""
        if not v:
            return v  # Empty dict OK for static strategies

        required_keys = {"condition", "if_true", "if_false"}
        if not required_keys.issubset(v.keys()) and "filter" not in v:
            raise ValueError(f"Missing keys: {required_keys - set(v.keys())}")

        # Validate branches have assets and weights
        for branch in ["if_true", "if_false"]:
            branch_data = v[branch]
            assert isinstance(branch_data, dict)
            assert "assets" in branch_data and "weights" in branch_data

        return v
```

### Logic Tree Structure

```python
# STATIC STRATEGY (no conditional logic)
strategy.logic_tree = {}

# CONDITIONAL STRATEGY (dynamic allocation)
strategy.logic_tree = {
    "condition": "VIXY_price > 25",  # Trigger condition (string expression)
    "if_true": {
        "assets": ["QQQ", "TLT"],
        "weights": {"QQQ": 0.7, "TLT": 0.3}
    },
    "if_false": {
        "assets": ["SPY", "IWM", "VEA"],
        "weights": {"SPY": 0.6, "IWM": 0.2, "VEA": 0.2}
    }
}

# FILTER-ONLY STRATEGY (rank/select assets)
strategy.logic_tree = {
    "filter": {"sort_by": "cumulative_return", "window": 30, "select": "top", "n": 2},
    "assets": ["XLK", "XLF", "XLE"]
}
```

### Charter Object (models.py)

```python
class Charter(BaseModel):
    market_thesis: str  # Section 1: Market analysis, regime fit
    strategy_selection: str  # Section 2: Why selected, alternatives rejected
    expected_behavior: str  # Section 3: Base/bear/bull cases, regime transitions
    failure_modes: List[str]  # Section 4: 3-8 measurable failure conditions
    outlook_90d: str  # Section 5: Milestones, red flags, 90-day plan
```

### WorkflowCheckpoint (models.py)

```python
class WorkflowCheckpoint(BaseModel):
    last_completed_stage: WorkflowStage
    created_at: str  # ISO timestamp
    updated_at: str  # ISO timestamp
    model: str  # LLM model used
    cohort_id: str  # Cohort identifier
    market_context: dict  # Original context pack

    # Results from each stage (accumulated)
    candidates: List[Strategy] | None = None  # After Stage 1
    scorecards: List[EdgeScorecard] | None = None  # After Stage 2
    winner: Strategy | None = None  # After Stage 3
    selection_reasoning: SelectionReasoning | None = None  # After Stage 3
    charter: Charter | None = None  # After Stage 4
    symphony_id: str | None = None  # After Stage 5
    deployed_at: str | None = None  # After Stage 5
    strategy_summary: str | None = None  # After Stage 5
```

---

## Validation Entry Points

### Entry Point 1: Stage 1 - CandidateGenerator._validate_semantics()
**File**: `src/agent/stages/candidate_generator.py:977`

```python
def _validate_semantics(self, candidates: List[Strategy], market_context: dict) -> List[str]:
    """
    Validate semantic coherence of candidates.

    Runs 6 checks per candidate:
    1. _validate_syntax() - Structure valid?
    2. _validate_concentration() - Diversification OK?
    3. _validate_leverage_justification() - 2x/3x explained?
    4. _validate_archetype_logic_tree() - Type matches structure?
    5. _validate_thesis_logic_tree_coherence() - Numbers align?
    6. _validate_weight_derivation_coherence() - Weights justified?

    Returns: List[str] of error messages (empty if valid)
    """
```

### Entry Point 2: NEW - Stage 4 - CharterGenerator.audit_symphony_logic()
**Location**: After charter synthesis in `charter_generator.py:generate()`

```python
async def _audit_symphony_logic(
    self,
    strategy: Strategy,
    charter: Charter,
    market_context: dict,
    model: str = DEFAULT_MODEL
) -> SymphonyLogicAuditResult:
    """
    Audit symphony logic with full charter context.

    Non-blocking audit that:
    1. Validates condition syntax
    2. Checks branch asset validity
    3. Assesses regime applicability
    4. Correlates with charter failure modes

    Returns: SymphonyLogicAuditResult with warnings/errors
    """
```

### Entry Point 3: NEW - Stage 5 - ComposerDeployer.audit_symphony_logic_for_deployment()
**Location**: Before `_build_symphony_json()` in `composer_deployer.py:_deploy_once()`

```python
async def _audit_symphony_logic_for_deployment(
    self,
    strategy: Strategy,
    market_context: dict
) -> List[str]:
    """
    Final audit before deployment to Composer.

    Blocking audit that:
    1. Validates Composer-compatible syntax
    2. Checks all assets available
    3. Verifies weights valid for Composer
    4. Ensures no schema violations

    Returns: List[str] of error messages (empty if valid)
             If non-empty: deployment is blocked
    """
```

---

## Resume/Checkpoint Flow

```
Resume Scenario: Workflow failed at Stage 4 (Charter generation)

Entry:
  workflow.py:125-131
  └─> checkpoint = load_checkpoint(cohort_id)
      └─> Loads: WorkflowCheckpoint with last_completed_stage = CHARTER

  └─> result = await create_strategy_workflow(
          market_context=checkpoint.market_context,
          model=checkpoint.model,
          cohort_id=cohort_id,
          resume_checkpoint=checkpoint
      )

Inside workflow():
  Line 137: resume_stage = checkpoint.get_resume_stage()
            └─> Returns: WorkflowStage.DEPLOYMENT (next stage after CHARTER)

  Line 174-184: should_run_stage():
            └─> Stage 1 (CANDIDATES): False (skip, use checkpoint)
            └─> Stage 2 (SCORING): False (skip, use checkpoint)
            └─> Stage 3 (SELECTION): False (skip, use checkpoint)
            └─> Stage 4 (CHARTER): False (skip, use checkpoint)
            └─> Stage 5 (DEPLOYMENT): True (resume here!)

  Line 164-171: Load cached results from checkpoint:
            ├─> candidates = checkpoint.candidates
            ├─> scorecards = checkpoint.scorecards
            ├─> winner = checkpoint.winner
            ├─> reasoning = checkpoint.selection_reasoning
            ├─> charter = checkpoint.charter
            └─> symphony_id, deployed_at = None (to be filled)

  Line 324: Run Stage 5 (Deployment)
            └─> Deploy with cached winner + charter

Result: Completes workflow without re-running Stages 1-4
```

---

## Symphony Logic Audit Integration Points

### Option B: Insert in Stage 4 (Recommended)

```
After charter synthesis (charter_generator.py):

charter = await self._generate_charter_document(...)

# NEW: Non-blocking audit
if winner.logic_tree:
    audit_result = await self._audit_symphony_logic(
        strategy=winner,
        charter=charter,
        market_context=market_context,
        model=model
    )

    if audit_result.warnings:
        print(f"⚠️  Symphony Logic Audit ({len(audit_result.warnings)} warnings):")
        for warning in audit_result.warnings:
            print(f"  - {warning}")

    if audit_result.checks_performed:
        print(f"✓ Audit performed: {', '.join(audit_result.checks_performed)}")

return charter  # Unchanged, proceed to deployment
```

### Option C: Insert in Stage 5 (Safety Gate)

```
Before building symphony JSON (composer_deployer.py:_deploy_once()):

confirmation = await self._get_llm_confirmation(...)

# NEW: Blocking audit
if strategy.logic_tree:
    audit_errors = await self._audit_symphony_logic_for_deployment(
        strategy=strategy,
        market_context=market_context
    )

    if audit_errors:
        print(f"❌ Symphony Logic Audit FAILED:")
        for error in audit_errors:
            print(f"  - {error}")
        return None, None, None  # Block deployment

# Continue with deployment
symphony_json = _build_symphony_json(...)
```

---

## Summary

The execution flow is strictly linear with clear stage boundaries:

1. **Stage 1**: Generate & validate 5 candidates (semantic validation)
2. **Stage 2**: Score candidates (pure evaluation, no validation)
3. **Stage 3**: Select winner (pure reasoning, no validation)
4. **Stage 4**: Create charter (informational, **NEW: non-blocking audit**)
5. **Stage 5**: Deploy to Composer (**NEW: blocking audit + API call**)

Symphony Logic Audit fits optimally at Stage 4 (with optional blocking gate at Stage 5) because:
- Has full charter context for regime analysis
- Runs on single strategy (efficient)
- Still before deployment (actionable)
- Doesn't require modifying validated strategy
- Compatible with checkpoint/resume system
      │           │      └─> IF has_filter_leaf:
      │           │          ├─> Build filter node + wrap in wt-cash-equal
      │           │          └─> symphony_score uses root → wt-cash-equal → filter
