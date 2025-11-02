# Candidate Generation Recipe

This recipe guides you through generating 5 diverse, research-driven trading strategy candidates.

---

## WORKFLOW OVERVIEW

**Phase 1: RESEARCH (30-40 minutes)**
- Use tools to understand current market environment
- Output: ResearchSynthesis

**Phase 2: GENERATE (20-30 minutes)**
- Create 5 diverse candidates with clear edges
- Output: List[Strategy] (exactly 5)

---

## PHASE 1: RESEARCH (Tool-Driven)

### Step 1.1: Macro Regime Classification

**Tools to use:**
- `fred_search()`: Find relevant economic indicators
- `fred_get_series()`: Pull time series data

*See FRED Tool Guidance section in your prompt for efficiency rules and recommended query parameters.*

**What to analyze:**
- **Fed Funds Rate**: Rising (hawkish) or falling (dovish)? Recent trend?
- **10Y Treasury Yield**: Above/below 4%? Inverted curve (compare to DGS2)?
- **CPI Inflation**: Accelerating or decelerating? Above/below 2% target?
- **Unemployment Rate**: Near historic lows or rising? Trend direction?
- **GDP Growth**: Expansion or contraction? Recent quarters?
- **Leading Indicators**: Positive or negative trend? Recent direction?

**Output classification:**
- **Expansion**: Low unemployment, positive growth, moderate inflation
- **Slowdown**: Growth decelerating, unemployment rising, inflation mixed
- **Recession**: Negative growth, rising unemployment, falling inflation
- **Recovery**: Growth turning positive, unemployment falling, inflation low

### Step 1.2: Market Regime Analysis

**Note:** The market context pack already provides:
- Trend classification (bull/bear based on SPY vs 200d MA)
- Volatility regime (VIX-based: low/normal/elevated/high)
- Sector leadership (top 3 and bottom 3 sectors vs SPY)
- Market breadth (% sectors above 50d MA)
- Factor premiums (momentum, quality, size, value vs growth)

**Your task:** Review the provided market context and optionally:
- Verify specific data points if they seem surprising
- Drill deeper into sectors/factors relevant to your strategy ideas
- Get additional data for specific stocks/ETFs you're considering
- Check recent news for context on market events

**Tools available:**
- `stock_get_historical_stock_prices()`: For specific stocks/ETFs
- `stock_get_yahoo_finance_news()`: For recent headlines
- `stock_get_stock_info()`: For company/ETF details

*See yfinance Tool Guidance section for tool capabilities and usage patterns.*

### Step 1.3: Pattern Learning (Composer)

**Tools to use:**
- `composer_search_symphonies(query="...")`: Search for strategies

**What to search:**

Based on Step 1.2 regime:
- If bull + low vol: "momentum strategy", "growth stocks", "tech focused"
- If bull + high vol: "defensive rotation", "quality focus", "low volatility"
- If bear + high vol: "bonds", "gold", "inverse ETF", "hedged"
- If bear + low vol: "dividend", "value", "defensive sectors"

**What to extract:**
- Asset selection patterns (which ETFs/stocks are popular?)
- Rebalancing frequency (how often do they rebalance?)
- Conditional logic (do they use VIX thresholds, momentum filters?)
- Weighting schemes (equal weight, market cap, inverse vol?)

**Output:** Note 3-5 successful patterns that match current regime

---

## PHASE 2: GENERATE (Framework-Driven)

### Step 2.0: Asset Research & Exploration (Optional)

**BEFORE ideating candidates, optionally explore available assets beyond what's in the context pack:**

The context pack provides comprehensive data on:
- ✅ **Sector ETFs:** XLK, XLF, XLU, XLE, XLV, XLY, XLP, XLI, XLB, XLC, XLRE
- ✅ **Benchmarks:** SPY, QQQ, AGG, VIX
- ✅ **Macro data:** Interest rates, inflation, employment, etc.
- ✅ **Factor premiums:** Momentum, quality, value vs growth, size

