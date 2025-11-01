# Charter Creation Recipe

Create a comprehensive investment charter that documents the selected strategy's rationale, expected behavior, and risk profile.

---

## WORKFLOW OVERVIEW

**Pre-Work: Parse Selection Context**
- Review SelectionReasoning (why winner, why others rejected)
- Review Edge Scorecard scores (institutional evaluation)

**Phase 1: Market Data Gathering (15-20 minutes)**
- Use FRED tools for macro regime
- Use yfinance tools for market regime
- Synthesize into regime classification

**Phase 2: Charter Writing (40-50 minutes)**
- Section 1: Market Thesis (grounded in tool data)
- Section 2: Strategy Selection (integrated with selection context)
- Section 3: Expected Behavior (scenarios)
- Section 4: Failure Modes (specific and measurable)
- Section 5: 90-Day Outlook (milestones)

---

## PRE-WORK: Understanding Selection Context

Before writing, parse the context from prior stages:

### SelectionReasoning Structure
```python
{
  "winner_index": 2,  # Which of 5 candidates won (0-4)
  "why_selected": "Momentum Leadership strategy selected for strong edge economics...",
  "tradeoffs_accepted": "Accepted higher volatility for better Sharpe ratio...",
  "alternatives_rejected": [
    "Candidate 0 (60/40 Balanced): Weak edge differentiation in current regime",
    "Candidate 1 (Defensive Rotation): Lower Edge Scorecard (18.5 vs winner's 21.5)",
    "Candidate 3 (Mean Reversion): Misaligned with bull+low-vol regime",
    "Candidate 4 (Risk Parity): Lower conviction on multi-factor timing"
  ],
  "conviction_level": 0.85
}
```

### Edge Scorecard Structure
```python
{
  "thesis_quality": 4.2,
  "edge_economics": 4.5,
  "risk_framework": 3.8,
  "regime_awareness": 4.7,
  "strategic_coherence": 4.3,
  "total_score": 21.5,  # out of 25
  "reasoning": "Strong momentum thesis with institutional validation..."
}
```

**Action**: Extract key facts for Strategy Selection section:
- Winner's name and edge type
- Why_selected summary (use verbatim)
- Edge scores (focus on highest dimensions)
- Alternatives rejected (use verbatim list)

---

## PHASE 1: Market Data Gathering

### Step 1.1: Gather Macro Indicators (FRED)

**Required calls:**
```python
fred_get_series(series_id="FEDFUNDS", observation_start="2025-01-01")
fred_get_series(series_id="DGS10", observation_start="2025-01-01")
fred_get_series(series_id="CPIAUCSL", observation_start="2024-01-01")  # 12-month lookback
fred_get_series(series_id="UNRATE", observation_start="2025-01-01")
```

**Additional based on strategy:**
- If bonds: DGS2, DGS30 (yield curve)
- If inflation-sensitive: T5YIE (5Y breakeven inflation)
- If growth-focused: GDP, USSLIND (leading indicators)

**Output**: Table of current values

| Indicator | Current Value | Date | Interpretation |
|-----------|---------------|------|----------------|
| Fed Funds | 5.50% | Oct 2025 | Restrictive but peaking |
| 10Y Yield | 4.25% | Oct 27, 2025 | Elevated but stable |
| CPI YoY | 3.2% | Sep 2025 | Moderating inflation |
| Unemployment | 3.8% | Sep 2025 | Near historic lows |

### Step 1.2: Gather Market Regime Data (yfinance)

**Required calls:**
```python
stock_get_historical_stock_prices(symbol="SPY", period="1y")
stock_get_historical_stock_prices(symbol="^VIX", period="3mo")
# For sector leadership:
stock_get_historical_stock_prices(symbol="XLK", period="6mo")  # Tech
stock_get_historical_stock_prices(symbol="XLF", period="6mo")  # Financials
stock_get_historical_stock_prices(symbol="XLE", period="6mo")  # Energy
# etc for all 9 sectors
```

**Analysis steps:**
1. **Trend**: SPY vs 200d MA → bull or bear
2. **Volatility**: VIX current level and 30d avg → low/normal/elevated/high
3. **Breadth**: Count sectors above 50d MA → strong/mixed/weak
4. **Leadership**: Rank sectors by 90d return → top 3 and bottom 3
5. **Factors**: Pull MTUM, QUAL, VTV, VUG → identify premiums

