# Symphony Logic Audit Integration Guide

Quick reference for implementing Symphony Logic Audit in the workflow.

---

## Recommended Approach: Hybrid (Stage 4 + Stage 5)

**Primary Audit**: Stage 4 (Charter Generation)
- Non-blocking warnings before deployment
- Full context for regime analysis
- Low cost (single strategy)

**Safety Gate**: Stage 5 (Deployment)
- Blocking errors before Composer API
- Final validation of deployment readiness
- Prevents failed API calls

---

## Stage 4 Implementation Details

### Location in Code
File: `/Users/ben/dev/ai-hedge-fund/src/agent/stages/charter_generator.py`
After line: 117 (after `generate()` completes)

### Method Signature

```python
async def _audit_symphony_logic(
    self,
    strategy: Strategy,
    charter: Charter,
    market_context: dict,
    model: str = DEFAULT_MODEL
) -> "SymphonyLogicAuditResult":
    """
    Audit symphony logic with full charter context.

    Runs these checks:
    1. Condition Validity: Syntax correct, thresholds realistic
    2. Branch Completeness: Both branches have assets & weights
    3. Asset Consistency: Branch assets logical for scenario
    4. Regime Applicability: Condition likely to activate in current regime
    5. Charter Alignment: Failure modes mention relevant branches

    Args:
        strategy: Strategy with logic_tree to audit
        charter: Generated charter for context
        market_context: Market regime data
        model: LLM for semantic checks

    Returns:
        SymphonyLogicAuditResult:
        - is_valid: bool (always true for non-blocking audit)
        - warnings: List[str] (actionable issues found)
        - errors: List[str] (empty for Stage 4)
        - checks_performed: List[str] (what was audited)
        - regime_applicability: dict (when condition activates)
    """
```

### Integration Code

```python
# In CharterGenerator.generate(), after charter synthesis:

async def generate(
    self,
    winner: Strategy,
    reasoning: SelectionReasoning,
    candidates: List[Strategy],
    scorecards: List[EdgeScorecard],
    market_context: dict,
    model: str = DEFAULT_MODEL
) -> Charter:
    # ... existing code (lines 63-200) ...

    charter = await self._generate_charter_document(
        winner, reasoning, candidates, scorecards, market_context, model
    )

    # ===== NEW: Symphony Logic Audit (Stage 4) =====
    if winner.logic_tree:  # Only audit conditional strategies
        audit_result = await self._audit_symphony_logic(
            strategy=winner,
            charter=charter,
            market_context=market_context,
            model=model
        )

        # Log audit results (non-blocking)
        if audit_result.warnings:
            print(f"\n⚠️  Symphony Logic Audit: {len(audit_result.warnings)} warning(s)")
            for warning in audit_result.warnings:
                print(f"  - {warning}")

        if audit_result.checks_performed:
            checks_str = ", ".join(audit_result.checks_performed)
            print(f"✓ Audit checks: {checks_str}")

        if audit_result.regime_applicability:
            print(f"📊 Condition activation: {audit_result.regime_applicability}")

    # Continue without modification (non-blocking)
    return charter
```

### Audit Checks to Implement

#### Check 1: Condition Validity

```python
def _validate_condition_syntax(self, condition: str) -> tuple[bool, str]:
    """
    Validate condition syntax is parseable.

    Valid patterns:
    - "VIX > 25" (indicator, operator, threshold)
    - "SPY 200d MA > 0" (asset comparison)
    - "momentum < -0.05" (factor metric)
    - "drawdown > 15%" (risk metric)

    Returns: (is_valid, error_message)
    """
    import re

    # Valid indicators and operators
    valid_indicators = {
        "vix", "momentum", "drawdown", "ma", "rsi", "macd",
        "200d", "50d", "20d"
    }
    valid_operators = {">", "<", ">=", "<=", "=", "==", "!="}

    # Parse condition
    tokens = re.split(r'[\s()]+', condition.lower())
    found_indicator = False
    found_operator = False

    for token in tokens:
        if token in valid_indicators:
            found_indicator = True
        if token in valid_operators:
            found_operator = True

    if not found_indicator:
        return False, f"Condition missing valid indicator (VIX, momentum, drawdown, etc)"

    if not found_operator:
        return False, f"Condition missing comparison operator (>, <, >=, <=, ==)"

    # Check for numeric threshold
    numbers = re.findall(r'\d+(?:\.\d+)?', condition)
    if not numbers:
        return False, f"Condition missing numeric threshold"

    return True, ""
```