**If you're considering strategies with assets NOT in the context pack, research them now:**

```python
# Example 1: Individual stock concentration
# Research specific stocks for competitive moat analysis
stock_get_historical_stock_prices(symbol="NVDA", period="1y")
stock_get_stock_info(symbol="NVDA")  # P/E, market cap, dividend

# Example 2: Factor ETF strategies
# Compare factor ETF performance and characteristics
stock_get_historical_stock_prices(symbol="VTV", period="1y")  # Value
stock_get_historical_stock_prices(symbol="MTUM", period="1y") # Momentum

# Example 3: Dividend/yield strategies
# Get current yields for yield-focused strategies
stock_get_stock_info(symbol="VYM")   # High Dividend Yield ETF
stock_get_stock_info(symbol="SCHD")  # Dividend Aristocrats

# Example 4: Pattern exploration (optional but valuable)
# Understand proven strategy patterns on the platform
composer_search_symphonies(query="momentum sector rotation")
composer_search_symphonies(query="defensive VIX rotation")
```

**This step is OPTIONAL.** You can:
- Skip if using only context pack assets (sector ETFs, benchmarks)
- Use tools now to explore before ideating
- Use tools later during Step 2.1 if you discover data gaps mid-generation

**If you used tools in Step 2.0, document your findings:**

```markdown
### Research Findings (Step 2.0):

**Assets Explored:**
- Individual Stocks: [e.g., NVDA (P/E 45, AI accelerator market leader), AMD (P/E 38, datacenter growth)]
- Factor ETFs: [e.g., VTV (30d return +2.1%), MTUM (30d return +5.3%)]
- Dividend ETFs: [e.g., VYM (yield 3.2%), SCHD (yield 3.5%, higher quality)]
- Composer Patterns: [e.g., Top momentum strategies use monthly rebalance + 3-5 assets]

**Key Insights:**
[1-3 sentences summarizing what you learned that will inform your candidates]

**Data Gaps Identified:**
[Note any additional data needs that emerged during research]
```

**THEN proceed to Step 2.1 (Ideate 5 Candidates)**

### Step 2.1: Ideate 5 Candidates

Using insights from the context pack and optional Step 2.0 research, brainstorm candidates across different dimensions:

**Dimension Grid (ensure coverage):**

| Edge Type | Archetype | Concentration | Regime Bet | Rebalance |
|-----------|-----------|---------------|------------|-----------|
| Behavioral | Momentum | Focused (3-5) | Pro-cyclical | Daily |
| Structural | Mean Reversion | Balanced (6-10) | Counter-cyclical | Weekly |
| Informational | Carry | Diversified (11-15) | Tactical | Monthly |
| Risk Premium | Directional | Mixed | Hedged | Quarterly |

**Example Combinations:**
1. **Momentum + Focused + Pro-cyclical** → "Top 3 sectors by 3m momentum, monthly rebalance"
2. **Carry + Diversified + Tactical** → "Dividend aristocrats + bonds, shift on VIX spikes"
3. **Risk Premium + Balanced + Hedged** → "60/40 with VIX overlay for dynamic hedging"
4. **Structural + Focused + Counter-cyclical** → "Oversold sectors mean reversion"
5. **Behavioral + Diversified + Pro-cyclical** → "Growth momentum with quality filter"

### Step 2.2: Apply Edge Articulation Framework

For each candidate, complete:

**Template:**
```
Candidate [N]: [Name]

Edge: [Specific inefficiency - e.g., "Momentum persistence in sector rotation"]

Why it exists: [Mechanism - e.g., "Institutional capital flows lag sector trends by 2-4 weeks"]

Why now: [Regime fit - cite Phase 1 data - e.g., "Current strong breadth (75%) + low VIX (14) = momentum works"]

Archetype: [momentum|mean reversion|carry|directional|volatility|multi-strategy]

Assets: [List tickers]
Weights: [Specify allocation]
Rebalance: [Frequency]

Failure mode: [Specific condition - e.g., "VIX > 25 for 10+ days → momentum reverses"]
```