**Output**: Regime classification

```
Current Regime (as of Oct 27, 2025):
- Trend: Bull (SPY at 4520, 18% above 200d MA of 3835)
- Volatility: Low (VIX at 14.2, 30d avg 15.8)
- Breadth: Strong (8 of 9 sectors above 50d MA)
- Leadership: Tech +22%, Consumer Discretionary +18%, Financials +16%
- Weakness: Energy -5%, Utilities +3%, Consumer Staples +5%
- Factors: Momentum +2.3%, Quality +0.8%, Growth > Value by 8%
```

---

## PHASE 2: Charter Writing

### Section 1: Market Thesis (500-1000 words)

**Structure:**
```
1. Economic Regime (200-300 words)
   - Classification (expansion/slowdown/recession/recovery)
   - Key drivers with FRED citations
   - Forward implications

2. Market Regime (200-300 words)
   - Classification (trend, volatility, breadth)
   - Sector dynamics with yfinance citations
   - Factor environment

3. Why This Matters for Strategy (100-200 words)
   - Connect regime to strategy's edge
   - Explain alignment
```

**Template:**

```
**Economic Regime: [Classification]**

The US economy is in [expansion/slowdown/recession/recovery] as of October 2025. The Federal Reserve's policy rate sits at [X]% (FRED:FEDFUNDS, Oct 2025), indicating [hawkish/neutral/dovish] stance. The 10-year Treasury yield is [X]% (FRED:DGS10, Oct 27, 2025), [above/below] the fed funds rate, suggesting [normal/inverted] yield curve.

Inflation has [accelerated/moderated/stabilized] to [X]% year-over-year (FRED:CPIAUCSL, Sep 2025), [above/below] the Fed's 2% target. Employment remains [strong/mixed/weak] with unemployment at [X]% (FRED:UNRATE, Sep 2025), [near historic lows/elevated/rising].

[Forward implications: What does this regime mean for risk assets, bonds, etc.?]

**Market Regime: [Bull/Bear] + [Low/High] Volatility**

Equity markets show [strong/weak] trend characteristics. The S&P 500 trades at [level] (yfinance:SPY, Oct 27, 2025), [X]% [above/below] its 200-day moving average of [level], confirming [bull/bear] market status.

Volatility is [low/elevated] with the VIX at [X] (yfinance:^VIX, Oct 27, 2025), [below/above] its long-term median of 17. Market breadth is [strong/weak] with [X] of 9 sectors trading above their 50-day moving averages.

Sector leadership reveals [cyclical/defensive] positioning. Top performers include [XLK, XLY, XLF] with [+X%, +Y%, +Z%] 90-day returns (yfinance:sectors). Laggards include [XLE, XLU, XLP] with [+/-X%] performance, suggesting [growth/value] preference.

Factor analysis shows [momentum/quality/value/growth] premiums. [MTUM/QUAL/VTV/VUG] outperforms SPY by [X]%, indicating [trend-following/quality-seeking/value-hunting/growth-chasing] behavior.

**Why This Regime Favors [Strategy Name]**

[Explain 2-3 specific connections between regime characteristics and strategy's edge. E.g., "The combination of bull trend (SPY +18% above 200d MA) and low volatility (VIX 14.2) creates ideal conditions for momentum persistence, the core edge of this strategy. Historical patterns show 6-12 month momentum continues 3-6 months in low-vol bull markets due to institutional capital flow lags."]
```

### Section 2: Strategy Selection (400-800 words)

**Structure:**
```
1. Selection Summary (100-150 words)
   - Use SelectionReasoning.why_selected verbatim or paraphrased
   - State winner's name and edge type

2. Edge Validation (150-250 words)
   - Cite Edge Scorecard total score (out of 25)
   - Highlight 2-3 strongest dimensions with scores
   - Explain what makes edge institutionally credible

3. Comparative Analysis (100-200 words)
   - List 4 rejected alternatives with elimination reasons
   - Reference SelectionReasoning.alternatives_rejected
   - Cite Edge Scorecard comparison across candidates

4. Tradeoffs Accepted (50-100 words)
   - Use SelectionReasoning.tradeoffs_accepted
   - Be honest about what was sacrificed
```

**Template:**

