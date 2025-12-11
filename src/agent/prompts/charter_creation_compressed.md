# Charter Creation Recipe (Compressed v1.0)

## CRITICAL: Date Grounding

**Use `metadata.anchor_date` from context pack for ALL dates.**
- The anchor_date is the current date for this charter
- 90-day outlook = anchor_date + 90 days
- DO NOT guess dates or use training data dates

## Workflow Overview

1. **PARSE**: Extract SelectionReasoning + Edge Scorecard from prior stages
2. **ANALYZE**: Review context pack for current regime data (note anchor_date)
3. **WRITE**: Create 5-section charter following templates
4. **VALIDATE**: Run quality gates before returning

---

## Pre-Work: Parse Selection Context

### SelectionReasoning (validate and enhance in Section 2)
```python
{
  "winner_index": 2,
  "why_selected": "Strong edge economics (4.5/5)...",  # Starting point - validate, enhance if weak
  "tradeoffs_accepted": "Accepted higher volatility...",  # Reference, may clarify
  "alternatives_rejected": ["C0: weak differentiation", ...],  # List all 4
  "conviction_level": 0.85
}
```

### Edge Scorecard (cite scores)
```python
{
  "thesis_quality": 4.2,
  "edge_economics": 4.5,
  "risk_framework": 3.8,
  "regime_awareness": 4.7,
  "strategic_coherence": 4.3,
  "total_score": 21.5  # out of 25
}
```

---

## Charter Section Templates

### Section 1: Market Thesis (500-1000 words)

**Structure:**
1. **Economic Regime** (200-300 words)
   - Classification: Expansion/Slowdown/Recession/Recovery
   - Key drivers: Fed funds (`macro_indicators.interest_rates`), 10Y yield, CPI, unemployment
   - Forward implications

2. **Market Regime** (200-300 words)
   - Trend: Bull/Bear (`regime_snapshot.trend.regime`)
   - Volatility: VIX level and regime (`regime_snapshot.volatility`)
   - Breadth: Sectors above 50d MA (`regime_snapshot.breadth`)
   - Leadership: Top/bottom sectors (`regime_snapshot.sector_leadership`)
   - Factors: Momentum, value vs growth (`regime_snapshot.factor_regime`)

3. **Why This Matters for THIS Strategy** (100-200 words)
   - What CATALYST will trigger the edge in the next 90 days? (Not just "conditions are favorable")
   - If mean-reversion: What evidence shows this level historically reverts? (not just "oversold")
   - If momentum: What sustains the trend vs exhaustion risk?
   - If regime contradicts performance (e.g., "value regime" but strategy underperforming): Address explicitly
   - **Horizon Check**: If edge typically requires > 90 days (e.g., value mean-reversion ~2-3 years), explain what compresses the timeline here
   - REQUIRED: Specific calendar catalyst (e.g., "FOMC Dec 18", "Tech earnings Nov 12-26", "Year-end rebalancing Dec 15-31") - not just "favorable conditions"

**Data Citation Example:**
"VIX at 17.44 (per `regime_snapshot.volatility.VIX_current.current`), indicating normal volatility regime favorable for momentum persistence."

### Section 2: Strategy Selection (400-800 words)

**Structure:**
1. **Selection Summary** (100-150 words)
   - Strategy name and edge type
   - Reference SelectionReasoning.why_selected as starting point (you may enhance/clarify)
   - Edge Scorecard total score + conviction level
   - **CRITICAL**: If thesis claims regime X favors this strategy BUT strategy is currently underperforming in that regime, you MUST address this contradiction:
     (a) Explain why underperformance is temporary (with evidence), OR
     (b) Acknowledge thesis weakness and adjust expectations accordingly

2. **Edge Validation** (150-250 words)
   - Cite 2-3 highest dimension scores
   - **REQUIRED - Quantify the edge**:
     - What alpha (%) do you expect vs benchmark over 90 days? Provide range, not point estimate (e.g., "base +3%, range -1% to +7%")
     - What are estimated transaction costs + slippage?
     - Is expected alpha > costs? (If marginal, acknowledge weak edge)
   - If claiming behavioral edge (e.g., "institutional rebalancing flows"): What evidence suggests this is exploitable at retail scale?
   - Connect to regime alignment

3. **Comparative Analysis** (100-200 words)
   - List all 4 rejected alternatives (name + reason from alternatives_rejected)
   - Edge Scorecard comparison: Winner vs next best vs median

4. **Tradeoffs Accepted** (50-100 words)
   - Use SelectionReasoning.tradeoffs_accepted verbatim
   - Be honest about sacrifices

### Section 3: Expected Behavior (400-600 words)

**Structure:**

**Best Case (if current regime continues)** (100-150 words)
- Market conditions: Regime continuation
- Expected performance: vs SPY, QQQ, AGG
- Mechanism: WHY this scenario favors strategy

**Base Case (most likely path)** (100-150 words)
- Market conditions: Most likely path
- Expected performance: Sharpe ratio range
- Key risks to monitor