#### Check 2: Branch Completeness

```python
def _validate_branch_completeness(
    self,
    strategy: Strategy
) -> tuple[bool, List[str]]:
    """
    Validate both branches have assets and weights.

    Returns: (is_valid, list_of_errors)
    """
    errors = []
    logic_tree = strategy.logic_tree

    if not logic_tree:
        return True, []

    for branch_name in ["if_true", "if_false"]:
        branch = logic_tree.get(branch_name, {})

        # Check assets exist
        assets = branch.get("assets", [])
        if not assets or not isinstance(assets, list):
            errors.append(f"{branch_name}: missing or empty assets list")
            continue

        # Check weights exist
        weights = branch.get("weights", {})
        if not weights or not isinstance(weights, dict):
            errors.append(f"{branch_name}: missing or empty weights dict")
            continue

        # Check weights sum to ~1.0
        total_weight = sum(weights.values())
        if not (0.99 <= total_weight <= 1.01):
            errors.append(
                f"{branch_name}: weights sum to {total_weight:.2f}, not 1.0"
            )
            continue

        # Check all assets in weights
        missing_weights = set(assets) - set(weights.keys())
        if missing_weights:
            errors.append(
                f"{branch_name}: assets {missing_weights} missing from weights"
            )

    return len(errors) == 0, errors
```

#### Check 3: Asset Consistency

```python
def _validate_asset_consistency(
    self,
    strategy: Strategy,
    market_context: dict
) -> tuple[bool, List[str]]:
    """
    Validate branch assets make logical sense for their scenarios.

    For if_true branch (condition met, e.g., "VIX > 25"):
    - Should have defensive assets (bonds, utilities) or hedges (gold, VIX calls)
    - OK to have growth if paired with hedge

    For if_false branch (condition not met, e.g., "VIX < 25"):
    - Should have growth assets (tech, equities)
    - OK to have bonds for diversification

    Returns: (is_valid, list_of_warnings)
    """
    warnings = []
    logic_tree = strategy.logic_tree

    if not logic_tree:
        return True, []

    condition = logic_tree.get("condition", "").lower()
    if_true_assets = set(logic_tree.get("if_true", {}).get("assets", []))
    if_false_assets = set(logic_tree.get("if_false", {}).get("assets", []))

    # Defensive assets (bonds, utilities, consumer staples)
    defensive = {"TLT", "BND", "AGG", "SHY", "IEF", "XLU", "XLP", "KO", "JNJ"}

    # Growth assets (tech, small cap, emerging markets)
    growth = {"QQQ", "VGT", "IWM", "VWO", "XLK", "XLV", "ARKK", "SMH"}

    # Hedges (gold, puts, inverse ETFs, VIX)
    hedges = {"GLD", "VNQ", "SH", "PSQ", "UVXY", "VXX"}

    # If condition is about volatility increase (VIX > X, drawdown > Y)
    if any(vol_keyword in condition for vol_keyword in ["vix >", "volatility", "drawdown >"]):
        # if_true should be defensive or hedged
        if if_true_assets and not any(asset in if_true_assets for asset in defensive | hedges):
            warnings.append(
                f"if_true branch ({if_true_assets}) lacks defensive assets "
                f"for high-volatility scenario (condition: {condition})"
            )

        # if_false should be growth
        if if_false_assets and not any(asset in if_false_assets for asset in growth):
            warnings.append(
                f"if_false branch ({if_false_assets}) lacks growth assets "
                f"for low-volatility scenario"
            )

    return len(warnings) == 0, warnings
```

#### Check 4: Regime Applicability