### Step 2.3: Ensure Diversity

**Diversity Checklist (run after all 5 candidates):**

- [ ] At least 3 different edge types (behavioral, structural, informational, risk premium)
- [ ] At least 3 different archetypes (momentum, mean reversion, carry, directional, volatility)
- [ ] At least 1 focused (≤5 assets) and 1 diversified (≥10 assets)
- [ ] At least 1 pro-cyclical and 1 counter-cyclical
- [ ] At least 3 different rebalancing frequencies

**If any checklist item fails:** Revise the least compelling candidate to increase diversity.

---

## WORKED EXAMPLES

**⚠️ WARNING: These are ABSTRACT TEMPLATES for learning structure - DO NOT copy ticker lists or strategy names.**
**Your candidates must use YOUR research findings from Step 2.0 gap analysis, NOT these placeholder examples.**

### Abstract Example Regime: [Use YOUR context pack data]

**Research Findings Template:**
- Macro: [Your macro regime from context pack]
- Market: [Your market regime: trend, volatility, breadth]
- Leadership: [Your top 3 sectors from context pack]
- Weakness: [Your bottom 3 sectors from context pack]
- Factors: [Your factor premiums from context pack]

### Example Pattern 1: Momentum Archetype
```
Name: "[ARCHETYPE] + [DIFFERENTIATOR]"
  → NOT "Tech Momentum Leaders" - create your own name

Edge: [Your specific momentum inefficiency - be precise]
Why it exists: [Your causal mechanism - cite research if available]
Why now: [Your regime fit - cite YOUR context pack data]
Archetype: Momentum

Assets: [YOUR top performers from research - Step 2.0]
  → NOT pre-determined tickers - use your gap analysis results
  → Example format: If your research found Healthcare, Tech, Financials leading,
     use those - don't copy someone else's Energy, Utilities, Staples

Weights: [YOUR allocation logic]
Rebalance: [YOUR frequency based on edge timescale]

Failure mode: [YOUR specific trigger - cite context pack thresholds]
```

### Example Pattern 2: Carry/Yield Archetype
```
Name: "[ARCHETYPE] + [DIFFERENTIATOR]"
  → Create based on YOUR strategy specifics

Edge: [Your yield/carry inefficiency]
  → If using dividend ETFs, you MUST call stock_get_stock_info in Step 2.0 for yields
Why it exists: [Your causal mechanism]
Why now: [Your regime fit - cite YOUR context pack]
Archetype: Carry

Assets: [YOUR dividend/yield instruments from Step 2.0 research]
  → Example: If researching dividend ETFs, call tools for VYM, SCHD, DVY, etc.
  → Then select based on actual data, not assumptions

Weights: [YOUR allocation]
Rebalance: [YOUR frequency - typically quarterly for carry]

Failure mode: [YOUR specific condition]
```

### Example Pattern 3: Volatility/Tactical Archetype
```
Name: "[ARCHETYPE] + [TRIGGER]"
  → Base on YOUR specific volatility logic

Edge: [Your volatility regime inefficiency]
  → VIX data IS in context pack - cite actual current VIX level
Why it exists: [Your mechanism]
Why now: [Your regime - what's current VIX from context pack?]
Archetype: Volatility

Assets: [YOUR tactical allocation assets]
  → If using non-standard defensive assets beyond AGG/TLT, call tools in Step 2.0

Weights: [YOUR dynamic logic]
  → Define YOUR threshold and allocations based on research
Rebalance: [YOUR frequency]

Failure mode: [YOUR whipsaw risk or breakdown condition]
```

