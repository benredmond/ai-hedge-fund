# Candidate Generation Recipe (Parallel Mode v1.0)

## Your Role

{persona}

## Your Emphasis

Focus on: **{emphasis}**

Constraint: {constraint}

---

## Workflow Overview

**Phase 1: ANALYZE** - Review context pack, classify regime
**Phase 2: GENERATE** - Create 1 high-quality candidate with clear edge

---

## Phase 1: Analyze Context Pack

The context pack provides ALL macro/market data you need. Extract:

1. **Macro Regime:** Expansion, Slowdown, Recession, or Recovery
2. **Market Trend:** Bull/Bear (SPY vs 200d MA)
3. **Volatility:** Low/Normal/Elevated/High (VIX level)
4. **Breadth:** % sectors above 50d MA
5. **Sector Leadership:** Top/bottom 3 sectors
6. **Factor Regime:** Value vs Growth, Momentum, Quality premiums

**Use tools primarily for:**
- Individual stock data (not in context pack)
- Expanding intra_sector_divergence seed lists with additional candidates
- Factor ETFs (VTV, MTUM, QUAL)
- Extended time series (>12 months)

**Context pack signals are starting points, not limits.** Do not reuse tickers verbatim across candidates. Use sector_leadership and intra_sector_divergence as seed lists, then expand with tools to find additional names and validate fit.

### Asset Type Guidance by Persona (Soft Guidance)

- **Macro regime:** Cross-asset exposures (rates, commodities, broad equity beta), not sector ETFs.
- **Factor quant:** Factor ETFs or rules-based baskets; avoid sector ETFs.
- **Tail risk:** Defensive/hedge exposures (duration, gold, low-vol), not sector ETFs.
- **Sector rotation:** Sector ETFs are allowed and should be central.
- **Trend follower:** Cross-asset ETFs or stock baskets when intra_sector_divergence is high.

---

## Phase 2: Generate Your Candidate

### Step 2.1: Planning (REQUIRED)

Before generating, plan your strategy through the lens of your emphasis:

| Attribute | Your Plan |
|-----------|-----------|
| Archetype | |
| Conditional? | YES/NO |
| Triggers (if conditional) | |
| Weight Method | |
| Frequency | |

**Validation:**
- If conditional (YES), triggers must be defined
- Frequency must match edge timescale
- Sector ETFs for Mean Reversion/Value? → reconsider (weak edge)

### Sector ETF Tradeoff

Sector ETFs (XLK, XLF, XLE) are commoditized. **Acceptable:** Timing-based edges (volatility rotation, compound filters) or the sector_rotation persona. **Weak:** Mean reversion/value with sector ETFs for non-sector personas. Check `intra_sector_divergence` - high spread (>10%) = prioritize individual stocks and expand the list via tools.

### Step 2.2: Generate the Strategy

Answer these questions through your unique lens ({emphasis}):

1. **What is the edge?** (Specific structural inefficiency)
2. **Why does it exist?** (Behavioral, structural, informational, risk premium)
3. **Why now?** (Cite context pack data)
4. **What is the archetype?** (Momentum, mean reversion, carry, directional, volatility)
5. **What breaks it?** (Specific failure modes)

### Step 2.3: Self-Critique (RSIP Checkpoint)

Verify your candidate:

**Q1: Implementation Coherence**
- Conditional keywords in thesis? → logic_tree MUST be populated
- Ranking/selection keywords in thesis? → logic_tree MUST use a filter leaf (root or branch)
- Empty logic_tree + conditional thesis = AUTO-REJECT

**Q2: Weight Justification**
- Show calculation for weights
- Round numbers need explicit derivation method

**Q3: Edge Robustness**
- Specific failure trigger + expected drawdown
- "Market crashes" is too vague

**Q4: Sector ETF Edge Type**
- Using sector ETFs? → Edge must be timing-based (not selection-based)
- Mean reversion/value with sector ETFs = FAIL

Mark each Q1/Q2/Q3/Q4 as ✅ PASS or ❌ FAIL. Fix all failures before proceeding.