```python
async def _assess_regime_applicability(
    self,
    strategy: Strategy,
    market_context: dict,
    model: str
) -> dict:
    """
    Assess whether condition is likely to activate in current and near-term regimes.

    Uses market context to evaluate:
    - Current VIX level (is condition already met?)
    - Regime tags (bull, bear, elevated volatility?)
    - Recent events (what triggered them?)

    Returns: dict with activation analysis
    {
        "condition": "VIX > 25",
        "current_vix": 18.5,
        "is_currently_active": False,
        "likely_to_activate_30d": "High",
        "recent_activations": ["2024-01-15 market correction"],
        "regime_fit": "Defensive positioning for vol spike"
    }
    """
    condition = strategy.logic_tree.get("condition", "").lower()
    regime_snapshot = market_context.get("regime_snapshot", {})
    recent_events = market_context.get("recent_events", [])
    regime_tags = market_context.get("regime_tags", [])

    # Extract condition components
    if "vix" in condition:
        current_vix = regime_snapshot.get("volatility", {}).get("vix_level")
        vix_threshold = int(re.search(r'\d+', condition).group()) if re.search(r'\d+', condition) else None

        is_active = current_vix > vix_threshold if current_vix and vix_threshold else None

        return {
            "condition": condition,
            "indicator": "VIX",
            "current_value": current_vix,
            "threshold": vix_threshold,
            "is_currently_active": is_active,
            "likely_to_activate_30d": "High" if "elevated" in regime_tags or "high" in regime_tags else "Medium",
            "regime_fit": f"{'Elevated' if is_active else 'Normal'} volatility regime",
        }

    elif "momentum" in condition:
        return {
            "condition": condition,
            "indicator": "Momentum",
            "current_trend": regime_snapshot.get("trend"),
            "is_currently_active": "bull" not in regime_tags.get("trend_type", "").lower(),
            "regime_fit": "Market rotation or regime change",
        }

    else:
        return {
            "condition": condition,
            "indicator": "Unknown",
            "warning": "Could not assess activation likelihood",
        }
```

#### Check 5: Charter Alignment

```python
def _validate_charter_alignment(
    self,
    strategy: Strategy,
    charter: Charter
) -> List[str]:
    """
    Validate that charter's failure modes reference strategy's branches.

    Example:
    - Charter failure mode: "High volatility spike > 50% drawdown"
    - logic_tree if_true branch should have defensive assets
    - if_false branch should have growth assets

    Returns: List of misalignment warnings
    """
    warnings = []
    logic_tree = strategy.logic_tree
    failure_modes = charter.failure_modes

    if not logic_tree:
        return warnings

    condition = logic_tree.get("condition", "").lower()
    if_true_assets = logic_tree.get("if_true", {}).get("assets", [])
    if_false_assets = logic_tree.get("if_false", {}).get("assets", [])

    # Check if failure modes mention branches' assets
    for i, failure_mode in enumerate(failure_modes):
        failure_mode_lower = failure_mode.lower()

        # If condition is about volatility, check if failure mentions it
        if "vix" in condition or "volatility" in condition or "drawdown" in condition:
            if "volatility" not in failure_mode_lower and "vix" not in failure_mode_lower:
                warnings.append(
                    f"Failure mode {i+1} doesn't mention volatility, "
                    f"but strategy conditions on VIX/volatility"
                )

        # Check if failure modes reference branch assets
        if_true_mentioned = any(asset.lower() in failure_mode_lower for asset in if_true_assets)
        if_false_mentioned = any(asset.lower() in failure_mode_lower for asset in if_false_assets)

        if not (if_true_mentioned or if_false_mentioned):
            warnings.append(
                f"Failure mode {i+1} doesn't mention any branch assets "
                f"({if_true_assets} or {if_false_assets})"
            )

    return warnings
```

### Audit Result Dataclass

```python
from dataclasses import dataclass, field

@dataclass
class SymphonyLogicAuditResult:
    """Results of symphony logic audit."""

    # Validation status
    is_valid: bool = True  # Always True for Stage 4 (non-blocking)

    # What was audited
    audit_type: str = "stage4_charter"  # or "stage5_deployment"
    checks_performed: List[str] = field(default_factory=list)
    # e.g., ["condition_syntax", "branch_completeness", "regime_applicability"]

    # Issues found
    warnings: List[str] = field(default_factory=list)  # Non-blocking
    errors: List[str] = field(default_factory=list)    # Blocking (Stage 5 only)

    # Analysis details
    condition_analysis: dict = field(default_factory=dict)
    branch_analysis: dict = field(default_factory=dict)
    regime_applicability: dict = field(default_factory=dict)
    charter_alignment: dict = field(default_factory=dict)
```

---

## Stage 5 Implementation Details