### Example Pattern 4: Mean Reversion Archetype
```
Name: "[ARCHETYPE] + [TARGET]"
  → Describe YOUR mean reversion target

Edge: [Your overreaction/oversold inefficiency]
  → Context pack has sector performance - identify YOUR laggards
Why it exists: [Your behavioral/structural mechanism]
Why now: [Your dispersion metric from context pack]
Archetype: Mean Reversion

Assets: [YOUR underperformers from context pack sector_leadership.laggards]
  → Example: If context pack shows XLF, XLC, XLB as laggards, explain WHY you think
     they'll revert (not just "they're down")

Weights: [YOUR allocation]
Rebalance: [YOUR frequency]

Failure mode: [YOUR structural decline risk]
```

### Example Pattern 5: Multi-Strategy Archetype
```
Name: "[STRATEGY_1] + [STRATEGY_2] [COMBINATION]"
  → Describe YOUR specific multi-strategy blend

Edge: [Your diversification + factor tilt logic]
  → If using factor ETFs, you MUST call tools in Step 2.0 for historical data
Why it exists: [Your correlation structure + factor premium evidence]
Why now: [Your regime supporting multiple edges]
Archetype: Multi-strategy

Assets: [YOUR blend from Step 2.0 research]
  → If using MTUM, QUAL, USMV, etc. - fetch their data first
  → Then explain why THIS combination given YOUR research

Weights: [YOUR allocation across strategies]
Rebalance: [YOUR frequency]

Failure mode: [YOUR correlation breakdown scenario]
```

---

## DETAILED WORKED EXAMPLE: Full Implementation with Complex Logic Tree

**This example shows EXACTLY how to implement a conditional strategy with proper logic_tree structure.**

### Context Pack Data (Example):
- Current VIX: 17.44 (normal regime)
- Trend: Strong bull (SPY +12.8% above 200d MA)
- Volatility regime: Normal
- Market breadth: 75% sectors above 50d MA

### Strategy: VIX Inversion Defensive Rotation

**Edge:** VIX spikes above 22 trigger institutional defensive rotation with 2-4 day lag due to committee-based rebalancing constraints

**Step-by-Step Implementation Planning:**

1. **Requires conditional logic?** YES (VIX trigger mentioned)
2. **Triggers identified:**
   - VIX > 22 → Defensive mode (bonds/gold)
   - VIX < 18 for 2 consecutive days → Growth mode (equities)
   - 18 ≤ VIX ≤ 22 → Transitional/balanced mode
3. **Weight derivation:** Static within each mode (defensive = equal weight bonds/gold, growth = 50/30/20 equity split)
4. **Rebalancing frequency:** Daily (volatility edge requires fast response to regime changes)

**COMPLETE Strategy Object:**