**Worst Case (adverse regime shift)** (100-150 words)
- Market conditions: Adverse scenario
- Expected drawdown: [-X% to -Y%]
- Recovery mechanism

**DO NOT include arbitrary probabilities (25%/50%/25%).**
Instead, use one of:
- Historical base rates: "Bull markets historically persist 65% of time after reaching this premium to 200d MA"
- Explicit uncertainty: "We assign roughly equal probability to continuation and transition, with base-rate favor to continuation"
- No probabilities: Just describe the scenarios without likelihood claims

**Regime Transitions** (100 words)
- VIX spike (>25): Expected behavior
- Trend reversal: Expected behavior
- Sector rotation: Expected behavior
- Correlation change: Expected behavior

### Section 4: Failure Modes (3-8 items)

**Format per mode:**
```
[N]. [NAME]
   Condition: [Measurable trigger with numbers]
   Impact: [Quantified consequence]
   Early Warning: [Observable signal before trigger]
```

**Example - Momentum Strategy:**
```
1. VIX REGIME SHIFT
   Condition: VIX rises above 30 and sustains for 10+ consecutive days
   Impact: Momentum reversal; expected drawdown 15-20%
   Early Warning: VIX crosses 25; sector correlation > 0.85

2. BREADTH COLLAPSE
   Condition: Fewer than 30% of sectors above 50d MA for 20+ days
   Impact: Momentum edge weakens; underperformance 5-10% vs SPY
   Early Warning: Breadth falls below 50%; sector dispersion < 3%
```

**Example - Defensive/Carry Strategy:**
```
1. RATE SHOCK
   Condition: 10Y yield rises 100bps in 30 days
   Impact: Bond allocation suffers 10-15% loss
   Early Warning: 2Y yield rises 50bps in 2 weeks

2. INFLATION SURPRISE
   Condition: CPI prints 50bps above consensus for 2 consecutive months
   Impact: Real returns negative; expected -5-10% underperformance
   Early Warning: Core CPI re-accelerates; breakeven inflation +25bps
```

### Section 5: 90-Day Outlook (300-500 words)

**Structure:**

**Market Path Expectation** (100-150 words)
- Base case trajectory
- Key events: Fed meetings, earnings, economic releases
- Technical levels and thresholds

**Strategy Positioning** (75-100 words)
- How positioned for expected path
- Adjustment triggers if path changes
- Review triggers

**Milestones** (75-100 words)
- Day 30: Expected progress, checkpoints
- Day 60: Mid-point assessment criteria
- Day 90: Success criteria (what defines "worked")

**Red Flags** (50-75 words)
- Early warnings from failure modes
- Metrics to monitor daily/weekly
- Exit criteria (2+ red flags = review)

---

## Quality Gates

### Gate 1: Selection Context + Validation
- [ ] Referenced and validated SelectionReasoning.why_selected (addressed contradictions if any)
- [ ] Cited Edge Scorecard total + 2-3 dimensions
- [ ] Quantified expected alpha vs transaction costs
- [ ] Listed all 4 rejected alternatives
- [ ] Compared scores vs alternatives

### Gate 2: Data Citation + Catalyst
- [ ] Context pack used as primary source
- [ ] Specific values cited (not vague claims)
- [ ] Tools called ONLY for gaps
- [ ] Concrete catalyst identified with 90-day timeline (not just "conditions favorable")

### Gate 3: Failure Modes
- [ ] 3-8 modes total
- [ ] Each has: Condition + Impact + Early Warning
- [ ] Connected to strategy mechanics

### Gate 4: Character Limits
- [ ] market_thesis < 8000 chars
- [ ] strategy_selection < 8000 chars
- [ ] expected_behavior < 8000 chars
- [ ] outlook_90d < 4000 chars

**Fix all failures before returning Charter.**

---

## Anti-Patterns to Avoid

**Vague failure modes:**
- "Market crashes" (no threshold)
- "Strategy underperforms" (circular)

**Missing data citation:**
- "Volatility is low" → "VIX at 14.2 per context pack"

**Uncritical pass-through:**
- Citing upstream reasoning without validating contradictions
- Claiming edges without quantifying expected alpha vs costs
- "Oversold" or "favorable conditions" without specific catalyst/timeline

**Exceeding character limits:**
- market_thesis > 8000 chars = Pydantic validation failure

---

## Execution Checklist

**Before starting:**
- [ ] Received SelectionReasoning, Edge Scorecard, all 5 candidates
- [ ] Parsed why_selected, alternatives_rejected, tradeoffs_accepted

**Writing:**
- [ ] Section 1: Market Thesis - context pack cited
- [ ] Section 2: Strategy Selection - SelectionReasoning integrated
- [ ] Section 3: Expected Behavior - best/base/worst + transitions
- [ ] Section 4: Failure Modes - 3-8 specific, measurable
- [ ] Section 5: 90-Day Outlook - milestones + red flags

**Final:**
- [ ] All quality gates passed
- [ ] Character limits verified
- [ ] Charter object ready to return