```
**Selection Summary**

[Strategy Name] was selected from 5 candidates for its [edge type] approach. [Paste or paraphrase SelectionReasoning.why_selected]. This strategy scored [X.X]/25 on the institutional Edge Scorecard, passing all quality thresholds with conviction level [X]%.

**Edge Validation**

The institutional evaluation validated [Strategy Name]'s edge across five dimensions:
- **Edge Economics** ([X]/5): [Brief explanation of why this scored high]
- **Regime Awareness** ([X]/5): [Brief explanation]
- **[Highest dimension]** ([X]/5): [Brief explanation]

Total score: [X.X]/25 (minimum 15 required for deployment)

This edge is institutionally credible because [connect to academic research, market structure, or behavioral finance principle]. The strategy exploits [specific inefficiency] which persists due to [structural reason it hasn't been arbitraged away].

**Comparative Analysis**

This strategy outperformed 4 alternatives on Edge Scorecard evaluation:

1. **[Candidate 0 Name]**: [Elimination reason from alternatives_rejected]
2. **[Candidate 1 Name]**: [Elimination reason]
3. **[Candidate 3 Name]**: [Elimination reason]
4. **[Candidate 4 Name]**: [Elimination reason]

Edge Scorecard comparison:
- Winner: [X.X]/25 total score
- Next best: [X.X]/25
- Median: [X.X]/25

The winner's superior scores in [dimension 1] and [dimension 2] were decisive factors in the selection.

**Tradeoffs Accepted**

[Paste SelectionReasoning.tradeoffs_accepted]. We accept [higher volatility / concentration risk / rebalancing costs / etc.] in exchange for [higher expected returns / better regime alignment / clearer edge / etc.].
```

### Section 3: Expected Behavior (400-600 words)

**Structure:**
```
1. Best Case (100-150 words)
2. Base Case (100-150 words)
3. Worst Case (100-150 words)
4. Regime Transitions (100-150 words)
```

**Template:**

```
**Best Case: Regime Continuation**

Market conditions: [Bull/bear] trend continues, volatility remains [low/high], [sector/factor] leadership persists

Expected performance: Outperform SPY by [X-Y]%, outperform QQQ by [X-Y]%, match/beat 60/40 by [X-Y]%

Mechanism: [Explain WHY - e.g., "Momentum persistence compounds in low-vol environments as institutional flows lag trends by 2-4 weeks. With current VIX at 14.2 and sector correlation at 0.65, conditions support continued momentum."]

Probability assessment: [X]% likelihood over 90 days

**Base Case: Moderate Volatility**

Market conditions: [Describe most likely path based on forward reasoning]

Expected performance: Match SPY ± [X]%, outperform AGG by [X-Y]%, Sharpe ratio [X.X-Y.Y]

Key risks: [2-3 specific risks to monitor that could shift to worst case]

Probability assessment: [X]% likelihood over 90 days

**Worst Case: Regime Shift**

Market conditions: [Describe adverse scenario - connect to failure modes]

Expected drawdown: [-X% to -Y%] vs SPY [-Z%]

Recovery mechanism: [How strategy adapts - e.g., "Rebalancing into defensive sectors if VIX > 25; bonds provide downside cushion; expected recovery within 30-45 days as correlations normalize"]

Probability assessment: [X]% likelihood over 90 days

**Behavior During Regime Transitions**

Volatility spike (VIX crosses 25): [Expected behavior - e.g., "Momentum reversal risk; expect 5-8% drawdown in first week; defensive rotation in portfolio; reference Failure Mode 1"]

Trend reversal (SPY < 200d MA): [Expected behavior]

Sector rotation: [Expected behavior - monthly rebalancing may lag fast rotations]

Correlation regime change: [Expected behavior - diversification may increase/decrease]
```

### Section 4: Failure Modes (3-8 specific conditions)

**Format per mode:**
```
[N]. [DESCRIPTIVE NAME]
   Condition: [Measurable trigger with numbers]
   Impact: [Quantified consequence]
   Early Warning: [Observable signal before full trigger]
```

**Templates by Strategy Type:**

