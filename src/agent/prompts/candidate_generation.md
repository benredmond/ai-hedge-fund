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

### Step 2.1: Asset Research & Exploration (Optional)

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
- Use tools later during Step 2.7 if you discover data gaps mid-generation

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

**THEN proceed to Step 2.2 (Edge Quantification Schema)**

---

### Step 2.2: Edge Quantification Schema (REQUIRED BEFORE IDEATION)

**BEFORE ideating any strategies, define quantitative expectations to prevent unfalsifiable claims and overfitting.**

**Schema Format:**
```
Edge Type | Expected Sharpe (0.5-2.0) | vs Benchmark | Max DD (-8% to -30%) | Win Rate (45-65%) | Timeframe (90d)
```

**Instructions:**
1. Complete this schema for ALL 5 candidates BEFORE writing any thesis or strategy details
2. Must specify benchmark comparison (SPY, QQQ, AGG, 60/40, or factor ETF)
3. Constraints enforce realism:
   - Sharpe range prevents overfitting signals
   - Drawdown range prevents "no risk" fantasy strategies
   - Win rate prevents "always wins" claims

**Example:**
```
Momentum      | 1.0-1.4 | vs SPY      | -18% to -25% | 52-58% | 90d
Mean-Rev      | 0.8-1.2 | vs SPY      | -12% to -18% | 55-62% | 90d
Volatility    | 1.2-1.8 | vs 60/40    | -10% to -15% | 48-54% | 90d
Carry         | 0.7-1.1 | vs AGG      | -15% to -22% | 50-60% | 90d
Directional   | 0.9-1.3 | vs QQQ      | -20% to -28% | 50-56% | 90d
```

**After completing quantification schema, proceed to Step 2.3 (Planning Matrix)**

---

### Step 2.3: Planning Matrix (COMPRESSED - REQUIRED CHECKPOINT)

**BEFORE ideating, plan each candidate using this inline format:**

**Format:** `Archetype | Conditional? (YES/NO) | Triggers (if YES) | Weight Method | Frequency | Rationale`

**Example:**
```
#1: Momentum | YES | VIX <20 & top 2 sectors by 30d return | Momentum-weighted | Weekly | Momentum persistence 2-4w
#2: Mean-Rev | NO | N/A | Equal-weight | Monthly | Oversold bounce, equal-weight amplifies
#3: Volatility | YES | VIX >22 → defense, VIX <18 → growth | Dynamic (logic_tree) | Daily | Fast regime shift response
#4: Carry | NO | N/A | Equal-weight | Quarterly | Dividend yield, low turnover preserves carry
#5: Directional | YES | 10Y yield <4% → financials | Static per branch | Monthly | Rate sensitivity, 1-month lag
```

**Validation (MANDATORY before proceeding):**
- At least 2/5 conditional (YES), 2/5 static (NO)
- All conditional strategies have triggers (not "N/A")
- Frequency matches edge timescale (momentum=weekly, carry=quarterly, volatility=daily)

**After completing planning matrix, proceed to Step 2.4 (Benchmark Comparison).**

**CRITICAL: You must output all 5 Strategy objects in a single List[Strategy] response. Do not generate them one at a time. Use progress markers (Step 2.6a) to track completion as you work through all 5 candidates.**

---

### Step 2.4: Active vs Passive Tradeoff Matrix (MANDATORY)

**For EACH candidate, complete this tradeoff analysis BEFORE writing the full thesis:**

**Why this matters:** If your active strategy loses to a passive ETF on 5+ dimensions, you're adding cost without value. This matrix forces honest evaluation.

**Tradeoff Matrix Template:**