---

## Threshold Hygiene (REQUIRED - Syntax Error if violated)

All numeric thresholds in conditions MUST be **relative**, not absolute magic numbers.

### ALLOWED Patterns

```python
# Price vs own moving average (relative to history)
"condition": "SPY_price > SPY_200d_MA"

# Absolute price threshold allowed ONLY for approved volatility proxies
# (example only; derive threshold from recent VIXY distribution and cite lookback/stat)
"condition": "VIXY_price > [derived_threshold]"

# Zero-bounded direction check (up/down only)
"condition": "SPY_cumulative_return_30d > 0"

# Bounded indicator with standard threshold (RSI 0-100)
"condition": "SPY_RSI_14d > 70"

# Cross-asset comparison (relative performance)
"condition": "XLK_cumulative_return_30d > XLF_cumulative_return_30d"
```

### REJECTED Patterns (Will fail validation)

```python
# Absolute price threshold - WHY 22? No empirical basis
"condition": "SPY_price > 450"  # ❌ SYNTAX ERROR (non-proxy absolute)

# Arbitrary return threshold - WHY 5%? Magic number
"condition": "SPY_cumulative_return_30d > 0.05"  # ❌ SYNTAX ERROR
```

### Fix Patterns

| Magic Number | Relative Alternative |
|--------------|---------------------|
| `SPY_price > 450` | `SPY_price > SPY_200d_MA` (trend confirmation) |
| `XLK_price < 150` | `XLK_cumulative_return_30d < 0` (momentum fading) |
| `SPY_return > 0.05` | `SPY_cumulative_return_30d > 0` (positive trend) |
| `TLT_price < 100` | `TLT_cumulative_return_30d < 0` (bonds falling) |

---

## Conditional Logic Pattern Reference (Syntax Only)

Use these as syntax references; derive your trigger from your thesis.

| Pattern | Example | Use Case |
|---------|---------|----------|
| Price vs MA | `SPY_price > SPY_200d_MA` | Trend regime |
| Return direction | `XLK_cumulative_return_30d > 0` | Momentum confirmation |
| Cross-asset | `VTV_cumulative_return_30d > VUG_cumulative_return_30d` | Factor rotation |
| RSI threshold | `SPY_RSI_14d < 30` | Mean-reversion entry |
| Volatility proxy | `VIXY_cumulative_return_5d > 0` | Vol regime (vol-focused thesis only) |
| Vol proxy (absolute) | `VIXY_price > [derived_threshold]` | Example only; derive threshold from lookback stats (e.g., 60d mean + 1σ or 75th pct) |

---

## Filter + Weighting Constraints (REQUIRED)

**Filter leaf rules:**
- `sort_by` must be one of: `cumulative_return`, `current_price`, `moving_average_return`, `moving_average_price`, `relative_strength_index`, `standard_deviation_return`, `standard_deviation_price`, `max_drawdown`
- `window` is required (positive int) for every `sort_by` except `current_price` (omit `window` entirely for `current_price`)
- `select` must be `"top"` or `"bottom"`
- `n` must be an int >= 1 and **n <= len(assets)**

**Weighting leaf rules:**
- `method` must be `"inverse_vol"` (only supported method)
- `window` is required (positive int)
- Weighting leaves only appear inside conditional branches

---

## Advanced Logic Patterns (Copyable Skeletons; Replace Tickers With Context-Driven Picks)

Use these templates and swap tickers/thresholds with context-driven picks. Justify any absolute VIXY threshold with a concrete derivation (lookback + statistic).
Weighting leaves are only valid inside conditional branches (not as a root-level logic_tree).