**Momentum Strategy:**
```
1. VIX REGIME SHIFT
   Condition: VIX rises above 30 and sustains for 10+ consecutive days
   Impact: Momentum reversal; expected drawdown 15-20%; sector rotation accelerates
   Early Warning: VIX crosses 25; sector correlation rises above 0.85; breadth falls below 40%

2. BREADTH COLLAPSE
   Condition: Fewer than 30% of sectors above 50-day moving average for 20+ days
   Impact: Momentum edge weakens; leader/laggard spread compresses; expected underperformance 5-10% vs SPY
   Early Warning: Breadth falls below 50%; sector dispersion below 3%
```

**Defensive/Carry Strategy:**
```
1. RATE SHOCK
   Condition: 10-year Treasury yield rises 100bps (1%) in 30 days or less
   Impact: Bond allocation suffers 10-15% loss; dividend stocks underperform; total portfolio impact -8-12%
   Early Warning: 10Y yield rises 50bps in 2 weeks; 2Y-10Y spread inverts further; Fed rhetoric shifts hawkish

2. INFLATION SURPRISE
   Condition: CPI prints 50bps above consensus for 2 consecutive months
   Impact: Real returns turn negative despite positive nominal; defensive sectors lag; expected -5-10% underperformance
   Early Warning: Core CPI re-accelerates; breakeven inflation rises 25bps; commodity prices surge
```

**Multi-Strategy/Balanced:**
```
1. CORRELATION BREAKDOWN
   Condition: Stock-bond correlation turns positive (>0.3) for 30+ consecutive days
   Impact: Diversification benefit evaporates; 60/40 logic breaks; drawdown amplified to -20-25%
   Early Warning: Correlation crosses 0; inflation expectations rise; Fed loses credibility; both stocks and bonds sell off simultaneously
```

**Worked Example (Momentum Strategy):**
```
1. VIX REGIME SHIFT (LOW → HIGH)
   Condition: VIX rises above 30 and sustains for 10+ consecutive days (currently VIX 14.2)
   Impact: Momentum reversal occurs; 6-12 month winners become losers; expected drawdown 15-20% as sector leadership collapses; tech/growth hit hardest
   Early Warning: VIX crosses 25 (first threshold); sector correlation rises above 0.85 (dispersion collapses); market breadth falls below 40% (leadership narrows)

2. BREADTH COLLAPSE
   Condition: Fewer than 30% of sectors above 50-day MA for 20+ consecutive days (currently 89%)
   Impact: Momentum edge weakens significantly; leader/laggard spread compresses from current 27% to <10%; expected underperformance 5-10% vs SPY as stock-picking dominates over sector bets
   Early Warning: Breadth falls below 50%; sector dispersion below 3%; large-cap factor (size) turns negative

3. SECTOR CORRELATION SPIKE
   Condition: Average pairwise correlation of top 3 sectors rises above 0.9 for 15+ days (currently 0.68)
   Impact: False diversification; concentration risk in correlated positions; amplified drawdown to -18-22% in stress scenario
   Early Warning: Correlation crosses 0.80; sector returns move in lockstep; macro factors dominate micro fundamentals

4. REBALANCING WHIPSAW
   Condition: Market regime changes (bull/bear or low/high vol) more than 3 times in 90 days
   Impact: Monthly rebalancing too slow; buy high/sell low repeatedly; transaction costs erode returns by 3-5%
   Early Warning: VIX oscillates around 20-25 range; sector leadership flips every 2-3 weeks; technical indicators give conflicting signals
```

### Section 5: 90-Day Outlook (300-500 words)

**Structure:**
```
1. Market Path Expectation (100-150 words)
2. Strategy Positioning (75-125 words)
3. Milestones (75-125 words)
4. Red Flags (50-100 words)
```

**Template:**

