# Candidate Generation Recipe (Compressed v1.0)

## Workflow Overview

**Phase 1: ANALYZE** - Review context pack, classify regime (10 min)
**Phase 2: GENERATE** - Create 5 diverse candidates with clear edges (20 min)

---

## Phase 1: Analyze Context Pack

The context pack provides ALL macro/market data you need.

### Step 1.1: Macro Regime Classification (REQUIRED)

Analyze these indicators from context pack:

| Indicator | What to Check | Classification Impact |
|-----------|---------------|----------------------|
| Fed Funds Rate | Hawkish (rising) vs Dovish (falling) | Risk appetite |
| 10Y Treasury | >4% bearish bonds, <3% bullish bonds | Duration positioning |
| 10Y-2Y Spread | Inverted = recession signal | Defensive tilt |
| CPI Inflation | >3% = Fed hawkish, <2% = Fed dovish | Sector rotation |
| Unemployment | <4% = tight labor, >5% = slack | Consumer discretionary |
| GDP Growth | >2% = expansion, <0% = recession | Cyclical vs defensive |

**Output:** Classify regime as one of:
- **Expansion:** Rising GDP, low unemployment, moderate inflation → Pro-cyclical strategies
- **Slowdown:** Falling GDP, rising unemployment → Defensive rotation
- **Recession:** Negative GDP, high unemployment → Safe haven, counter-cyclical
- **Recovery:** Rising GDP from low base → Early cyclical, high beta

### Step 1.2: Market Regime Summary

Extract from `regime_snapshot`:
1. **Trend:** Bull/Bear (SPY vs 200d MA)
2. **Volatility:** Low (<15)/Normal (15-20)/Elevated (20-25)/High (>25) VIX
3. **Breadth:** % sectors above 50d MA (>70% strong, <40% weak)
4. **Leadership:** Top/bottom 3 sectors
5. **Factor Regime:** Value vs Growth premium, Momentum strength

**Use tools ONLY for:**
- Individual stock data (not in context pack)
- Factor ETFs (VTV, MTUM, QUAL)
- Extended time series (>12 months)

---

## Phase 2: Generate Candidates

### Step 2.1: Planning Matrix (REQUIRED)

Before generating, plan each candidate:

| # | Archetype | Conditional? | Triggers | Weight Method | Frequency |
|---|-----------|--------------|----------|---------------|-----------|
| 1 | | YES/NO | | | |
| 2 | | YES/NO | | | |
| 3 | | YES/NO | | | |
| 4 | | YES/NO | | | |
| 5 | | YES/NO | | | |

**Validation:**
- At least 2 conditional (YES), 2 static (NO)
- All conditional strategies have triggers defined
- Frequency matches edge timescale

### Diversity Grid (Reference for Planning)

Ensure your 5 candidates span multiple cells:

| Edge Type | Archetype | Concentration | Regime Bet | Frequency |
|-----------|-----------|---------------|------------|-----------|
| Behavioral | Momentum | Focused (3-5) | Pro-cyclical | Daily |
| Structural | Mean Reversion | Balanced (6-10) | Counter-cyclical | Weekly |
| Informational | Carry | Diversified (10+) | Neutral | Monthly |
| Risk Premium | Directional | - | - | Quarterly |
| - | Volatility | - | - | - |

**Target diversity across 5 candidates:**
- ≥3 different edge types
- ≥3 different archetypes
- Mix of focused + diversified
- Mix of pro-cyclical + counter-cyclical
- ≥3 different frequencies

### Step 2.2: Edge Quantification (REQUIRED)

For each candidate, provide realistic expectations:

| Metric | Realistic Range | Red Flags |
|--------|-----------------|-----------|
| Expected Sharpe | 0.5 - 2.0 | >2.5 is suspicious |
| vs Benchmark | +0.5% to +5% | >10% alpha is unrealistic |
| Max Drawdown | -8% to -30% | <-8% too optimistic |
| Win Rate | 45% - 65% | >70% needs evidence |

**If claiming >2.0 Sharpe or >70% win rate, MUST provide:**
- Historical backtesting evidence, OR
- Hypothesis language: "If edge holds, EXPECT to achieve..."

### Step 2.3: Active vs Passive Tradeoff (REQUIRED)

Before finalizing each candidate, compare against passive alternative:

| Dimension | Your Strategy | Passive Alternative |
|-----------|---------------|---------------------|
| Simplicity | [1-5] | [1-5] |
| Cost (annual %) | [X%] | [0.03-0.10%] |
| Downside Protection | [1-5] | [1-5] |
| Upside Capture | [1-5] | [1-5] |
| Regime Dependency | High/Medium/Low | None |
| Alpha Potential | [+X% expected] | 0% |
| Failure Risk | [Describe] | Market risk only |

**Decision Rule:** If passive wins ≥5 dimensions → RECONSIDER strategy value-add

### Step 2.4: Cost Budget for High-Frequency Strategies

**Required for Daily/Weekly strategies:**