### Location in Code
File: `/Users/ben/dev/ai-hedge-fund/src/agent/stages/composer_deployer.py`
Before line: 581 (in `_deploy_once()`)

### Method Signature

```python
async def _audit_symphony_logic_for_deployment(
    self,
    strategy: Strategy,
    market_context: dict
) -> List[str]:
    """
    Final blocking audit before Composer deployment.

    Strict validation that:
    1. Condition syntax valid for Composer parsing
    2. All branch assets supported by Composer
    3. Weights valid for Composer schema
    4. No condition edge cases that break execution

    Returns: List[str] of error messages
             Empty list = deployment OK
             Non-empty = deployment blocked
    """
```

### Integration Code

```python
# In ComposerDeployer._deploy_once(), after confirmation (line 578):

async def _deploy_once(
    self,
    strategy: Strategy,
    charter: Charter,
    market_context: dict,
    model: str,
) -> tuple[str | None, str | None, str | None]:
    """Single deployment attempt."""

    # Step 1: Get LLM confirmation
    confirmation = await self._get_llm_confirmation(
        strategy=strategy,
        charter=charter,
        model=model,
    )

    if not confirmation.ready_to_deploy:
        print("⚠️  LLM declined to deploy strategy")
        return None, None, None

    # ===== NEW: Symphony Logic Audit (Stage 5) =====
    if strategy.logic_tree:
        audit_errors = await self._audit_symphony_logic_for_deployment(
            strategy=strategy,
            market_context=market_context
        )

        if audit_errors:
            print(f"\n❌ Symphony Logic Audit FAILED before deployment:")
            for error in audit_errors:
                print(f"  ❌ {error}")
            print(f"\n💾 Checkpoint preserved - can retry from Stage 4")
            return None, None, None  # Block deployment

    # Step 2: Build symphony JSON (existing code)
    symphony_json = _build_symphony_json(...)
```

### Deployment Audit Checks

```python
async def _audit_symphony_logic_for_deployment(
    self,
    strategy: Strategy,
    market_context: dict
) -> List[str]:
    """
    Strict validation before Composer API call.

    Checks:
    1. Condition syntax valid for _parse_condition()
    2. All assets supported by Composer
    3. Weights valid (sum to 1.0 per branch)
    4. No special characters that confuse parser
    """
    errors = []
    logic_tree = strategy.logic_tree

    if not logic_tree:
        return errors  # Static strategies always OK

    # Check 1: Condition syntax
    condition = logic_tree.get("condition", "")
    if not self._is_composer_compatible_condition(condition):
        errors.append(
            f"Condition '{condition}' not Composer-compatible. "
            f"Use simple syntax: 'VIX > 25' or 'SPY > 200d MA'"
        )

    # Check 2: All assets available to Composer
    all_assets = set()
    for branch in ["if_true", "if_false"]:
        branch_assets = logic_tree.get(branch, {}).get("assets", [])
        all_assets.update(branch_assets)

    unavailable = self._check_asset_availability(all_assets, market_context)
    if unavailable:
        errors.append(
            f"Assets not available: {unavailable}. "
            f"Check exchange or ticker spelling."
        )

    # Check 3: Weights sum to 1.0 per branch
    for branch in ["if_true", "if_false"]:
        weights = logic_tree.get(branch, {}).get("weights", {})
        total = sum(weights.values())
        if not (0.99 <= total <= 1.01):
            errors.append(
                f"{branch} weights sum to {total:.2f}, not 1.0"
            )

    return errors

def _is_composer_compatible_condition(self, condition: str) -> bool:
    """
    Check if condition can be parsed by _parse_condition().

    Valid: "VIX > 25", "momentum < -0.05"
    Invalid: "VIX > 25 AND momentum < -0.05" (AND not supported)
    """
    # Should not have boolean operators (those require more complex logic)
    if any(op in condition for op in [" and ", " or ", " AND ", " OR "]):
        return False

    # Must have indicator + operator + value
    indicators = ["vix", "momentum", "drawdown", "ma"]
    if not any(ind in condition.lower() for ind in indicators):
        return False

    # Must have operator
    if not any(op in condition for op in [">", "<", ">=", "<=", "==", "!="]):
        return False

    return True

def _check_asset_availability(
    self,
    assets: set,
    market_context: dict
) -> set:
    """
    Check if assets are available in Composer.

    Returns: Set of unavailable assets
    """
    # Composer supports all major ETFs and stocks
    # This is a basic check - could be expanded

    known_invalid = {"invalid_ticker", "fake_etf"}
    return assets & known_invalid
```