| Dimension | Passive Alternative | Your Active Strategy | Winner | Justification |
|-----------|-------------------|---------------------|--------|---------------|
| **Simplicity** | [1 ETF, buy-hold] | [X assets, rebalance frequency] | [Passive/Mine] | [Complexity cost in effort/failure modes] |
| **Cost** | [Expense ratio %] | [ER% + turnover × spread = total%] | [Passive/Mine] | [Total cost difference in bps] |
| **Downside Protection** | [Historical max DD%] | [Expected max DD%] | [Passive/Mine] | [Drawdown improvement or sacrifice] |
| **Upside Capture** | [100% of market rally] | [X% capture (timing drag)] | [Passive/Mine] | [Upside you're willing to sacrifice] |
| **Regime Dependency** | [Works in all regimes] | [Requires X regime] | [Passive/Mine] | [Your regime assumptions] |
| **Alpha Potential** | [0% - pure beta] | [+X-Y% alpha target] | [Mine/Tied] | [Quantified edge in bps] |
| **Failure Risk** | [Cannot fail - market beta] | [Thesis risk: X breaks strategy] | [Passive/Mine] | [Failure mode probability] |

**Decision Criteria:**
- **Passive wins ≥5 dimensions:** ❌ REJECT - insufficient edge to justify costs
- **Mine wins ≥3 dimensions:** ✅ KEEP - justifiable tradeoffs
- **Split 3-4 or 4-3:** ⚠️ MARGINAL - include only if needed for diversity

For self-check questions on rebalancing method alignment, see system prompt lines 789-828.

---

### Step 2.5: Execution Cost Budget (MANDATORY for Daily/Weekly Strategies)

**IF rebalancing daily or weekly, THEN estimate friction:**

**Format:** `Strategy | Turnover% | Spread+Impact bps | Annual Friction% | Net Alpha`

**Example:**
```
#3 Volatility (daily): 250% turnover | 4 bps avg (sector ETFs) | 1.0% friction | 6% gross - 1% = 5% net
```

**Cost Guidelines:**
- **Mega-cap stocks** (AAPL, MSFT, GOOGL): 1-2 bps per trade
- **Sector ETFs** (XLF, XLE, XLK): 3-5 bps per trade
- **Small-cap stocks**: 10-20 bps per trade
- **Turnover** = Sum(|position changes|) / portfolio value annually
- **Annual friction** = Turnover × Avg spread

**Your task (for daily/weekly strategies ONLY):**
1. Estimated annual turnover (e.g., "250%" means assets turn over 2.5x per year)
2. Spread + impact cost per trade (bps)
3. Total friction budget (turnover × cost)
4. Net alpha after costs (gross alpha - friction)

**Evidence:** High-frequency strategies without cost discussion will trigger retry. Costs can exceed alpha by 2-10x (e.g., VIX strategy: 10% cost vs 5% alpha = underwater).

---

### Step 2.6: Leverage Justification (if using 2x/3x ETFs)

**Required:** Complete the 4-element justification per system prompt Priority 2B (lines 144-199):

1. **Convexity Advantage** - Why leverage amplifies your specific edge (not just "amplifies returns")
2. **Decay Cost Quantification** - Expected decay vs edge magnitude (edge alpha should be ≥5-10x decay cost)
3. **Drawdown Amplification** - Realistic worst-case: 2x = -18% to -40%, 3x = -40% to -65%
4. **Benchmark Comparison** - Why not unleveraged? (TQQQ vs QQQ, UPRO vs SPY, etc.)

**For 3x ETFs only:** Additional stress test (2022/2020/2008 analog) and exit criteria required (system lines 181-198).

**Approved ETFs:** SSO/UPRO, QLD/TQQQ, SOXL, TMF (2x/3x bull) | SH, PSQ, SPXU, SQQQ, SOXS (inverse). No exotic leveraged instruments.

**If ANY element missing → DO NOT use leverage for that candidate.**

---

### Step 2.6a: Progress Tracking (REQUIRED)

**After completing each candidate's Strategy object, output a progress marker:**

```
✓ Candidate N/5 complete: [Strategy Name]
```

**Example:**
```
[Generate Candidate #1...]

✓ Candidate 1/5 complete: Sector Momentum Top 3 Rotation

[Generate Candidate #2...]

✓ Candidate 2/5 complete: Dividend Yield with VIX Protection

[Continue for all 5...]

✓ Candidate 5/5 complete: Market Breadth Factor Rotation
```

These progress markers help track completion and provide better diagnostics if validation fails.

---

### Step 2.7: Ideate 5 Candidates

Using insights from the context pack and optional Step 2.0 research, brainstorm candidates across different dimensions:

**Dimension Grid (ensure coverage):**

| Edge Type | Archetype | Concentration | Regime Bet | Rebalance |
|-----------|-----------|---------------|------------|-----------|
| Behavioral | Momentum | Focused (3-5) | Pro-cyclical | Daily |
| Structural | Mean Reversion | Balanced (6-10) | Counter-cyclical | Weekly |
| Informational | Carry | Diversified (11-15) | Tactical | Monthly |
| Risk Premium | Directional | Mixed | Hedged | Quarterly |

**CRITICAL: Edge-Frequency Alignment**

**See System Prompt Priority 2 for complete edge-frequency alignment matrix.**

Common violations: Momentum+Quarterly (too slow), Mean-Rev+Daily/Weekly (whipsaw), Carry+Daily/Weekly/Monthly (destroys carry), Volatility+Monthly/Quarterly (too slow). Validate Planning Matrix (Step 2.3) against system prompt rules before generating.

**Example Combinations:**
1. **Momentum + Focused + Pro-cyclical** → "Top 3 sectors by 3m momentum, monthly rebalance"
2. **Carry + Diversified + Tactical** → "Dividend aristocrats + bonds, shift on VIX spikes"
3. **Risk Premium + Balanced + Hedged** → "60/40 with VIX overlay for dynamic hedging"
4. **Structural + Focused + Counter-cyclical** → "Oversold sectors mean reversion"
5. **Behavioral + Diversified + Pro-cyclical** → "Growth momentum with quality filter"

### Step 2.8: Apply Edge Articulation Framework

For each candidate, complete:

**Template:**
```
Candidate [N]: [Name]

Edge: [Specific inefficiency - e.g., "Momentum persistence in sector rotation"]

Why it exists: [Mechanism - e.g., "Institutional capital flows lag sector trends by 2-4 weeks"]

Why now: [Regime fit - cite Phase 1 data - e.g., "Current strong breadth (75%) + low VIX (14) = momentum works"]

Archetype: [momentum|mean reversion|carry|directional|volatility|multi-strategy]

Assets: [List tickers]
Weights: [Specify allocation - MUST derive from edge mechanism, see Weight Derivation Methods below]
Rebalance: [Frequency]

Failure mode: [Specific condition - e.g., "VIX > 25 for 10+ days → momentum reverses"]
```

**CRITICAL: Weight Derivation Methods**

**See System Prompt Priority 3 for weight derivation requirements and validation rules.**

Acceptable methods: momentum-weighted, equal-weight, risk-parity, conviction-based, dynamic (logic_tree). Round numbers (0.25, 0.30, 0.35) require explicit justification in rebalancing_rationale. Must show calculation or explain equal treatment.

**Example:** "Weights derived using momentum-weighting: XLK 4.09% → 0.54, XLY 2.1% → 0.28, XLF 1.5% → 0.18"

### Step 2.9: Adversarial Self-Critique (RSIP Reflection Checkpoint)

**As a skeptical portfolio manager, challenge each candidate with 3 questions:**

**Q1: Implementation Coherence** - "Where is [conditional logic] implemented in logic_tree?"
- Thesis mentions "if/when/rotate/threshold" → logic_tree MUST be populated
- Empty logic_tree with conditional thesis = **Priority 1 AUTO-REJECT**

**Q2: Weight Justification** - "Show the calculation for these exact weights."
- Round numbers (0.25, 0.33, 0.50) require explicit derivation
- Example: "XLK 4.09% → 4.09/(4.09+2.10+1.51) = 0.54"

**Q3: Edge Robustness** - "What breaks this, how fast, and expected drawdown?"
- Vague ("market crashes") = FAIL
- Specific ("VIX > 30 for 10+ days → -20% drawdown") = PASS

**Validation:** For each candidate, mark Q1/Q2/Q3 as ✅ PASS, ⚠️ WEAK, or ❌ FAIL. Fix all Priority 1 violations before proceeding.

See system prompt RSIP checklist (lines 382-423) for complete validation framework.

---

### Step 2.10: Ensure Diversity

**See System Prompt Diversity Requirements section for complete checklist.**

Key requirements:
- ≥3 different edge types (behavioral, structural, informational, risk premium)
- ≥3 different archetypes (momentum, mean reversion, carry, directional, volatility)
- ≥1 focused (≤5 assets) AND ≥1 diversified (≥10 assets)
- ≥1 pro-cyclical AND ≥1 counter-cyclical
- ≥3 different rebalancing frequencies

**CRITICAL: Correlation Anti-Pattern Check**

Scan for **Diversification Theater**: Portfolios with correlation >0.9 across all assets (e.g., QQQ+TQQQ+XLK+MSFT = all tech, false diversification). If claiming "diversified" but correlation >0.8 → either replace with uncorrelated assets (<0.6) OR revise thesis to acknowledge concentration.

**If any requirement fails:** Revise least compelling candidate to increase diversity.

---

## WORKED EXAMPLES

**Study the concrete examples below to learn implementation patterns. Use YOUR research findings, not copied tickers.**

For archetype fundamentals (static vs dynamic patterns), see system prompt lines 287-423.

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

## ADDITIONAL WORKED EXAMPLES: Concrete Implementations by Archetype

**THESE ARE COMPLETE, PRODUCTION-READY EXAMPLES showing EXACTLY how to implement different archetypes with proper logic_tree structure (where applicable).**

### Example 1: Momentum Archetype - Sector Momentum Rotation

**Context Pack Data (Example):**
- Current VIX: 14.8 (low volatility)
- Trend: Strong bull (SPY +18.3% above 200d MA)
- Breadth: 82% sectors above 50d MA (high breadth)
- Sector leaders (30d): XLK +4.09%, XLY +2.10%, XLF +1.51%
- Factor premiums: Momentum +2.3% (30d), strong momentum environment

**Complete Strategy Object:**

```python
Strategy(
  name="Sector Momentum Top 3 Rotation",

  thesis_document="""
  Market Analysis: Current strong bull market (SPY +18.3% above 200d MA) with high breadth (82% sectors >50d MA) and low volatility (VIX 14.8) creates ideal momentum environment. Momentum factor premium at +2.3% (30d) confirms persistence regime.

  Edge Explanation: Sector momentum persists for 4-8 weeks due to institutional capital allocation lag. Large funds have quarterly rebalancing mandates and monthly investment committee cycles, creating predictable flow patterns. When SPY is above 200d MA (bull market), top momentum sectors continue outperforming. When SPY falls below 200d MA (bear market), momentum breaks down and defensive rotation is required.

  Regime Fit: Current strong bull with SPY +18.3% above 200d MA confirms momentum regime. High breadth (82%) means broad participation, ideal for sector rotation. Low VIX (14.8) provides stable environment for momentum persistence.

  Risk Factors: Strategy fails when SPY crosses below 200d MA (momentum reversal), VIX spikes >25 (regime shift), or breadth collapses <50% (narrow market). Expected max drawdown 12-18% during trend reversal.
  """,

  rebalancing_rationale="""
  My weekly rebalancing implements conditional momentum allocation based on trend regime. WHEN SPY > 200d MA (bull regime): allocate 100% to top 3 momentum sectors (XLK, XLY, XLF based on current leaders) with weights proportional to 30d returns (0.50, 0.30, 0.20). WHEN SPY < 200d MA (bear regime): rotate 100% defensive to utilities and consumer staples (XLU 50%, XLP 50%) to preserve capital during momentum breakdown. This exploits the 2-4 week institutional rebalancing lag when trend regimes shift, allowing us to rotate defensively before broader institutional flows drive the move. Weekly frequency captures regime changes faster than monthly institutional committees.
  """,

  assets=["XLK", "XLY", "XLF", "XLU", "XLP", "SPY"],

  weights={},  # Empty - allocation determined by conditional logic_tree, not static

  rebalance_frequency="weekly",

  logic_tree={
    "condition": "SPY_price > SPY_200d_MA",
    "if_true": {
      "comment": "Bull regime - momentum allocation",
      "assets": ["XLK", "XLY", "XLF"],
      "weights": {"XLK": 0.50, "XLY": 0.30, "XLF": 0.20}  # Momentum-weighted based on 30d strength
    },
    "if_false": {
      "comment": "Bear regime - defensive rotation",
      "assets": ["XLU", "XLP"],
      "weights": {"XLU": 0.50, "XLP": 0.50}  # Equal defensive allocation
    }
  }
)
```

**Why This Implementation Is Coherent:**
- ✅ Archetype (momentum) matches edge (sector momentum persistence in bull markets)
- ✅ Conditional logic (SPY > 200d MA) creates regime-based rotation
- ✅ Rebalancing method ALIGNS with thesis (momentum in bull, defensive in bear)
- ✅ Frequency (weekly) captures regime changes before institutional flows
- ✅ Weights in if_true branch are momentum-weighted (0.50, 0.30, 0.20)
- ✅ Defensive rotation in if_false prevents drawdown during momentum breakdown
- ✅ Specific failure trigger (SPY < 200d MA) with quantified defensive response

---

### Example 2: Carry Archetype - Dividend Yield with VIX Protection

**Context Pack Data (Example):**
- Current VIX: 18.2 (normal volatility)
- Current 10Y Treasury: 4.1%
- Dividend Yield VYM (Vanguard High Dividend): 3.2% (from yfinance tool)
- Dividend Yield SCHD (Schwab Dividend Equity): 3.5% (from yfinance tool)
- Dividend Yield JEPI (JPMorgan Equity Premium Income): 7.8% (from yfinance tool)
- Market trend: Bull (SPY +8.4% above 200d MA)
- Recent events: "Fed holds rates steady, market stability supports income strategies"

**Complete Strategy Object:**

```python
Strategy(
  name="Dividend Yield with VIX Protection",

  thesis_document="""
  Market Analysis: Current environment (VIX 18.2, 10Y at 4.1%) favors dividend yield strategies with moderate volatility. High-quality dividend ETFs (VYM 3.2% yield, SCHD 3.5% yield, JEPI 7.8% yield) provide attractive income in stable market conditions. Bull trend (SPY +8.4% above 200d MA) supports equity income exposure, but elevated absolute VIX levels warrant defensive rotation capability.

  Edge Explanation: Carry edge from dividend yield premium with volatility protection. When VIX < 22 (stable regime), dividend stocks capture yield premium as institutions maintain equity exposure but retail investors focus on total return over income, creating systematic undervaluation of dividend payers. When VIX > 22 (stress regime), dividend stocks face drawdown risk as volatility spikes compress valuations faster than yield increases - rotating to cash-like defensive (BIL) preserves carry by avoiding drawdowns that take quarters to recover. Edge exists because income-focused investors maintain static allocations (no VIX triggers), while we dynamically protect capital during volatility spikes.

  Regime Fit: Current VIX 18.2 (normal) keeps portfolio in dividend allocation mode. VIX threshold at 22 chosen because historical analysis shows dividend ETF drawdowns accelerate when VIX exceeds 22 for 3+ consecutive days, indicating regime shift from normal volatility to stressed conditions. Bull trend (SPY +8.4%) supports equity dividend exposure, but VIX protection prevents carry destruction during volatility spikes.

  Risk Factors: Strategy fails if VIX oscillates around 22 creating whipsaw (frequent rotation destroys carry via transaction costs). Also fails if dividend cuts occur during recession while VIX remains < 22 (no defensive trigger but yield collapses). Expected max drawdown 8-12% during VIX spikes > 30 before defensive rotation completes, or during sustained VIX 20-21 regime where carry is threatened but no rotation triggers.
  """,

  rebalancing_rationale="""
  My quarterly rebalancing with conditional VIX rotation implements carry edge while preserving capital during volatility regimes. WHEN VIX < 22 (stable regime): allocate to high-yield dividend ETFs [VYM 35%, SCHD 35%, JEPI 30%] with equal weighting across quality names (VYM/SCHD) and higher yield tilt (JEPI). Weights derived from yield-quality tradeoff: VYM/SCHD = core quality dividend exposure (70% combined), JEPI = higher yield with covered call premium (30%). WHEN VIX > 22 (stress regime): rotate 100% to BIL (cash-like defensive) to preserve carry by avoiding dividend stock drawdowns during volatility spikes. Quarterly frequency aligns with carry archetype requirement (per Constitutional Constraints, carry forbidden from daily/weekly/monthly rebalancing) - low turnover preserves carry while allowing regime-based protection. VIX checked quarterly at rebalance dates, not daily, so rotation is strategic (regime shift) not tactical (day-to-day volatility).
  """,

  assets=["VYM", "SCHD", "JEPI", "BIL"],

  weights={},  # Empty - allocation determined by conditional VIX regime logic_tree

  rebalance_frequency="quarterly",

  logic_tree={
    "condition": "VIX < 22",
    "if_true": {
      "comment": "Stable volatility regime - dividend yield allocation",
      "assets": ["VYM", "SCHD", "JEPI"],
      "weights": {"VYM": 0.35, "SCHD": 0.35, "JEPI": 0.30}  # Quality tilt (70%) + yield tilt (30%)
    },
    "if_false": {
      "comment": "Elevated volatility regime (VIX >= 22) - defensive cash-like",
      "assets": ["BIL"],
      "weights": {"BIL": 1.00}  # Full defensive rotation to preserve carry
    }
  }
)
```

**Why This Implementation Is Coherent:**
- ✅ Archetype (carry) matches edge (dividend yield harvest with volatility protection)
- ✅ Conditional logic (VIX < 22 threshold) implements regime-based rotation
- ✅ Rebalancing frequency (quarterly) ALIGNS with carry archetype (low turnover preserves carry per Constitutional Constraints Priority 2)
- ✅ VIX threshold (22) justified with historical drawdown analysis in thesis_document
- ✅ Weights in if_true branch derived from yield-quality tradeoff (35/35/30)
- ✅ Defensive rotation (BIL) prevents carry destruction during volatility spikes
- ✅ Quarterly rebalancing (not daily/weekly/monthly) complies with carry archetype frequency constraints
- ✅ Specific failure modes (VIX whipsaw, dividend cuts without VIX trigger) quantified
- ✅ rebalancing_rationale explains WHY quarterly (Constitutional Constraints) and HOW VIX rotation works

---

### Example 3: Multi-Factor Archetype - Dynamic Factor Allocation

**Context Pack Data (Example):**
- Current VIX: 16.2 (normal volatility)
- Trend: Bull market (SPY +10.4% above 200d MA)
- Market breadth: 64% sectors above 50d MA (moderate-strong participation)
- Factor premiums (30d): Momentum +2.1%, Value +0.8%, Quality +1.3%, Size -0.4%
- Sector dispersion: 3.2% (moderate, not extreme)

**Complete Strategy Object:**

```python
Strategy(
  name="Market Breadth Factor Rotation",

  thesis_document="""
  Market Analysis: Current bull market (SPY +10.4% above 200d MA) with moderate-strong breadth (64% sectors >50d MA) and normal volatility (VIX 16.2) supports factor rotation strategy. Factor premiums show positive momentum (+2.1%), quality (+1.3%), and value (+0.8%), with size factor lagging (-0.4%) as typical in mid-cycle markets.

  Edge Explanation: Factor premiums exhibit regime-dependent performance based on market breadth. WHEN breadth > 60% (broad market participation): momentum and quality factors outperform as rising tide lifts quality boats and trends persist across sectors. WHEN breadth <= 60% (narrow leadership): value and size factors outperform as investors rotate to overlooked segments and mean-reversion dominates. This edge exists because most institutional factor allocators maintain static weights (equal-weight across factors or strategic tilts), missing the 4-8 week lag when breadth regime shifts trigger factor performance reversals. Academic research documents momentum works in high-breadth environments (Asness 1997), while value thrives in low-breadth dispersion regimes (Fama-French 2015).

  Regime Fit: Current breadth at 64% (above 60% threshold) favors momentum + quality allocation. Historical analysis shows when breadth > 60%, MTUM + QUAL outperform VLUE + SIZE by 4-7% over subsequent 30 days. Factor ETFs (VLUE, MTUM, QUAL, SIZE) provide pure factor exposure without stock-specific risk, enabling clean regime-based rotation.

  Risk Factors: Strategy fails if breadth oscillates around 60% threshold (creates whipsaw rotation). Also fails in extreme regimes: breadth > 85% (momentum becomes crowded/overextended) or breadth < 40% (value traps in structural decline). Expected max drawdown 14-18% during breadth regime transitions if rotation lags by 2+ weeks. Factor crowding risk if institutional flows catch up faster than historical 4-8 week lag (reduces edge).
  """,

  rebalancing_rationale="""
  My monthly rebalancing implements breadth-based factor rotation by checking market breadth (% S&P 500 sectors above 50d MA) at month-end and allocating accordingly. WHEN breadth > 60% (broad participation regime): allocate 45% momentum + 45% quality + 10% size to capture trend persistence and quality premium in rising markets. WHEN breadth <= 60% (narrow leadership regime): rotate to 45% value + 45% size + 10% quality to exploit mean-reversion and small-cap dispersion while maintaining quality anchor. Quality factor maintains 10-45% across regimes as regime-adaptive (positive premium in both environments, provides stability). This exploits the 4-8 week institutional rebalancing lag documented in thesis - when breadth crosses 60% threshold, we rotate before broader institutional factor flows adjust their static allocations. Monthly frequency captures regime changes (breadth typically persists 2-3 months) while avoiding whipsaw from weekly breadth noise.

  Weights derived using conviction-based allocation within each regime: In broad markets (>60% breadth), momentum + quality receive equal 45% weights (both thrive in participation environments), with 10% size as diversifier. In narrow markets (<=60% breadth), value + size receive equal 45% weights (both exploit dispersion/mean-reversion), with 10% quality as stability anchor. No intermediate regime needed - breadth is binary signal (broad vs narrow participation).
  """,

  assets=["VLUE", "MTUM", "QUAL", "SIZE"],

  weights={},  # Empty - allocation determined by breadth-based conditional logic_tree

  rebalance_frequency="monthly",

  logic_tree={
    "condition": "market_breadth > 60",  # Broad participation threshold (% sectors > 50d MA)
    "if_true": {
      "comment": "Broad market regime - momentum + quality factors",
      "assets": ["MTUM", "QUAL", "SIZE"],
      "weights": {"MTUM": 0.45, "QUAL": 0.45, "SIZE": 0.10}  # Trend + quality in rising tide
    },
    "if_false": {
      "comment": "Narrow leadership regime - value + size factors",
      "assets": ["VLUE", "SIZE", "QUAL"],
      "weights": {"VLUE": 0.45, "SIZE": 0.45, "QUAL": 0.10}  # Mean-reversion + small-cap in dispersion
    }
  }
)
```

**Why This Implementation Is Coherent:**
- ✅ Archetype (multi-factor) matches edge (regime-based factor rotation across multiple factors)
- ✅ Conditional logic (breadth > 60%) creates systematic regime-based allocation shift
- ✅ Factor ETFs [VLUE, MTUM, QUAL, SIZE] provide pure factor exposure per Alpha vs Beta framework (line 317)
- ✅ Weights shift dramatically between regimes (45/45/10 momentum+quality vs 45/45/10 value+size)
- ✅ Quality factor serves as regime-adaptive anchor (present in both branches at 10-45%)
- ✅ Monthly rebalancing captures factor rotation timescale (2-3 month breadth persistence) while avoiding weekly noise
- ✅ Explicit breadth threshold (60%) with documented factor performance differential (4-7% outperformance)
- ✅ Rebalancing rationale explains 4-8 week institutional lag exploitation (why monthly rotation works)
- ✅ Risk factors address whipsaw (breadth oscillation), extreme regimes (>85%, <40%), and crowding

---

### Example 4: Mean Reversion Archetype - Oversold Financial Stock Selection

**Context Pack Data (Example):**
- Current VIX: 22.1 (elevated volatility, fear spike)
- Trend: Bull (SPY +5.3% above 200d MA, slight pullback from highs)
- Sector performance (30d): XLF -8.2% (financials lagging), XLK +4.1%, SPY +1.2%
- Sector dispersion: 4.1% (elevated, mean-reversion opportunity)
- Recent events: "Regional bank fears drive financial selloff despite fortress balance sheets at mega-caps"

**Security Selection Workflow (CRITICAL for Mean Reversion):**
*(Applying system prompt Security Selection Framework, lines 597-623)*

1. **Universe Definition**: S&P 500 Financials (XLF constituents), focus on mega-cap banks
2. **Screening Criteria**:
   - P/E < sector average (11.2x per XLF ETF data)
   - 30-day return < -10% (oversold threshold)
   - Market cap > $100B (liquidity + quality filter)
   - Dividend yield > 2.5% (income support during recovery)
3. **Fundamental Analysis** (using stock_get_stock_info):
   - JPM: 8.5x P/E (vs 11.2x sector), fortress balance sheet, down 12% on contagion fears despite AAA credit
   - BAC: 9.1x P/E, solid capital ratios, down 11%, strong deposit franchise
   - WFC: 10.2x P/E, asset cap removed 2023, down 10%, rebuilding trust
   - C: 7.8x P/E (cheapest), international exposure risk, down 14%, highest risk-reward
4. **Ranking Mechanism**: Composite score = (Value Z-score + Quality Z-score + Oversold Z-score) / 3
   - JPM: 0.82 (top quality, moderate value)
   - BAC: 0.71 (balanced profile)
   - WFC: 0.63 (turnaround story)
   - C: 0.58 (highest risk, highest value)
5. **Selection Rationale**: Top 4 by composite score. JPM/BAC = core quality, WFC/C = value tilt.

**Complete Strategy Object:**

```python
Strategy(
  name="Oversold Financial Stock Selection",

  thesis_document="""
  Market Analysis: XLF sector down 8.2% in 30 days (vs SPY +1.2%) due to regional bank contagion fears, creating indiscriminate selloff in mega-cap banks despite fortress balance sheets. Sector dispersion at 4.1% (elevated) indicates mean-reversion setup. Individual stock analysis reveals mega-caps (JPM 8.5x P/E, BAC 9.1x P/E, WFC 10.2x P/E, C 7.8x P/E) trading below 11.2x sector average despite quality fundamentals.

  Edge Explanation: Mean-reversion edge operates at STOCK LEVEL, not sector level. Behavioral overreaction to regional bank fears creates temporary mispricing in unrelated mega-caps with different risk profiles. Edge exists because: (1) Institutional funds sold entire XLF exposure via ETF redemptions (indiscriminate), (2) Mega-cap fundamentals unchanged (fortress balance sheets, AAA credit), (3) Value buyers step in at P/E < 9x with 2.5%+ yields. Reversion catalyst is 30-60 day normalization as investors differentiate quality from risk.

  Why Individual Stocks vs XLF: XLF = equally weighted basket including 20+ financials (regional banks, insurance, brokers). Our edge is SECURITY SELECTION: identifying the 4 quality mega-caps mispriced by panic vs the sector ETF which includes risky names. JPM at 8.5x P/E with fortress balance sheet is NOT the same as regional banks at 15x P/E with deposit flight risk. This is alpha generation (stock selection) NOT beta exposure (sector rotation).

  Security Selection Process: From XLF universe (20+ stocks) → Screen for P/E < 11.2x, down >10%, cap >$100B, yield >2.5% → Fundamental analysis using stock_get_stock_info (balance sheets, credit ratings) → Composite ranking (value + quality + oversold) → Select top 4: [JPM, BAC, WFC, C]. Mean reversion is at STOCK level (oversold quality names recover), not sector level (entire XLF rebounds).

  Regime Fit: Elevated VIX (22.1) + bull trend (SPY +5.3% above 200d MA) supports quality stock selection during fear spikes. When panic subsides and investors differentiate quality, mean reversion activates over 30-60 days.

  Risk Factors: Strategy fails if regional bank crisis spreads to mega-caps (systemic contagion), Fed hikes 50+ bps extending financial stress, or recession triggers credit cycle deterioration. Stock-specific risk: WFC regulatory issues resurface, C international exposure worsens. Expected max drawdown 12-18% if crisis deepens or recovery takes 90+ days.
  """,

  rebalancing_rationale="""
  Monthly rebalancing captures mean-reversion at stock level while allowing 30-60 day recovery window. Equal-weight allocation (25% each) across [JPM, BAC, WFC, C] reflects composite ranking with quality tilt (JPM/BAC core 50%, WFC/C value tilt 50%). No conditional logic needed - edge is in the SELECTION (these 4 stocks vs XLF sector), not timing (market regime). Rebalance monthly to maintain equal weights as individual stocks recover at different rates. Frequency aligns with mean-reversion timescale (30-60 days for panic dissipation, value recognition). No defensive rotation - static allocation demonstrates security selection edge, not tactical timing.
  """,

  assets=["JPM", "BAC", "WFC", "C"],

  weights={"JPM": 0.25, "BAC": 0.25, "WFC": 0.25, "C": 0.25},  # Equal-weight, rebalanced monthly

  rebalance_frequency="monthly",

  logic_tree={}  # Static allocation - edge is SELECTION not TIMING
)
```

**Why This Implementation Is Coherent:**
- ✅ Archetype (mean-reversion) matches edge (oversold STOCK selection, not sector rotation)
- ✅ Security selection workflow documented: Universe → Screening → Analysis → Ranking → Selection
- ✅ Individual stocks [JPM, BAC, WFC, C] demonstrate alpha generation (specific mispricing)
- ✅ Thesis explicitly explains WHY stocks vs XLF ETF (differentiation within sector)
- ✅ Rebalancing rationale explains equal-weight derivation and monthly frequency alignment
- ✅ Frequency (monthly) allows 30-60 day stock-level recovery window (appropriate for mean reversion)
- ✅ No conditional logic needed - edge is in SELECTION (these 4 quality names), not timing
- ✅ Fundamental analysis cited (P/E ratios, balance sheets, credit quality) using stock_get_stock_info
- ✅ Risk factors address both systemic (crisis spread) and stock-specific (WFC/C issues)

**Key Learning: Alpha vs Beta**
- ❌ **WRONG**: [XLF] = sector beta exposure, passive, no security selection edge
- ✅ **CORRECT**: [JPM, BAC, WFC, C] = alpha generation via stock selection within financials
- Mean reversion REQUIRES identifying WHICH securities are mispriced, not just buying oversold sectors

---

**Key Principle:** The abstract patterns above show STRUCTURE (how to think about edges, archetypes, failure modes).
Your actual candidates must be based on:
1. YOUR context pack data (current regime, sectors, factors)
2. YOUR Step 2.0 research findings (if tools were used)

**IMPORTANT:** The examples above use EXAMPLE data for illustration. DO NOT attempt to verify or fetch the specific numbers shown in examples (e.g., "SPY +18.3%", "VIX 14.8"). Instead, use the ACTUAL data from YOUR context pack provided above. The examples show the STRUCTURE of conditional logic, not the specific thresholds to use.
3. YOUR original thinking (not copying these examples)

**If your final candidates look similar to these examples, you've failed the diversity requirement.**

---

## ANTI-PATTERNS: Common Diversity Failures

For foundational anti-patterns (Diversification Theater, Same Archetype, Template Weights, Vague Edge), see system prompt lines 870-897.

**Recipe-Specific Anti-Patterns (from validation failures):**

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

### ❌ Anti-Pattern #6: Leverage Without Justification

**Pattern:** Using 2x/3x ETFs without completing the 4-element justification framework.

**Why it fails:** "Using TQQQ for momentum" + "Expected max drawdown: -25%" = AUTO-REJECT
- Missing convexity explanation (why leverage amplifies YOUR edge)
- No decay quantification (3x decays 2-5% annually in sideways markets)
- Unrealistic drawdown expectations (3x = -40-65%, not -25%)
- No benchmark comparison (TQQQ vs QQQ alpha?)
- For 3x: missing stress test (2022 TQQQ -80%) and exit criteria

**Fix:** Complete all elements per Step 2.6 and system prompt Priority 2B (lines 144-199):
1. Convexity Advantage - edge window < decay threshold
2. Decay Cost - quantified, justified by alpha (6-9x)
3. Drawdown Amplification - realistic: 2x = -40%, 3x = -65%
4. Benchmark Comparison - specific alpha target vs 1x
5. Stress Test (3x only) - cite 2020/2022 with back-test
6. Exit Criteria (3x only) - specific triggers with thresholds

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

## STEP 2.11: PRE-SUBMISSION VALIDATION SUMMARY (RSIP Plan Checkpoint)

**BEFORE submitting your final List[Strategy] output, complete this final validation summary:**

This is your last checkpoint to ensure Constitutional Constraints compliance and diversity requirements are met. All prior RSIP checkpoints (Step 2.3 Planning Matrix, Step 2.9 Self-Critique) feed into this final verification.

### Constitutional Constraints Verification (MANDATORY)

Validate ALL 5 strategies against system prompt Constitutional Constraints (lines 57-286):

| Priority | Check | System Lines | Auto-Reject If |
|----------|-------|--------------|----------------|
| 1 | Implementation-Thesis Coherence | 73-113 | Conditional thesis + empty logic_tree |
| 2 | Edge-Frequency Alignment | 116-141 | Momentum+Quarterly, MeanRev+Daily, Carry+Weekly |
| 2B | Leverage Justification | 144-199 | Missing 4-element framework for 2x/3x ETFs |
| 3 | Weight Derivation Transparency | 202-220 | Round weights (0.25, 0.33) without derivation |
| 4 | Quantitative Expectations | 223-242 | Percentage claims without evidence/hypothesis |

### Architecture-Specific Verification

**Mean Reversion/Value Security Selection (Recipe requirement lines 580-658):**
- [ ] All Mean Reversion/Value strategies use individual stocks [TICKER, TICKER], NOT sector ETFs
- [ ] Security selection workflow documented in thesis: Universe → Screening → Analysis → Ranking → Selection
- [ ] If using sector ETFs (XLF, XLE) for Mean Reversion → ❌ FAIL - must use individual stocks

**Planning Matrix Consistency (Step 2.3 verification):**
- [ ] All conditional strategies flagged in Planning Matrix have implemented logic_tree
- [ ] Rebalancing frequencies match Planning Matrix commitments
- [ ] Weight methods align with archetypes as planned

### Diversity Requirements Verification

**See System Prompt Diversity Requirements section for master checklist.**

Verify: ≥3 edge types, ≥3 archetypes, ≥3 frequencies, ≥1 focused + ≥1 diversified, ≥1 pro-cyclical + ≥1 counter-cyclical.

### Final Submission Checklist

- [ ] **Exactly 5 Strategy objects** in List[Strategy] output format
- [ ] All Constitutional Constraints verified (Priorities 1-4 above)
- [ ] All Mean Reversion/Value strategies use individual stock selection
- [ ] Diversity requirements met (≥3 edge types, ≥3 archetypes, ≥3 frequencies)
- [ ] All strategies pass Planning Matrix consistency check
- [ ] No AUTO-REJECT violations present

**If ANY checkbox above is unchecked → Do not submit until fixed**

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
