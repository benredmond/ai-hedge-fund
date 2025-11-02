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

### Step 2.0: MANDATORY Pre-Generation Gap Analysis

**BEFORE generating any Strategy objects, identify data gaps and fetch missing data:**

For EACH of your 5 candidate ideas:

1. **List the assets you're considering**
   - Example: ["NVDA", "AMD", "AVGO"] or ["VTV", "MTUM", "QUAL"]

2. **Check if data is in context pack**
   - ✅ **IN context pack:** Sector ETFs (XLK, XLF, XLU, etc.), SPY, QQQ, AGG, VIX, macro data
   - ❌ **NOT in context pack:** Individual stocks, factor ETFs, dividend yields, P/E ratios

3. **Identify gaps and call tools**
   ```python
   # Example: Stock concentration strategy
   if using ["NVDA", "AMD", "AVGO"]:
       stock_get_historical_stock_prices(symbol="NVDA", period="1y")
       stock_get_historical_stock_prices(symbol="AMD", period="1y")
       stock_get_historical_stock_prices(symbol="AVGO", period="1y")
       stock_get_stock_info(symbol="NVDA")  # Get fundamentals

   # Example: Factor ETF strategy
   if using ["VTV", "VUG", "MTUM"]:
       stock_get_historical_stock_prices(symbol="VTV", period="1y")
       stock_get_historical_stock_prices(symbol="VUG", period="1y")
       stock_get_historical_stock_prices(symbol="MTUM", period="1y")

   # Example: Dividend strategy
   if dividend/yield focus:
       stock_get_stock_info(symbol="VYM")  # Get dividend yield
       stock_get_stock_info(symbol="SCHD")

   # Always valuable: Pattern inspiration
   composer_search_symphonies(query="your strategy archetype")
   ```

4. **THEN proceed to Step 2.1**

**Validation:** If your candidate uses assets NOT in the context pack, you MUST call tools before generating the Strategy object. This ensures your thesis is grounded in actual data, not assumptions.

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

**Key Principle:** These patterns show STRUCTURE (how to think about edges, archetypes, failure modes).
Your actual candidates must be based on:
1. YOUR context pack data (current regime, sectors, factors)
2. YOUR Step 2.0 gap analysis (tools called for missing data)
3. YOUR original thinking (not copying these examples)

**If your final candidates look similar to these examples, you've failed the diversity requirement.**

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