```python
Strategy(
  name="VIX Inversion Defensive Rotation",

  thesis_document="""
  Market Analysis: Current VIX at 17.44 represents normal volatility regime in a strong bull market (SPY +12.8% above 200d MA, breadth at 75%). Historical analysis shows VIX spikes above 22 trigger mechanical defensive rotation by institutional investors with 2-4 day lag.

  Edge Explanation: When VIX crosses 22, risk parity funds have mechanical deleveraging triggers, but most institutional mandates use weekly or monthly rebalancing committees that cannot react intraday. This creates a 2-4 day window where bonds (TLT) and gold (GLD) rally before broader institutional flows catch up. The edge exists due to governance constraints at large institutions requiring committee approval for allocation changes.

  Regime Fit: Currently in growth mode (VIX 17.44, bull market), but positioned to rotate defensively when VIX exceeds 22. Strong breadth (75%) and low volatility support equity allocation until trigger threshold breached. Recent events show no elevated volatility catalysts, making current growth positioning appropriate.

  Risk Factors: Primary risk is whipsaw if VIX oscillates around 22 threshold. Mitigated via hysteresis logic requiring VIX < 18 for 2 consecutive days before re-entering growth mode. Expected max drawdown 8-12% during sustained volatility spikes (VIX > 30 for 10+ days) when defensive rotation fails to protect. Strategy underperforms in grinding bear markets with moderate volatility (VIX 18-22 sustained).
  """,

  rebalancing_rationale="""
  My daily rebalancing implements the VIX rotation edge by checking volatility threshold every market day and shifting allocation when VIX crosses 22 (defensive mode) or drops below 18 for 2 days (growth mode). Daily frequency is required because the edge exists in the 2-4 day institutional rebalancing lag - weekly or monthly rebalancing would miss the opportunity window entirely. This mechanically buys defensive assets (TLT, GLD) during VIX spikes before broader institutional flows drive prices up, exploiting the rebalancing committee delay documented in the thesis. The hysteresis logic (requiring 2 days below 18 to exit defensive) prevents whipsaw from rapid VIX oscillations.

  Weights derived using mode-based allocation: Defensive mode uses equal weights (0.50 TLT, 0.30 GLD, 0.20 BIL) justified by equal conviction in bonds and gold during volatility spikes. Growth mode uses 0.50 SPY, 0.30 QQQ, 0.20 AGG based on bull market regime favoring large cap (SPY) over pure growth (QQQ), with 20% bond allocation for stability. Transitional mode (18 < VIX < 22) uses balanced 0.40/0.40/0.20 to maintain flexibility.
  """,

  assets=["SPY", "QQQ", "AGG", "TLT", "GLD", "BIL"],

  weights={},  # Empty because weights are dynamic based on VIX regime

  rebalance_frequency="daily",

  logic_tree={
    "condition": "VIX > 22",
    "if_true": {
      # Defensive mode: High volatility
      "assets": ["TLT", "GLD", "BIL"],
      "weights": {"TLT": 0.50, "GLD": 0.30, "BIL": 0.20},
      "comment": "VIX spike - rotate to defensive assets before institutional flows"
    },
    "if_false": {
      "condition": "VIX < 18 AND days_below_18 >= 2",
      "if_true": {
        # Growth mode: Low volatility confirmed (hysteresis)
        "assets": ["SPY", "QQQ", "AGG"],
        "weights": {"SPY": 0.50, "QQQ": 0.30, "AGG": 0.20},
        "comment": "Low volatility confirmed for 2+ days - growth allocation"
      },
      "if_false": {
        # Transitional mode: Moderate volatility or just dropped below 18
        "assets": ["SPY", "AGG", "BIL"],
        "weights": {"SPY": 0.40, "AGG": 0.40, "BIL": 0.20},
        "comment": "Transitional regime (18 ≤ VIX ≤ 22) - balanced allocation"
      }
    }
  }
)
```

**Why This Implementation Is Coherent:**

✅ **Logic Tree Completeness:** Thesis mentions "VIX crosses 22" and "VIX < 18" → logic_tree implements nested VIX conditions with three distinct modes

✅ **Rebalancing Alignment:** Volatility edge with 2-4 day institutional lag → daily rebalancing (PASS auto-reject matrix - volatility edges require daily/weekly)

✅ **Weight Derivation:** Explicit derivation in rebalancing_rationale:
- Defensive mode: Equal weights (0.50/0.30/0.20) justified by equal conviction
- Growth mode: 50/30/20 split based on bull regime favoring large cap
- Transitional mode: 40/40/20 balanced allocation

✅ **Hysteresis Logic:** "days_below_18 >= 2" prevents whipsaw explicitly addressed in Risk Factors section - this is how you implement sophisticated trigger logic

✅ **Internal Consistency:**
- Thesis says "daily" → rebalance_frequency = "daily" ✓
- Thesis describes three modes → logic_tree implements three branches ✓
- Thesis mentions 2-day confirmation → logic_tree has "days_below_18 >= 2" ✓

✅ **No Contradictions:**
- No "buy-and-hold" claim + rebalancing frequency mismatch
- No "quarterly" in thesis vs "daily" in field
- rebalancing_rationale frequency matches rebalance_frequency field

**This is the implementation standard for conditional strategies. Use this as your reference.**

---

**Key Principle:** The abstract patterns above show STRUCTURE (how to think about edges, archetypes, failure modes).
Your actual candidates must be based on:
1. YOUR context pack data (current regime, sectors, factors)
2. YOUR Step 2.0 research findings (if tools were used)
3. YOUR original thinking (not copying these examples)

