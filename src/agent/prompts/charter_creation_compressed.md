# Charter Creation Recipe (Compressed v1.0)

## Workflow Overview

1. **PARSE**: Extract SelectionReasoning + Edge Scorecard from prior stages
2. **ANALYZE**: Review context pack for current regime data
3. **WRITE**: Create 5-section charter following templates
4. **VALIDATE**: Run quality gates before returning

---

## Pre-Work: Parse Selection Context

### SelectionReasoning (cite in Section 2)
```python
{
  "winner_index": 2,
  "why_selected": "Strong edge economics (4.5/5)...",  # Use verbatim
  "tradeoffs_accepted": "Accepted higher volatility...",  # Use verbatim
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

3. **Why This Matters** (100-200 words)
   - Connect regime to strategy's edge
   - Explain alignment with current conditions

**Data Citation Example:**
"VIX at 17.44 (per `regime_snapshot.volatility.VIX_current.current`), indicating normal volatility regime favorable for momentum persistence."

### Section 2: Strategy Selection (400-800 words)

**Structure:**
1. **Selection Summary** (100-150 words)
   - Strategy name and edge type
   - Use SelectionReasoning.why_selected verbatim
   - Edge Scorecard total score + conviction level

2. **Edge Validation** (150-250 words)
   - Cite 2-3 highest dimension scores
   - Explain institutional credibility
   - Connect to regime alignment

3. **Comparative Analysis** (100-200 words)
   - List all 4 rejected alternatives (name + reason from alternatives_rejected)
   - Edge Scorecard comparison: Winner vs next best vs median

4. **Tradeoffs Accepted** (50-100 words)
   - Use SelectionReasoning.tradeoffs_accepted verbatim
   - Be honest about sacrifices

### Section 3: Expected Behavior (400-600 words)

**Structure:**

**Best Case** (100-150 words)
- Market conditions: Regime continuation
- Expected performance: vs SPY, QQQ, AGG
- Mechanism: WHY this scenario favors strategy
- Probability: X% likelihood

**Base Case** (100-150 words)
- Market conditions: Most likely path
- Expected performance: Sharpe ratio range
- Key risks to monitor
- Probability: X% likelihood

**Worst Case** (100-150 words)
- Market conditions: Adverse scenario
- Expected drawdown: [-X% to -Y%]
- Recovery mechanism
- Probability: X% likelihood

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

### Gate 1: Selection Context
- [ ] Referenced SelectionReasoning.why_selected
- [ ] Cited Edge Scorecard total + 2-3 dimensions
- [ ] Listed all 4 rejected alternatives
- [ ] Compared scores vs alternatives

### Gate 2: Data Citation
- [ ] Context pack used as primary source
- [ ] Specific values cited (not vague claims)
- [ ] Tools called ONLY for gaps

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

**Ignoring selection context:**
- Not using why_selected, alternatives_rejected verbatim

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