```python
# A) Nested gate + filter + inverse-vol
logic_tree = {
  "condition": "SPY_price > SPY_200d_MA",
  "if_true": {
    "filter": {"sort_by": "cumulative_return", "window": 30, "select": "top", "n": 2},
    "assets": ["XLK", "XLF", "XLE", "XLI", "XLY"]
  },
  "if_false": {
    "weighting": {"method": "inverse_vol", "window": 20},
    "assets": ["TLT", "GLD", "BIL"]
  }
}

# B) Filter-only root
logic_tree = {
  "filter": {"sort_by": "cumulative_return", "window": 60, "select": "top", "n": 3},
  "assets": ["XLK", "XLF", "XLE", "XLI", "XLY", "XLV"]
}

# C) Weighted branches (uses wt-cash-specified in if-child)
logic_tree = {
  "condition": "SPY_cumulative_return_50d > 0",
  "if_true": {"assets": ["QQQ", "TLT"], "weights": {"QQQ": 0.70, "TLT": 0.30}},
  "if_false": {"assets": ["TLT", "GLD"], "weights": {"TLT": 0.80, "GLD": 0.20}}
}
```

---

## Worked Examples (Illustrative Only - Do Not Anchor on Tickers)

Use these for structure and reasoning style. Replace tickers using current context data plus tool expansion.

### Example 1: Intra-Sector Divergence Stock Basket (Stock Selection)

**Context Pack Data:**
- intra_sector_divergence: Semiconductors dispersion >10% (leaders vs laggards)
- Sector leadership: Technology leads, volatility normal

**Planning:**
1. Conditional? YES (sector momentum gate)
2. Triggers: SOXX momentum vs SPY
3. Weight Method: Equal-weight stocks; defensive sleeve otherwise
4. Frequency: Weekly

**Complete Strategy:**
```python
Strategy(
  name="Intra-Sector Divergence Basket",

  thesis_document="""
  Market Analysis: intra_sector_divergence flags large dispersion in semiconductors. Use the divergence list as a seed, then expand with tool lookups to add adjacent names; tickers below are illustrative only.

  Edge Explanation: Dispersion creates momentum persistence in leaders as capital concentrates. Laggards underperform until dispersion mean-reverts.

  Regime Fit: Hold the stock basket only when semis lead the market (SOXX 30d return > SPY 30d return).

  Risk Factors: Sector-specific drawdowns and crowding risk. Expected drawdown 15-20% during sharp tech reversals.
  """,

  rebalancing_rationale="""
  Weekly rebalancing refreshes the basket as dispersion evolves. If semis lose relative momentum, rotate to defensive assets (AGG/BIL) to limit drawdown.
  """,

  assets=["NVDA", "AVGO", "AMD", "MU", "AGG", "BIL"],
  weights={},  # Dynamic
  rebalance_frequency="weekly",

  logic_tree={
    "condition": "SOXX_cumulative_return_30d > SPY_cumulative_return_30d",
    "if_true": {
      "assets": ["NVDA", "AVGO", "AMD", "MU"],
      "weights": {"NVDA": 0.25, "AVGO": 0.25, "AMD": 0.25, "MU": 0.25}
    },
    "if_false": {
      "assets": ["AGG", "BIL"],
      "weights": {"AGG": 0.60, "BIL": 0.40}
    }
  }
)
```
Note: This example uses explicit branch weights; Composer maps these to `wt-cash-specified` inside `if-child`.

### Example 2: Factor Regime Switch (Value vs Momentum)

**Context Pack Data:**
- Factor regime: Value premium positive, momentum fading

**Planning:**
1. Conditional? YES (factor leadership check)
2. Triggers: VTV vs VUG relative momentum
3. Weight Method: Mode-based factor ETFs
4. Frequency: Monthly

**Complete Strategy:**
```python
Strategy(
  name="Factor Regime Switch",

  thesis_document="""
  Market Analysis: Factor regime shows value outperformance and softer momentum. Use factor ETFs to express the regime without relying on sector exposures.

  Edge Explanation: Factor leadership shifts persist as systematic flows rebalance (value vs growth) on monthly windows.

  Regime Fit: Tilt to value + quality when value leads; otherwise tilt to momentum + growth.

  Risk Factors: Regime churn can cause whipsaw. Expected drawdown 8-12% during rapid factor reversals.
  """,

  rebalancing_rationale="""
  Monthly rebalancing aligns with factor cycle updates and reduces turnover. AGG provides ballast in both regimes.
  """,

  assets=["VTV", "VUG", "MTUM", "QUAL", "AGG"],
  weights={},  # Dynamic
  rebalance_frequency="monthly",

  logic_tree={
    "condition": "VTV_cumulative_return_90d > VUG_cumulative_return_90d",
    "if_true": {
      "assets": ["VTV", "QUAL", "AGG"],
      "weights": {"VTV": 0.45, "QUAL": 0.35, "AGG": 0.20}
    },
    "if_false": {
      "assets": ["MTUM", "VUG", "AGG"],
      "weights": {"MTUM": 0.40, "VUG": 0.40, "AGG": 0.20}
    }
  }
)
```

