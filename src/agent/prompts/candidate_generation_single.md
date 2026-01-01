# Single Candidate Generation Recipe (Parallel Mode v1.0)

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

**Use tools ONLY for:**
- Individual stock data (not in context pack)
- Factor ETFs (VTV, MTUM, QUAL)
- Extended time series (>12 months)

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
- Empty logic_tree + conditional thesis = AUTO-REJECT

**Q2: Weight Justification**
- Show calculation for weights
- Round numbers need explicit derivation method

**Q3: Edge Robustness**
- Specific failure trigger + expected drawdown
- "Market crashes" is too vague

Mark each Q1/Q2/Q3 as ✅ PASS or ❌ FAIL. Fix all failures before proceeding.

---

## Threshold Hygiene (REQUIRED - Syntax Error if violated)

All numeric thresholds in conditions MUST be **relative**, not absolute magic numbers.

### ALLOWED Patterns

```python
# Price vs own moving average (relative to history)
"condition": "SPY_price > SPY_200d_MA"

# Zero-bounded direction check (up/down only)
"condition": "VIXY_cumulative_return_5d > 0"

# Bounded indicator with standard threshold (RSI 0-100)
"condition": "SPY_RSI_14d > 70"

# Cross-asset comparison (relative performance)
"condition": "XLK_cumulative_return_30d > XLF_cumulative_return_30d"
```

### REJECTED Patterns (Will fail validation)

```python
# Absolute price threshold - WHY 22? No empirical basis
"condition": "VIXY_price > 22"  # ❌ SYNTAX ERROR

# Arbitrary return threshold - WHY 5%? Magic number
"condition": "SPY_cumulative_return_30d > 0.05"  # ❌ SYNTAX ERROR
```

### Fix Patterns

| Magic Number | Relative Alternative |
|--------------|---------------------|
| `VIXY_price > 22` | `VIXY_cumulative_return_5d > 0` (volatility rising) |
| `VIXY_price < 18` | `VIXY_cumulative_return_5d < 0` (volatility falling) |
| `SPY_return > 0.05` | `SPY_cumulative_return_30d > 0` (positive trend) |
| `TLT_price < 100` | `TLT_cumulative_return_30d < 0` (bonds falling) |

---

## Worked Example: VIX Tactical Rotation

**Context Pack Data:**
- VIX: 17.44 (normal)
- Trend: Strong bull (SPY +12.8% above 200d MA)
- Breadth: 75% sectors above 50d MA

**Planning:**
1. Conditional? YES (VIX movement detection)
2. Triggers: VIXY rising (5d return > 0) → defensive, VIXY falling (5d return < 0) → growth
3. Weight Method: Mode-based (static within each mode)
4. Frequency: Daily (volatility requires fast response)

**Complete Strategy:**
```python
Strategy(
  name="VIX Tactical Rotation",

  thesis_document="""
  Market Analysis: VIX at 17.44 in strong bull market with 75% breadth. VIX spikes trigger institutional defensive rotation with 2-4 day lag.

  Edge Explanation: Risk parity funds have mechanical deleveraging when volatility rises, but institutional mandates use weekly/monthly committees that cannot react daily. This creates 2-4 day window for defensive rotation. Capacity ~$500M AUM before volatility-based rotation signals become crowded.

  Regime Fit: Currently in growth mode (VIX stable/falling), positioned to rotate defensively when volatility rises (VIXY 5d return positive).

  Risk Factors: Whipsaw if volatility oscillates. Mitigated via directional confirmation (require positive/negative 5d return). Max drawdown 8-12% during sustained volatility spike.
  """,

  rebalancing_rationale="""
  Daily rebalancing implements VIX rotation edge by checking threshold every day. Daily frequency required because edge exists in 2-4 day institutional lag - weekly would miss the window. Hysteresis logic prevents whipsaw. Weights: Defensive 0.50/0.30/0.20 (equal conviction TLT/GLD/BIL), Growth 0.50/0.30/0.20 (bull regime favors SPY over QQQ).
  """,

  assets=["SPY", "QQQ", "AGG", "TLT", "GLD", "BIL"],
  weights={},  # Dynamic
  rebalance_frequency="daily",

  logic_tree={
    # NOTE: Use VIXY (VIX ETF) with RELATIVE thresholds - no magic numbers
    "condition": "VIXY_cumulative_return_5d > 0",  # Volatility rising (relative)
    "if_true": {
      "assets": ["TLT", "GLD", "BIL"],
      "weights": {"TLT": 0.50, "GLD": 0.30, "BIL": 0.20}
    },
    "if_false": {
      "condition": "VIXY_cumulative_return_5d < 0",  # Volatility falling (relative)
      "if_true": {
        "assets": ["SPY", "QQQ", "AGG"],
        "weights": {"SPY": 0.50, "QQQ": 0.30, "AGG": 0.20}
      },
      "if_false": {
        "assets": ["SPY", "AGG", "BIL"],
        "weights": {"SPY": 0.40, "AGG": 0.40, "BIL": 0.20}
      }
    }
  }
)
```

**Coherence Validation:**
✅ Logic Tree: Thesis mentions "volatility rises" → logic_tree uses VIXY_cumulative_return_5d > 0 (relative)
✅ Threshold Hygiene: No magic numbers - uses zero-bounded return checks
✅ Frequency: Volatility edge → daily rebalancing (PASS)
✅ Weights: Derivation explained (equal conviction defensive, bull tilt growth)
✅ Consistency: Thesis says "daily" → rebalance_frequency = "daily"

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
