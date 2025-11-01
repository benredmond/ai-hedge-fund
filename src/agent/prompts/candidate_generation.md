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

### Step 2.1: Ideate 5 Candidates

Using Research Synthesis from Phase 1, brainstorm candidates across different dimensions:

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

### Example Regime: Strong Bull + Low Volatility + Growth Leadership

**Phase 1 Research (abbreviated):**
- Macro: Expansion (low unemployment 3.8%, GDP growth 2.5%, inflation moderate 3.2%)
- Market: Bull (SPY +15% YTD, >200d MA), Low vol (VIX 14), Strong breadth (80% sectors >50d MA)
- Leadership: XLK (+22%), XLY (+18%), XLF (+16%)
- Weakness: XLE (-5%), XLU (+3%), XLP (+5%)
- Factors: Momentum +2.3%, Quality +0.8%, Growth > Value by 8%
- Composer: Top strategies use momentum filters, tech overweight, monthly rebalance

### Example Candidate 1: Momentum Concentration
```
Name: "Tech Momentum Leaders"

Edge: Momentum persistence in sector rotation
Why it exists: Institutional capital flows lag sector trends by 2-4 weeks due to quarterly rebalancing
Why now: Strong breadth (80%) + low VIX (14) + growth leadership = momentum regime confirmed by Phase 1 data
Archetype: Momentum

Assets: ["XLK", "XLY", "XLF"]  # Top 3 sectors by 90d return
Weights: {"XLK": 0.40, "XLY": 0.35, "XLF": 0.25}  # Weight by momentum strength
Rebalance: monthly

Failure mode: VIX > 25 for 10+ days → momentum reverses → expect 12-18% drawdown
```

### Example Candidate 2: Carry + Diversification
```
Name: "Quality Dividend Carry"

Edge: Dividend yield premium + quality factor resilience
Why it exists: Institutional demand for yield + quality screens for balance sheet strength
Why now: Low vol environment (VIX 14) + positive macro (expansion) = carry works, quality outperforming (+0.8% factor premium from Phase 1)
Archetype: Carry

Assets: ["VYM", "QUAL", "USMV", "AGG"]  # Dividend + quality + low vol + bonds
Weights: {"VYM": 0.30, "QUAL": 0.30, "USMV": 0.25, "AGG": 0.15}
Rebalance: quarterly

Failure mode: Rising rates (10Y yield > 5%) → dividend stocks underperform → expect 8-12% drawdown
```

### Example Candidate 3: Tactical Hedging (Counter-Cyclical)
```
Name: "VIX-Responsive Defensive"

Edge: Volatility spikes → defensive rotation lag → 2-5 day opportunity window
Why it exists: Risk-off flows take time to clear; bonds/gold rally after VIX crosses 20
Why now: Currently low vol (VIX 14) so positioned for growth, but vol spikes are regime-ending risk per historical patterns
Archetype: Volatility

Assets: ["SPY", "TLT", "GLD", "BIL"]
Weights: Dynamic based on VIX:
  - VIX < 20: {"SPY": 0.70, "TLT": 0.15, "GLD": 0.10, "BIL": 0.05}
  - VIX >= 20: {"SPY": 0.30, "TLT": 0.35, "GLD": 0.25, "BIL": 0.10}
Rebalance: daily (to respond to VIX changes)

Failure mode: Whipsaw (VIX oscillates around 20) → transaction costs erode returns
```

### Example Candidate 4: Mean Reversion (Counter-Cyclical)
```
Name: "Oversold Sector Rotation"

Edge: Extreme sector underperformance (>-15% vs SPY over 90d) mean reverts 65% of time
Why it exists: Sentiment overshoots fundamentals; institutional flows mechanically rebalance
Why now: Current regime shows high dispersion (energy -5%, utilities +3% vs SPY +15%) creating mean reversion opportunities
Archetype: Mean Reversion

Assets: ["XLE", "XLU", "XLP"]  # Bottom 3 sectors from Phase 1
Weights: {"XLE": 0.40, "XLU": 0.30, "XLP": 0.30}
Rebalance: monthly

Failure mode: Structural decline (e.g., energy transition) → mean reversion fails → expect -10% to -20% if thesis wrong
```

### Example Candidate 5: Multi-Strategy Balanced
```
Name: "60/40 Quality Momentum"

Edge: Diversification + systematic rebalancing discipline + quality/momentum tilts
Why it exists: Uncorrelated returns (stocks/bonds) + rebalancing bonus + factor premiums (quality +0.8%, momentum +2.3% from Phase 1)
Why now: Expansion regime supports stocks; bonds provide hedge; low vol allows modest risk
Archetype: Multi-strategy (directional + carry)

Assets: ["MTUM", "QUAL", "AGG", "TLT"]
Weights: {"MTUM": 0.30, "QUAL": 0.30, "AGG": 0.30, "TLT": 0.10}
Rebalance: quarterly

Failure mode: Simultaneous stock/bond selloff (stagflation) → correlation breaks → expect -15% to -25%
```

**Diversity check for examples:**
- Edge types: Momentum, Carry, Volatility, Mean Reversion, Multi-strategy ✓ (all different)
- Archetypes: Momentum, Carry, Volatility, Mean Reversion, Multi-strategy ✓ (all different)
- Concentration: 3 assets, 4 assets, 4 assets, 3 assets, 4 assets ✓ (all similar, could improve)
- Regime: Pro-cyclical, Pro-cyclical, Counter-cyclical, Counter-cyclical, Balanced ✓ (good mix)
- Rebalance: Monthly, Quarterly, Daily, Monthly, Quarterly ✓ (good mix)

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