### Example 3: Macro Cross-Asset Rotation (Growth vs Slowdown)

**Context Pack Data:**
- Macro regime: Growth slowing, rates easing, volatility normal

**Planning:**
1. Conditional? YES (macro trend confirmation)
2. Triggers: Duration vs equities relative strength
3. Weight Method: Cross-asset sleeves
4. Frequency: Monthly

**Complete Strategy:**
```python
Strategy(
  name="Macro Cross-Asset Rotation",

  thesis_document="""
  Market Analysis: Macro regime points to slowing growth with easing rates. Cross-asset positioning captures shifts between growth and slowdown phases.

  Edge Explanation: Rate-sensitive assets (duration, gold) react earlier to regime shifts than equities, creating a tactical window.

  Regime Fit: If duration leads equities, emphasize defensive macro hedges; otherwise stay pro-growth.

  Risk Factors: Correlation shifts can reduce diversification. Expected drawdown 10-14% during inflation re-acceleration.
  """,

  rebalancing_rationale="""
  Monthly checks capture macro inflection points without over-trading. Commodity exposure provides inflation hedge in pro-growth mode.
  """,

  assets=["SPY", "TLT", "GLD", "DBC", "BIL"],
  weights={},  # Dynamic
  rebalance_frequency="monthly",

  logic_tree={
    "condition": "TLT_cumulative_return_30d > SPY_cumulative_return_30d",
    "if_true": {
      "assets": ["TLT", "GLD", "BIL"],
      "weights": {"TLT": 0.50, "GLD": 0.30, "BIL": 0.20}
    },
    "if_false": {
      "assets": ["SPY", "DBC", "GLD"],
      "weights": {"SPY": 0.55, "DBC": 0.25, "GLD": 0.20}
    }
  }
)
```

### Example 4: Trend Gate + Vol Filter (Nested + Filter Leaf)

**Context Pack Data:** Trend weak (SPY < 200d MA), volatility elevated, dispersion high.

**Planning:** Trend gate → filter top-2 sector momentum; inverse-vol defense; weekly.

**Complete Strategy:**
```python
Strategy(
  name="Trend Gate with Sector Filter",

  thesis_document="""
  Market Analysis: Trend signals are mixed with elevated volatility and high sector dispersion. A trend gate avoids buying sector momentum in weak regimes.

  Edge Explanation: Trend regimes persist for weeks; when trend is positive, sector momentum concentrates in leaders. When trend breaks, inverse-vol defense reduces drawdown while staying invested.

  Regime Fit: Use SPY trend as a regime filter, then select top-2 sectors by momentum only in risk-on regimes.

  Risk Factors: Whipsaw during rapid trend reversals and factor crowding in momentum leaders. Expected drawdown 12-18% in false-break scenarios.
  """,

  rebalancing_rationale="""
  Weekly rebalancing captures trend and sector momentum without daily noise. The filter leaf selects the top 2 sectors by 30d return in risk-on regimes. In risk-off regimes, inverse-vol weighting balances duration and defensive assets to stabilize volatility.
  """,

  assets=["XLK", "XLF", "XLE", "XLI", "XLY", "TLT", "GLD", "BIL"],
  weights={},  # Dynamic
  rebalance_frequency="weekly",

  logic_tree={
    "condition": "SPY_price > SPY_200d_MA",
    "if_true": {
      "filter": {"sort_by": "cumulative_return", "window": 30, "select": "top", "n": 2},
      "assets": ["XLK", "XLF", "XLE", "XLI", "XLY"]
    },
    "if_false": {
      "weighting": {"method": "inverse_vol", "window": 20},
      "assets": ["TLT", "GLD", "BIL"]
    }
  }
)
```