```
**Market Path Expectation**

Over the next 90 days (Oct 27, 2025 - Jan 27, 2026), the base case scenario anticipates [bull/bear] trend continuation with [low/moderate/high] volatility. Key events to monitor include:

- **November 7**: FOMC meeting - expect [rate decision and guidance]
- **November 12-26**: Q3 earnings season - tech sector estimates at [X]% growth
- **December 13**: CPI/PPI inflation data - consensus [X]% YoY
- **December 18**: Final FOMC meeting of 2025 - potential [guidance shift]
- **January 20**: Inauguration Day - policy uncertainty

Technical levels: SPY support at [level] (200d MA), resistance at [level]. VIX support at [level], concern threshold [level].

**Strategy Positioning**

[Strategy Name] is positioned for [base case scenario]. The [momentum/defensive/balanced] tilt favors [specific holdings] which benefit from [regime characteristics].

If market path shifts to [worst case], rebalancing triggers include [specific thresholds from failure modes]. Adjustments would involve [describe portfolio changes - e.g., "rotating from growth sectors (XLK, XLY) into defensive (XLU, XLP) if VIX > 25"].

Strategy review triggers:
- Conviction drops below 0.5 (currently [X])
- Edge Scorecard dimensions fall below 3.0
- Drawdown exceeds [-X]% (personal risk tolerance)
- Failure Mode [N] triggered

**Milestones**

Day 30 (Nov 27, 2025):
- Expected progress: [+X% to +Y%] relative to SPY
- Checkpoints: No failure modes triggered; VIX remains < 20; sector leadership stable
- Review: Assess FOMC impact; confirm momentum persistence

Day 60 (Dec 27, 2025):
- Expected progress: [+X% to +Y%] cumulative relative to SPY
- Checkpoints: Passed earnings season without correlation spike; breadth > 50%
- Review: Year-end rebalancing effects; tax-loss harvesting impact

Day 90 (Jan 27, 2026):
- Success criteria: Outperform SPY by [X]%+; Sharpe ratio > [Y]; max drawdown < [-Z]%
- Full assessment: Compare realized vs expected behavior; validate edge scorecard; decide on continuation

**Red Flags (Early Exit Signals)**

Monitor daily/weekly for these early warning signs from failure modes:
- **Daily**: VIX level, SPY vs 200d MA, sector breadth
- **Weekly**: Sector correlation, dispersion, factor premiums
- **Monthly**: Fed rhetoric, inflation data, earnings revisions

Immediate review triggers (exit consideration):
- Failure Mode 1 triggered (VIX > 30 for 10+ days)
- Drawdown exceeds [-X]% (2x expected)
- Regime classification changes (bull → bear)
- Edge thesis invalidated (e.g., momentum premium turns negative for 30+ days)

Exit criteria: If 2+ red flags trigger simultaneously, or single red flag persists 30+ days, initiate strategy review for potential reallocation or defensive pivot.
```

---

## WORKED EXAMPLE: Charter for Momentum Strategy

**Context:**
- **Winner**: "Tech Momentum Leaders" (Candidate 2)
- **SelectionReasoning.why_selected**: "Strong edge economics (4.5/5) and regime awareness (4.7/5) in current bull+low-vol regime; highest Edge Scorecard total (21.5/25)"
- **SelectionReasoning.alternatives_rejected**:
  - C0 (60/40): "Weak differentiation"
  - C1 (Defensive): "Lower Edge Scorecard (18.5/25)"
  - C3 (Mean Reversion): "Regime misalignment"
  - C4 (Risk Parity): "Lower conviction"
- **Edge Scorecard**: thesis_quality=4.2, edge_economics=4.5, risk_framework=3.8, regime_awareness=4.7, strategic_coherence=4.3, total=21.5

**Charter (abbreviated for example):**

### Market Thesis

**Economic Regime: Expansion**

The US economy remains in expansion as of October 2025. The Federal Reserve's policy rate sits at 5.50% (FRED:FEDFUNDS, Oct 2025), indicating restrictive but potentially peaking stance. The 10-year Treasury yield is 4.25% (FRED:DGS10, Oct 27, 2025), below the fed funds rate with a -125bp inversion, suggesting the market expects future rate cuts.

Inflation has moderated to 3.2% year-over-year (FRED:CPIAUCSL, Sep 2025), down from the 9% peak in 2022 but still above the Fed's 2% target. Employment remains strong with unemployment at 3.8% (FRED:UNRATE, Sep 2025), near historic lows and below the Fed's estimated NAIRU of 4.1%.

This configuration suggests late-cycle expansion: growth continues but policy remains tight, and the Fed is data-dependent. Risk assets face a dual regime where earnings growth supports equities but elevated rates cap multiples.

**Market Regime: Bull + Low Volatility**

Equity markets show strong trend characteristics. The S&P 500 trades at 4520 (yfinance:SPY, Oct 27, 2025), 18% above its 200-day moving average of 3835, confirming bull market status with broad-based participation.