---

## Testing Symphony Logic Audit

### Unit Test Template

```python
# tests/test_symphony_logic_audit.py

import pytest
from src.agent.models import Strategy, Charter, RebalanceFrequency
from src.agent.stages.charter_generator import CharterGenerator
from src.agent.stages.composer_deployer import ComposerDeployer

class TestSymphonyLogicAudit:
    """Test suite for symphony logic audit."""

    @pytest.fixture
    def market_context(self):
        """Sample market context for testing."""
        return {
            "metadata": {"anchor_date": "2025-01-01"},
            "regime_snapshot": {"volatility": {"vix_level": 18.5}},
            "regime_tags": ["bull", "low_volatility"],
            "recent_events": []
        }

    @pytest.fixture
    def conditional_strategy(self):
        """Strategy with valid conditional logic."""
        return Strategy(
            name="Volatility Rotation",
            assets=["SPY", "TLT", "QQQ"],
            weights={"SPY": 0.5, "TLT": 0.3, "QQQ": 0.2},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={
                "condition": "VIX > 25",
                "if_true": {
                    "assets": ["TLT", "GLD"],
                    "weights": {"TLT": 0.7, "GLD": 0.3}
                },
                "if_false": {
                    "assets": ["SPY", "QQQ"],
                    "weights": {"SPY": 0.6, "QQQ": 0.4}
                }
            },
            rebalancing_rationale="Rotate to defensive when VIX spikes"
        )

    @pytest.mark.asyncio
    async def test_valid_conditional_strategy(self, conditional_strategy, market_context):
        """Valid conditional strategy should pass audit."""
        charter_gen = CharterGenerator()
        charter = Charter(
            market_thesis="Bull market thesis",
            strategy_selection="Selected for volatility management",
            expected_behavior="Defensive in high vol",
            failure_modes=["VIX stays elevated"],
            outlook_90d="Monitor volatility"
        )

        audit_result = await charter_gen._audit_symphony_logic(
            strategy=conditional_strategy,
            charter=charter,
            market_context=market_context,
            model="openai:gpt-4o"
        )

        assert audit_result.is_valid
        assert len(audit_result.errors) == 0
        assert len(audit_result.checks_performed) >= 3

    @pytest.mark.asyncio
    async def test_invalid_condition_syntax(self, market_context):
        """Invalid condition syntax should generate error."""
        strategy = Strategy(
            name="Bad Condition",
            assets=["SPY"],
            weights={"SPY": 1.0},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={
                "condition": "AND OR INVALID",
                "if_true": {"assets": ["SPY"], "weights": {"SPY": 1.0}},
                "if_false": {"assets": ["SPY"], "weights": {"SPY": 1.0}}
            },
            rebalancing_rationale="Test"
        )

        deployer = ComposerDeployer()
        errors = await deployer._audit_symphony_logic_for_deployment(
            strategy=strategy,
            market_context=market_context
        )

        assert len(errors) > 0
        assert any("invalid" in e.lower() for e in errors)

    def test_branch_completeness_check(self):
        """Branches must have assets and weights."""
        # Missing assets in if_true
        bad_strategy = Strategy(
            name="Incomplete Branch",
            assets=["SPY"],
            weights={"SPY": 1.0},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={
                "condition": "VIX > 25",
                "if_true": {
                    "assets": [],  # EMPTY!
                    "weights": {}
                },
                "if_false": {"assets": ["SPY"], "weights": {"SPY": 1.0}}
            },
            rebalancing_rationale="Test"
        )

        charter_gen = CharterGenerator()
        is_valid, errors = charter_gen._validate_branch_completeness(bad_strategy)

        assert not is_valid
        assert any("empty assets" in e.lower() for e in errors)
```

---

## Error Messages and Recovery

### Stage 4 Warning Example

```
⚠️  Symphony Logic Audit: 2 warning(s)
  - if_true branch (TLT, GLD) lacks defensive assets for high-volatility scenario
  - Failure mode 3 doesn't mention volatility, but strategy conditions on VIX

✓ Audit checks: condition_syntax, branch_completeness, regime_applicability

📊 Condition activation: {"condition": "VIX > 25", "current_vix": 18.5,
                          "is_currently_active": false,
                          "likely_to_activate_30d": "High"}

✓ Charter created (5 failure modes)

→ Continuing to deployment (warnings are non-blocking)
```