| Component | Estimate |
|-----------|----------|
| Turnover | [X% annual] |
| Spread + Impact | [X bps per trade] |
| Annual Friction | Turnover × Spread × 2 = [X%] |
| Gross Alpha Target | [Y%] |
| Net Alpha | Gross - Friction = [Z%] |

**Caution:** Transaction costs can exceed alpha by 2-10x for high-turnover strategies.
- Daily rebalancing: ~5-15% annual friction for liquid ETFs
- Weekly rebalancing: ~2-5% annual friction
- Monthly rebalancing: ~0.5-1.5% annual friction

**If Net Alpha < 0 after costs → strategy is underwater, revise frequency or abandon**

### Step 2.5: Generate Each Candidate

For each, answer:
1. **What is the edge?** (Specific structural inefficiency)
2. **Why does it exist?** (Behavioral, structural, informational, risk premium)
3. **Why now?** (Cite context pack data)
4. **What is the archetype?** (Momentum, mean reversion, carry, directional, volatility)
5. **What breaks it?** (Specific failure modes)

### Step 2.6: Self-Critique (RSIP Checkpoint)

For each candidate, verify:

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
    "condition": "VIX > 22",
    "if_true": {
      "assets": ["TLT", "GLD", "BIL"],
      "weights": {"TLT": 0.50, "GLD": 0.30, "BIL": 0.20}
    },
    "if_false": {
      "condition": "VIX < 18 AND days_below_18 >= 2",
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
✅ Logic Tree: Thesis mentions "VIX > 22" → logic_tree implements nested VIX conditions
✅ Frequency: Volatility edge → daily rebalancing (PASS)
✅ Weights: Derivation explained (equal conviction defensive, bull tilt growth)
✅ Consistency: Thesis says "daily" → rebalance_frequency = "daily"

---

## Worked Example: Mean Reversion with Stock Selection

**Context Pack Data:**
- VIX: 22.1 (elevated, fear spike)
- XLF: -8.2% (30d), lagging SPY +1.2%
- Sector dispersion: 4.1% (elevated)

**Planning:**
1. Conditional? NO (static allocation - edge is in SELECTION not timing)
2. Weight Method: Equal-weight (treating oversold quality stocks equally)
3. Frequency: Monthly (30-60 day reversion window)

**Security Selection (REQUIRED for mean reversion):**
1. Universe: S&P 500 Financials
2. Screen: P/E < 11.2x sector avg, down >10%, cap >$100B, yield >2.5%
3. Analysis: JPM 8.5x P/E fortress balance sheet, BAC 9.1x solid capital, WFC 10.2x turnaround, C 7.8x highest risk-reward
4. Selection: Top 4 by composite score

**Complete Strategy:**
```python
Strategy(
  name="Oversold Financial Stock Selection",

  thesis_document="""
  Market Analysis: XLF -8.2% due to regional bank contagion fears, creating indiscriminate selloff in mega-caps. JPM 8.5x P/E, BAC 9.1x, WFC 10.2x, C 7.8x - all below 11.2x sector average.

  Edge Explanation: Mean-reversion at STOCK level (not sector). Institutional funds sold entire XLF via ETF redemptions (indiscriminate). Mega-cap fundamentals unchanged (fortress balance sheets). Value buyers step in at P/E < 9x.

  Why Stocks vs XLF: XLF includes 20+ financials including risky regional banks. Our edge is security selection - identifying 4 quality mega-caps mispriced by panic.

  Risk Factors: Regional crisis spreads to mega-caps, Fed hikes 50+ bps, recession triggers credit cycle. Expected max drawdown 12-18%.
  """,

  rebalancing_rationale="""
  Monthly rebalancing captures mean-reversion at stock level (30-60 day recovery). Equal-weight (25% each) treats quality names equally - JPM/BAC core quality, WFC/C value tilt. No conditional logic - edge is in SELECTION (these 4 stocks vs XLF), not timing.
  """,

  assets=["JPM", "BAC", "WFC", "C"],
  weights={"JPM": 0.25, "BAC": 0.25, "WFC": 0.25, "C": 0.25},
  rebalance_frequency="monthly",
  logic_tree={}  # Static - edge is SELECTION not TIMING
)
```

**Coherence Validation:**
✅ Logic Tree: Static thesis → empty logic_tree (PASS)
✅ Frequency: Mean reversion → monthly (PASS)
✅ Weights: Equal-weight justified
✅ Securities: Individual stocks with fundamental analysis (PASS - not sector ETF)

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

## Final Validation Summary

Before returning, create summary:
```
Candidate #1: [Coherence ✅/❌] [Frequency ✅/⚠️] [Weights ✅/⚠️] [Securities ✅/⚠️]
Candidate #2: ...
Candidate #3: ...
Candidate #4: ...
Candidate #5: ...
```

**Fix ALL ❌ violations before returning List[Strategy].**

---

## Quality Gates

✅ Exactly 5 Strategy objects
✅ All weights sum to 1.0
✅ No single asset >50% without justification
✅ At least 3 different archetypes
✅ At least 2 conditional, 2 static strategies
✅ Mean reversion/value use individual stocks (not sector ETFs)
✅ All conditional theses have populated logic_tree

**Return List[Strategy] with exactly 5 validated candidates.**
