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

## Worked Example: VIX Tactical Rotation

**Context Pack Data:**
- VIX: 17.44 (normal)
- Trend: Strong bull (SPY +12.8% above 200d MA)
- Breadth: 75% sectors above 50d MA

**Planning:**
1. Conditional? YES (VIX threshold)
2. Triggers: VIX > 22 → defensive, VIX < 18 (2 days) → growth
3. Weight Method: Mode-based (static within each mode)
4. Frequency: Daily (volatility requires fast response)

**Complete Strategy:**
```python
Strategy(
  name="VIX Tactical Rotation",

  thesis_document="""
  Market Analysis: VIX at 17.44 in strong bull market with 75% breadth. VIX spikes above 22 trigger institutional defensive rotation with 2-4 day lag.

  Edge Explanation: Risk parity funds have mechanical deleveraging at VIX 22+, but institutional mandates use weekly/monthly committees that cannot react daily. This creates 2-4 day window for defensive rotation.

  Regime Fit: Currently in growth mode (VIX 17.44), positioned to rotate defensively when VIX exceeds 22.

  Risk Factors: Whipsaw if VIX oscillates around 22. Mitigated via hysteresis (VIX < 18 for 2 days before re-entering growth). Max drawdown 8-12% during sustained VIX > 30.
  """,

  rebalancing_rationale="""
  Daily rebalancing implements VIX rotation edge by checking threshold every day. Daily frequency required because edge exists in 2-4 day institutional lag - weekly would miss the window. Hysteresis logic prevents whipsaw. Weights: Defensive 0.50/0.30/0.20 (equal conviction TLT/GLD/BIL), Growth 0.50/0.30/0.20 (bull regime favors SPY over QQQ).
  """,

  assets=["SPY", "QQQ", "AGG", "TLT", "GLD", "BIL"],
  weights={},  # Dynamic
  rebalance_frequency="daily",

  logic_tree={
    # NOTE: Use VIXY (VIX ETF) for conditions - Composer cannot evaluate VIX index directly
    "condition": "VIXY_price > 22",
    "if_true": {
      "assets": ["TLT", "GLD", "BIL"],
      "weights": {"TLT": 0.50, "GLD": 0.30, "BIL": 0.20}
    },
    "if_false": {
      "condition": "VIXY_price < 18",  # Hysteresis for stability
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
✅ Logic Tree: Thesis mentions "VIX > 22" → logic_tree implements using VIXY ETF proxy
✅ Frequency: Volatility edge → daily rebalancing (PASS)
✅ Weights: Derivation explained (equal conviction defensive, bull tilt growth)
✅ Consistency: Thesis says "daily" → rebalance_frequency = "daily"

---

## Anti-Patterns to Avoid

**❌ Conditional thesis + empty logic_tree**
```
thesis: "Rotate to defense when VIX > 25"
logic_tree: {}  # FAIL - missing implementation
```

**❌ Momentum + equal-weight rebalancing**
Equal-weight sells winners (CONTRADICTS momentum)

**❌ Mean reversion with sector ETF**
```
thesis: "Oversold sector mean reversion"
assets: [XLF, XLC, XLB]  # FAIL - no security selection edge
```
Use individual stocks: [JPM, BAC, WFC, C]

**❌ Round weights without derivation**
```
weights: {"SPY": 0.40, "QQQ": 0.35, "AGG": 0.25}
# Missing: "equal-weight", "momentum-weighted", "risk-parity"
```

**❌ Vague failure modes**
```
"Strategy may underperform in bad markets"  # TOO VAGUE
```
Use: "VIX > 30 for 10+ days → -20% drawdown"

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