### Stage 5 Error Example

```
❌ Symphony Logic Audit FAILED before deployment:
  ❌ Condition 'VIX > 25 AND momentum < -0.05' uses AND operator
     Composer supports single conditions only. Use: 'VIX > 25' OR 'momentum < -0.05'
  ❌ Weights in if_true sum to 0.99, not 1.0 (TLT=0.7, GLD=0.29)
  ❌ Asset 'INVALID_TICKER' not available in Composer

💾 Checkpoint preserved - can retry from Stage 4

(No deployment attempted)
```

---

## Checklist for Implementation

### Before Coding
- [ ] Decide: Stage 4 only or Stage 4+5 hybrid?
- [ ] Define severity levels (warning vs error)
- [ ] Determine acceptable warning thresholds
- [ ] Design logging/reporting format

### Stage 4 (Charter Generator)
- [ ] Add `SymphonyLogicAuditResult` dataclass
- [ ] Add `_audit_symphony_logic()` async method
- [ ] Add sub-methods: `_validate_condition_syntax()`, `_validate_branch_completeness()`, etc.
- [ ] Add console output for warnings
- [ ] Test with 5+ conditional strategies
- [ ] Verify non-blocking behavior (continues to deployment)
- [ ] Test with static strategies (skip audit)

### Stage 5 (Composer Deployer)
- [ ] Add `_audit_symphony_logic_for_deployment()` async method
- [ ] Add `_is_composer_compatible_condition()` helper
- [ ] Add `_check_asset_availability()` helper
- [ ] Call audit before `_build_symphony_json()`
- [ ] Block deployment if errors found
- [ ] Test failure cases (invalid condition, bad weights)
- [ ] Verify error messages are actionable
- [ ] Test checkpoint is preserved on block

### Integration Testing
- [ ] End-to-end workflow with conditional strategy
- [ ] Checkpoint/resume with audit in place
- [ ] Mixed conditional + static strategies
- [ ] Deployment succeeds with warnings at Stage 4
- [ ] Deployment blocked with errors at Stage 5
- [ ] Token tracking includes audit costs

### Documentation
- [ ] Update CLAUDE.md with audit behavior
- [ ] Add examples of valid/invalid logic_trees
- [ ] Document audit check descriptions
- [ ] Document recovery paths (how to fix failures)

---

## Token Cost Estimates

### Stage 4 Audit
- Condition validation: ~50 tokens (regex parsing)
- Regime applicability: ~200 tokens (context analysis)
- Charter alignment: ~150 tokens (failure mode comparison)
- **Total per strategy**: ~400 tokens (1 strategy, non-async)
- **Cost**: Low - runs once at end of expensive charter generation

### Stage 5 Audit
- Syntax validation: ~20 tokens (strict parsing)
- Asset availability: ~50 tokens (lookup)
- Weight validation: ~30 tokens (arithmetic)
- **Total per strategy**: ~100 tokens (1 strategy, fast)
- **Cost**: Negligible - runs only if logic_tree present

**Total workflow cost increase**: ~500 tokens (~1% of typical 52k-57k workflow)

---

## References

- Main workflow orchestration: `src/agent/workflow.py:74-380`
- Charter generation: `src/agent/stages/charter_generator.py:26-230`
- Deployment: `src/agent/stages/composer_deployer.py:463-608`
- Strategy model: `src/agent/models.py:70-250`
- Symphony JSON builder: `src/agent/stages/composer_deployer.py:305-395`
- Condition parser: `src/agent/stages/composer_deployer.py:_parse_condition()`

---

## Quick Start

1. **Copy this file to workspace**
2. **Choose Option B (Stage 4) or B+C (Hybrid)**
3. **Implement `_audit_symphony_logic()` in CharterGenerator**
4. **Optionally implement `_audit_symphony_logic_for_deployment()` in ComposerDeployer**
5. **Test with conditional strategies**
6. **Run full workflow test with checkpoint/resume**
7. **Deploy and monitor token usage**

Estimated effort: 2-3 hours for Stage 4 alone, 4-5 hours for hybrid approach.