**If your final candidates look similar to these examples, you've failed the diversity requirement.**

---

## ANTI-PATTERNS: Common Diversity Failures

### ❌ Anti-Pattern #1: Same Archetype, Different Tickers

**BAD Example (FAIL - All Momentum):**
```
Candidate 1: Tech Momentum Leaders (XLK, XLY, XLC)
Candidate 2: Sector Momentum Rotation (XLF, XLI, XLE)
Candidate 3: Growth Momentum Focus (QQQ, VUG, MTUM)
Candidate 4: Large Cap Momentum (SPY, VOO, IVV)
Candidate 5: Quality Momentum Blend (QUAL, SIZE, USMV)
```

**Problem:** All 5 candidates are momentum strategies with different assets = FAIL diversity requirement

**Fix:** Ensure at least 3 different archetypes across your 5 candidates:
- Momentum (1-2 candidates)
- Mean Reversion (1-2 candidates)
- Carry/Yield (1 candidate)
- Volatility/Tactical (1 candidate)
- Directional/Multi-strategy (1 candidate)

---

### ❌ Anti-Pattern #2: Template Weight Copying

**BAD Example (FAIL - Repeating Weight Patterns):**
```
Candidate 1: {XLK: 0.40, XLY: 0.35, XLF: 0.25}
Candidate 2: {NVDA: 0.40, AMD: 0.35, AVGO: 0.25}
Candidate 3: {SPY: 0.30, QQQ: 0.30, AGG: 0.25, TLT: 0.15}
Candidate 4: {VYM: 0.30, QUAL: 0.30, USMV: 0.25, AGG: 0.15}
Candidate 5: {XLE: 0.40, XLU: 0.30, XLP: 0.30}
```

**Problem:** All use round numbers (0.25, 0.30, 0.35, 0.40) suggesting template copying, not thesis-driven allocation

**Fix:** Derive weights from your edge mechanism:
- **Momentum edge:** Weight by momentum strength (e.g., 0.48, 0.32, 0.20 if top performer is significantly stronger)
- **Equal edge strength:** Equal weight justified (0.333, 0.333, 0.334)
- **Risk parity:** Inverse volatility weights (varies by asset - e.g., 0.42, 0.28, 0.18, 0.12)
- **Conviction-based:** Larger weight to higher conviction (e.g., 0.50, 0.30, 0.20)

---

### ❌ Anti-Pattern #3: Fixed Rebalance Frequency

**BAD Example (FAIL - All Monthly):**
```
Candidate 1: Momentum edge → monthly rebalance
Candidate 2: Mean reversion edge → monthly rebalance
Candidate 3: Carry edge → monthly rebalance
Candidate 4: Volatility edge → monthly rebalance
Candidate 5: Directional edge → monthly rebalance
```

**Problem:** Rebalance frequency should match edge timescale, not be uniform across all strategies

**Fix:** Match rebalancing to your edge mechanism:
- **Carry/yield edge:** Quarterly or longer (yields are slow-moving)
- **Momentum edge:** Weekly to monthly (medium-term persistence)
- **Volatility edge:** Daily to weekly (fast regime changes)
- **Mean reversion edge:** Depends on reversion timescale (2-week reversion → weekly rebalance)
- **Value edge:** Monthly to quarterly (fundamentals change slowly)

---

### ❌ Anti-Pattern #4: Placeholder Thinking (Mad Libs Strategy)

**BAD Example (FAIL - Template Substitution):**
```
Name: "Momentum + Tech Focus"
Edge: [Generic momentum description]
Why it exists: [Generic behavioral bias explanation]
Assets: [Top 3 sectors from context pack]
```

**Problem:** Filling in template slots without original thinking - just replacing "[ARCHETYPE]" with "Momentum" and "[DIFFERENTIATOR]" with "Tech Focus"