Volatility is low with the VIX at 14.2 (yfinance:^VIX, Oct 27, 2025), well below its long-term median of 17 and in the bottom quartile historically. Market breadth is strong with 8 of 9 sectors trading above their 50-day moving averages (89% breadth).

Sector leadership reveals cyclical positioning. Top performers include Technology (XLK +22%), Consumer Discretionary (XLY +18%), and Financials (XLF +16%) with 90-day returns (yfinance:sectors). Laggards include Energy (XLE -5%), Utilities (XLU +3%), and Consumer Staples (XLP +5%), suggesting growth preference and risk-on sentiment.

Factor analysis shows momentum premiums. MTUM outperforms SPY by +2.3%, indicating trend-following behavior dominates. Quality (QUAL +0.8%) and Growth over Value (+8% spread) confirm the momentum/growth regime.

**Why This Regime Favors Tech Momentum Leaders**

The combination of bull trend (SPY +18% above 200d MA) and low volatility (VIX 14.2) creates ideal conditions for momentum persistence, the core edge of Tech Momentum Leaders. Historical patterns show 6-12 month sector momentum continues 3-6 months in low-vol bull markets due to institutional capital flow lags (quarterly rebalancing cycles).

Technology sector leadership (+22% vs SPY +15%) reflects structural tailwinds: AI investment cycles, cloud migration, and strong earnings growth. The 27% spread between leaders (XLK) and laggards (XLE) provides clear momentum signal with low noise (sector correlation 0.65), allowing monthly rebalancing to capture persistent trends without whipsaw.

Low VIX (14.2) indicates complacent put-buying, which historically precedes 2-4 month momentum extensions as fear remains suppressed and risk-seeking behavior compounds.

### Strategy Selection

**Selection Summary**

Tech Momentum Leaders was selected from 5 candidates for its sector momentum approach in Technology, Consumer Discretionary, and Financials. This strategy scored 21.5/25 on the institutional Edge Scorecard, passing all quality thresholds with conviction level 85%.

The selection rationale: "Strong edge economics (4.5/5) validates the structural basis for momentum persistence in institutional rebalancing cycles. Regime awareness (4.7/5) confirms exceptional alignment with current bull+low-vol environment. Edge Scorecard total of 21.5/25 significantly outperforms alternatives (median 19.5/25)."

**Edge Validation**

The institutional evaluation validated Tech Momentum Leaders' edge across five dimensions:
- **Edge Economics** (4.5/5): Exploits documented quarterly rebalancing lag in institutional capital flows; structural inefficiency persists due to compliance constraints on mid-quarter changes
- **Regime Awareness** (4.7/5): Exceptional fit with bull+low-vol regime; historical momentum persistence highest when VIX < 15 and breadth > 70%
- **Thesis Quality** (4.2/5): Clear articulation of 6-12 month momentum continuation due to flow dynamics

Total score: 21.5/25 (minimum 15 required for deployment)

This edge is institutionally credible because it aligns with academic research on momentum premiums (Jegadeesh & Titman, 1993) and exploits a structural market feature: institutional rebalancing operates on quarterly cycles while price trends evolve continuously, creating 2-4 week lags that monthly rebalancing can capture.

**Comparative Analysis**

This strategy outperformed 4 alternatives on Edge Scorecard evaluation:

1. **60/40 Balanced Portfolio**: Weak edge differentiation in current regime; generic allocation lacks exploitable inefficiency
2. **Defensive Rotation**: Lower Edge Scorecard (18.5/25 vs winner's 21.5/25); misaligned with bull market
3. **Oversold Sector Mean Reversion**: Regime misalignment (mean reversion underperforms in trending markets)
4. **Risk Parity Multi-Factor**: Lower conviction (0.65 vs 0.85) on multi-factor timing; complexity without commensurate edge

Edge Scorecard comparison:
- Winner: 21.5/25 (exceptional regime awareness 4.7/5, strong edge economics 4.5/5)
- Next best: 20.0/25
- Median: 19.5/25

The winner's superior scores in regime awareness and edge economics were decisive factors in the selection.

**Tradeoffs Accepted**

Accepted higher concentration (3 sectors vs diversified 9 sectors) and higher volatility (16% annualized vs 12% for balanced alternatives) in exchange for higher expected Sharpe ratio and clearer edge in current momentum regime. Monthly rebalancing (vs quarterly) introduces higher transaction costs (~0.5% annually) but captures momentum signals with shorter lag.

[Continue with sections 3-5...]

---

## QUALITY GATES (Before Submission)

### Gate 1: Selection Context Integration
- [ ] Strategy Selection section references SelectionReasoning.why_selected
- [ ] Cited Edge Scorecard total score + 2-3 dimension scores with values
- [ ] Listed all 4 rejected alternatives with specific elimination reasons
- [ ] Compared Edge Scorecard scores vs alternatives numerically
- [ ] Referenced SelectionReasoning.tradeoffs_accepted

### Gate 2: Tool Usage & Data Citation
- [ ] Called fred_get_series for ≥3 macro indicators
- [ ] Called stock_get_historical_stock_prices for SPY, VIX, ≥3 sectors
- [ ] Every claim cites tool + value + date (e.g., "FRED:FEDFUNDS 5.50%, Oct 2025")
- [ ] Market Thesis grounded in tool data, not speculation

### Gate 3: Failure Modes Quality
- [ ] 3-8 failure modes total
- [ ] Each has: Name + Condition (measurable) + Impact (quantified) + Early Warning (observable)
- [ ] No vague modes ("market crashes", "things go wrong")
- [ ] Connected to strategy mechanics (not generic risk)
- [ ] Early warnings cited in 90-Day Outlook red flags

### Gate 4: Structure & Length
- [ ] Market Thesis: 500-1000 words
- [ ] Strategy Selection: 400-800 words
- [ ] Expected Behavior: 400-600 words (best/base/worst + transitions)
- [ ] Failure Modes: 3-8 items in specified format
- [ ] 90-Day Outlook: 300-500 words (milestones included)
- [ ] Total: 1600-3700 words (substantive but focused)

### Gate 5: Tone & Framing
- [ ] Comparative framing (relative to benchmarks, not absolute predictions)
- [ ] Honest about uncertainty (scenarios, not certainties)
- [ ] Risk-aware (failure modes prominent, not hidden)
- [ ] Forward-looking (driven by Edge Scorecard, not historical backtests)
- [ ] Selection transparency (clear why THIS strategy vs alternatives)

---

## EXECUTION CHECKLIST

**Before starting:**
- [ ] Received SelectionReasoning, Edge Scorecard, All 5 candidates
- [ ] Parsed why_selected, alternatives_rejected, tradeoffs_accepted
- [ ] Identified winner's edge type and top scorecard dimensions

**Phase 1 (Market Data):**
- [ ] Called FRED for macro regime (≥3 indicators with values + dates)
- [ ] Called yfinance for market regime (SPY, VIX, ≥3 sectors with levels + dates)
- [ ] Synthesized regime classification (economic + market)

**Phase 2 (Writing):**
- [ ] Section 1 (Market Thesis): Tool-cited, regime-strategy connection
- [ ] Section 2 (Strategy Selection): Selection context integrated
- [ ] Section 3 (Expected Behavior): Best/base/worst + transitions
- [ ] Section 4 (Failure Modes): 3-8 specific, measurable modes
- [ ] Section 5 (90-Day Outlook): Milestones + red flags

**Final:**
- [ ] All quality gates passed
- [ ] Charter object ready to return
- [ ] Word counts in range for each section

---

## TIPS FOR SUCCESS

1. **Selection Context is Core**: The charter's value is explaining WHY this strategy. Use the SelectionReasoning verbatim or closely paraphrased.

2. **Cite Everything**: Every macro claim → FRED series + value + date. Every market claim → yfinance ticker + level + date.

3. **Failure Modes are Not Boilerplate**: Connect to strategy mechanics. Momentum strategy fails differently than carry strategy.

4. **Comparative Framing**: "Outperform SPY by 3-5%" not "Return 15%". Relative is honest, absolute is speculation.

5. **Scenarios Over Predictions**: "If X happens, expect Y" not "Y will happen". Acknowledge uncertainty.

6. **Milestones are Concrete**: "VIX remains <20" not "volatility stays calm". Measurable checkpoints.

**Remember:** You're documenting a selection decision and forward thesis, not making return guarantees. The charter succeeds when a reader understands the edge, the selection rationale, the risks, and the expected 90-day path.
