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
- Sector ETFs for Mean Reversion/Value? → reconsider (weak edge)

### Sector ETF Tradeoff

Sector ETFs (XLK, XLF, XLE) are commoditized. **Acceptable:** Timing-based edges (volatility rotation, compound filters). **Weak:** Mean reversion/value with sector ETFs. Check `intra_sector_divergence` - high spread (>10%) = use individual stocks.

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
"condition": "SPY_price > 450"  # ❌ SYNTAX ERROR

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

---

## Worked Example: Trend Regime Rotation (SPY vs 200d MA)

**Context Pack Data:**
- Trend: Strong bull (SPY +12.8% above 200d MA)
- Breadth: 75% sectors above 50d MA
- Volatility: Normal (stable risk regime)

**Planning:**
1. Conditional? YES (trend regime detection)
2. Triggers: SPY above 200d MA → risk-on, SPY below 200d MA → defensive
3. Weight Method: Mode-based (static within each mode)
4. Frequency: Weekly (trend breaks can accelerate quickly)

**Complete Strategy:**
```python
Strategy(
  name="Trend Regime Rotation",

  thesis_document="""
  Market Analysis: SPY trades above its 200d MA with strong breadth (75% sectors above 50d MA), confirming a durable bull trend. Institutional allocators raise equity exposure in confirmed uptrends and de-risk when long-term trend breaks.

  Edge Explanation: Trend breaks trigger systematic de-risking (risk parity, vol targeting) before discretionary committees react, creating a 1-3 week window where defensive assets outperform. The edge exists due to governance delays and risk-budget rules.

  Regime Fit: Current trend is positive (SPY above 200d MA), so risk-on allocation is appropriate while the trend holds. The strategy flips defensive on a confirmed trend break.

  Risk Factors: Whipsaw around the 200d MA can cause false signals. Bond/equity correlation spikes can reduce defensive protection. Expected max drawdown 10-15% during rapid trend reversals.
  """,

  rebalancing_rationale="""
  Weekly rebalancing implements the trend regime edge by checking SPY vs its 200d MA on a steady cadence that balances responsiveness with noise reduction. WHEN SPY > 200d MA: allocate to risk-on assets (SPY 0.50, QQQ 0.30, AGG 0.20). WHEN SPY < 200d MA: rotate defensive (TLT 0.50, GLD 0.30, BIL 0.20). Weights are mode-based: equal-conviction defensive allocation and growth-tilted risk-on exposure.
  """,

  assets=["SPY", "QQQ", "AGG", "TLT", "GLD", "BIL"],
  weights={},  # Dynamic
  rebalance_frequency="weekly",

  logic_tree={
    "condition": "SPY_price > SPY_200d_MA",
    "if_true": {
      "assets": ["SPY", "QQQ", "AGG"],
      "weights": {"SPY": 0.50, "QQQ": 0.30, "AGG": 0.20}
    },
    "if_false": {
      "assets": ["TLT", "GLD", "BIL"],
      "weights": {"TLT": 0.50, "GLD": 0.30, "BIL": 0.20}
    }
  }
)
```

**Coherence Validation:**
✅ Logic Tree: Thesis mentions SPY vs 200d MA → logic_tree uses SPY_price > SPY_200d_MA
✅ Threshold Hygiene: No magic numbers - uses relative MA comparison
✅ Frequency: Trend regime → weekly rebalancing (PASS)
✅ Weights: Derivation explained (mode-based allocation)
✅ Consistency: Thesis says "weekly" → rebalance_frequency = "weekly"

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