**Fix:** Generate genuinely novel strategy names and theses:
- **Not:** "Momentum + Tech Focus" (template fill-in)
- **Yes:** "VIX Inversion Defensive Rotation" (describes specific mechanism)
- **Not:** "Value + Dividend" (generic combination)
- **Yes:** "Rate Cut Financial Positioning" (regime-specific thesis)

**Your strategy name should describe the SPECIFIC inefficiency you're exploiting, not just archetype + sector.**

---

### ❌ Anti-Pattern #5: Asset Count Uniformity

**BAD Example (FAIL - All 3-4 Assets):**
```
Candidate 1: 3 assets (XLK, XLY, XLF)
Candidate 2: 4 assets (NVDA, AMD, AVGO, INTC)
Candidate 3: 3 assets (SPY, QQQ, AGG)
Candidate 4: 4 assets (VYM, QUAL, USMV, AGG)
Candidate 5: 3 assets (XLE, XLU, XLP)
```

**Problem:** All candidates have similar concentration (3-4 assets), no exploration of diversification dimension

**Fix:** Vary concentration based on edge and conviction:
- **Focused (3-5 assets):** High-conviction company-specific edges
- **Balanced (6-10 assets):** Sector/factor diversification with active tilts
- **Diversified (11-15 assets):** Broad market exposure with systematic reweighting

**At minimum, have 1 focused (<= 5 assets) and 1 diversified (>= 10 assets) candidate.**

---

### ✅ Good Diversity Example (PASS)

```
Candidate 1: Momentum + 3 tech stocks + weekly momentum-weighted + 0.50/0.30/0.20
Candidate 2: Mean Reversion + 3 oversold sectors + monthly equal-weight + 0.33/0.33/0.33
Candidate 3: Carry + 12 dividend stocks + quarterly buy-hold + varied weights
Candidate 4: Volatility + 4 defensive assets + daily VIX-triggered + dynamic allocation
Candidate 5: Multi-strategy + 8 mixed assets + threshold rebalance + risk parity weights
```

**Why this passes:**
- ✅ 5 different archetypes (momentum, mean-rev, carry, vol, multi)
- ✅ Varied concentration (3, 3, 12, 4, 8 assets)
- ✅ Different rebalance frequencies (weekly, monthly, quarterly, daily, threshold)
- ✅ Varied weight derivation (momentum-weighted, equal, varied, dynamic, risk parity)
- ✅ Original names describe specific mechanisms

---

## COMMON MISTAKES & FIXES

### Mistake 0: Fetching Too Much Data (CRITICAL - Causes Token Overflow)
**Wrong:** Calling FRED tools without `limit` parameter
**Fix:** Always use `limit` parameter (see FRED Tool Guidance section in your prompt)
**Why:** Without `limit`, FRED returns ALL historical data, causing token overflow!

### Mistake 1: Speculation Without Tool Data
**Wrong:** "I think tech will outperform"
**Fix:** "Phase 1 data shows XLK +22% (90d) vs SPY +15%, momentum factor +2.3%, VIX 14 = momentum regime confirmed"

### Mistake 2: Vague Edge
**Wrong:** "This strategy follows momentum"
**Fix:** "6-month sector momentum persists for 3-6 months due to institutional quarterly rebalancing lag (structural edge)"

### Mistake 3: No Diversity
**Wrong:** 5 candidates all use tech-heavy momentum with monthly rebalancing
**Fix:** Ensure 3+ different edge types, archetypes, and varied rebalancing

### Mistake 4: False Diversification
**Wrong:** {"QQQ": 0.30, "TQQQ": 0.25, "XLK": 0.25, "MSFT": 0.20} (all correlated >0.9)
**Fix:** Check correlations; true diversification requires <0.6 correlation

### Mistake 5: No Failure Modes
**Wrong:** "This strategy works in all conditions"
**Fix:** "Failure mode: VIX > 30 for 10+ days → defensive rotation → expect -15% drawdown"

---

## QUALITY GATES (Before Submission)