### Example 5: Filter-Only Sector Momentum

**Context Pack Data:** Leadership concentrated; breadth healthy but uneven.

**Planning:** Filter-only; top-3 sector momentum; equal-weight; monthly.

**Complete Strategy:**
```python
Strategy(
  name="Top-3 Sector Momentum",

  thesis_document="""
  Market Analysis: Sector leadership is concentrated in a small set of cyclical leaders with healthy breadth. Selecting the top sectors captures persistent leadership while avoiding laggards.

  Edge Explanation: Sector momentum persists due to flows and analyst revisions that update monthly. Ranking sectors directly captures the leadership effect.

  Regime Fit: Momentum leadership is strongest in stable volatility regimes with improving breadth.

  Risk Factors: Leadership can rotate abruptly after macro shocks. Expected drawdown 10-16% during regime flips.
  """,

  rebalancing_rationale="""
  Monthly rebalancing aligns with sector leadership updates and reduces churn. The filter leaf ranks sectors by 60d cumulative return and equal-weights the top three to avoid concentration in a single sector.
  """,

  assets=["XLK", "XLF", "XLE", "XLI", "XLY", "XLV"],
  weights={},  # Dynamic
  rebalance_frequency="monthly",

  logic_tree={
    "filter": {"sort_by": "cumulative_return", "window": 60, "select": "top", "n": 3},
    "assets": ["XLK", "XLF", "XLE", "XLI", "XLY", "XLV"]
  }
)
```

**Coherence Validation (Apply to Every Strategy):**
✅ Logic Tree matches thesis trigger
✅ Threshold hygiene: relative comparisons only (proxy absolute thresholds allowed for VIXY)
✅ Frequency matches edge timescale
✅ Weights sum to 1 with clear rationale
✅ If using branch weights, each branch weights sum to 1.0

---

## Edge Economics Calibration (Score Differentiation)

Your edge economics score determines strategy quality. Generic edges cap at 3/5.

**2-3/5 (CAPPED - Avoid):** "Momentum is a well-known factor premium. We buy assets with positive 12-month returns."
→ Why capped: No capacity limits, no causal mechanism, no decay timeline. Every quant fund runs this.

**4/5 (TARGET):** "Post-earnings momentum in mid-cap software decays over 15-20 trading days as sell-side updates lag. Capacity ~$50M before slippage erodes alpha. Edge exists because institutional coverage sparse below $5B market cap."
→ Why 4/5: Specific decay window + capacity constraint + structural explanation (analyst coverage gap).

**5/5 (STRETCH):** "Fed pivot signals → REIT repricing lag of 8-12 weeks. Historical analogs: Dec 2018 (REITs +18% in 10 weeks after pivot), Nov 2022 (+14% in 8 weeks). Mechanism: REIT valuation models use trailing cap rates updated quarterly; market-implied cap rates adjust within days."
→ Why 5/5: Quantified magnitude + historical precedent + structural mechanism (cap rate update lag).

**Your thesis_document MUST articulate:**
1. Capacity limits (when does the edge degrade?)
2. Decay timeline (how long does the edge persist?)
3. Why YOU can capture it (what's the structural explanation?)

---

## Final Validation

Before returning, verify:
```
[Coherence ✅/❌] [Frequency ✅/⚠️] [Weights ✅/⚠️] [Securities ✅/⚠️]
```

**Fix ALL ❌ violations before returning.**

---

## Quality Gates

✅ Exactly 1 Strategy object
✅ All weights sum to 1.0
✅ No single asset >50% without justification
✅ Mean reversion/value strategies use individual stocks (not sector ETFs)
✅ Conditional theses have populated logic_tree
✅ Strategy reflects your assigned emphasis: {emphasis}

**Return a single Strategy that embodies your unique perspective.**