### Gate 1: Research Completeness
- [ ] Called fred_search and fred_get_series (≥3 indicators)
- [ ] **ALL fred_get_series calls used `limit` parameter** (MANDATORY - prevents token overflow)
- [ ] Called stock_get_historical_stock_prices (≥SPY, VIX, 5 sectors)
- [ ] Called composer_search_symphonies (≥2 searches)
- [ ] ResearchSynthesis produced with tool citations

### Gate 1a: Data Efficiency (Token Management)
- [ ] **All FRED calls followed efficiency rules** (see FRED Tool Guidance section)
- [ ] Every fred_get_series call included `limit` parameter
- [ ] Every fred_search call included `limit` parameter
- [ ] No tool calls fetching excessive data (causing token overflow)

### Gate 2: Edge Quality
- [ ] All 5 candidates have specific edge (not "buy stocks that go up")
- [ ] All edges classified (behavioral/structural/informational/risk premium)
- [ ] All have "why now" tied to Phase 1 research data
- [ ] All have realistic failure modes

### Gate 3: Diversity
- [ ] ≥3 different edge types
- [ ] ≥3 different archetypes
- [ ] ≥1 focused (≤5 assets) and ≥1 diversified (≥10 assets)
- [ ] ≥1 pro-cyclical and ≥1 counter-cyclical
- [ ] ≥3 different rebalancing frequencies

### Gate 4: Platform Compliance
- [ ] All weights sum to 1.0
- [ ] No single asset >50%
- [ ] All tickers valid (EQUITIES::XXX//USD or valid ETF)
- [ ] No direct shorts (use SH, PSQ if needed)
- [ ] Rebalance frequency specified

### Gate 5: Output Format
- [ ] Exactly 5 Strategy objects
- [ ] Each has: name, assets, weights, rebalance_frequency
- [ ] logic_tree present (empty {} if static allocation)
- [ ] No duplicate ticker sets

---

## EXECUTION CHECKLIST

**Before starting:**
- [ ] Received market_context parameter
- [ ] Loaded system prompt (candidate_generation_system.md)
- [ ] MCP tools available (fred, yfinance, composer)

**Phase 1 (RESEARCH):**
- [ ] Macro regime classified (expansion/slowdown/recession/recovery)
- [ ] Market regime classified (trend, volatility, breadth, leadership)
- [ ] Composer patterns identified (3-5 examples)
- [ ] ResearchSynthesis JSON produced

**Phase 2 (GENERATE):**
- [ ] 5 candidates ideated across diversity dimensions
- [ ] Edge Articulation Framework applied to each
- [ ] Mental Models Checklist completed for each
- [ ] Diversity validated across all 5
- [ ] All quality gates passed

**Final:**
- [ ] Returned List[Strategy] with exactly 5 candidates
- [ ] All validation rules satisfied
- [ ] Ready for Stage 2 (Edge Scoring)

---

## TIPS FOR SUCCESS

1. **Follow FRED efficiency rules:** Token overflow is the #1 cause of failure. See FRED Tool Guidance section for required parameters. This is NOT optional!
2. **Start with tools, not intuition:** Always pull data first, generate candidates second
3. **Be specific about edges:** "Momentum" is vague; "6-month sector momentum persists 3-6 months due to institutional rebalancing lag" is specific
4. **Think in regimes:** What works in strong bull + low vol is different from high vol
5. **Embrace diversity:** Your job is to explore the possibility space, not pick the winner yet
6. **Be honest about failure modes:** Every edge breaks under some conditions; enumerate them
7. **Cite your sources:** Every claim should reference tool output (e.g., "FRED:FEDFUNDS shows...", "yfinance:SPY 90d return = ...")
8. **Be efficient with data:** Fetch only what you need. Recent data (last 1-2 years) is usually sufficient for regime classification.

**Remember:** You're a research analyst generating candidates for evaluation. Quantity (5 diverse options) + quality (clear edges) + rigor (tool-based) + efficiency (smart data fetching) = success.
