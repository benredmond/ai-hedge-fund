# Charter Creation Recipe

Create an investment thesis pitch memo for the selected strategy. This is a synthesis stage - you're distilling the selection reasoning into a compelling narrative, and you may refine the strategy if your reasoning supports it.

---

## Your Task

You've received:
- **5 candidate strategies** from generation stage
- **Edge Scorecards** evaluating each candidate
- **Selection reasoning** explaining why the winner was chosen
- **Market context pack** with current regime data

Now synthesize this into a charter - a pitch memo that articulates the thesis, the edge, and what would prove it wrong.

**Important**: This is a synthesis stage, not just documentation. If as you write the thesis you realize the strategy should be refined (different weights, different rebalancing, etc.), you can make those changes. The charter captures your best thinking, not just the prior stage's output.

---

## Synthesis, Not Recitation

The #1 failure mode is data dumping. Don't recite the context pack - synthesize it.

<wrong>
"The Federal Reserve's policy rate sits at 3.88% (November 2025), having declined from prior cycle peaks, while the 10-year Treasury yield at 4.17% reflects market confidence in sustained growth without overheating. The 10Y-2Y spread of +70bps confirms a healthy yield curve. CPI inflation has moderated to 2.71% year-over-year, approaching the Fed's target, while unemployment at 4.6% indicates a cooling but still robust labor market."
</wrong>

This tells the reader nothing they couldn't get from the context pack.

<right>
"We're in a disinflationary growth regime - rates easing (fed funds 3.88%), inflation converging to target (CPI 2.71%), healthy yield curve (+70bps). This is the sweet spot for value: rate pressure easing favors duration-sensitive assets, while no recession risk means we don't need to hide in defensives."
</right>

This tells the reader what the data *means* for the strategy.

**Ask yourself**: "Am I adding insight or just restating numbers?"

---

## Charter Sections

### 1. Market Thesis (300-500 words)

**Purpose**: Why NOW is the right time for this strategy.

Structure:
- **The Setup**: What's the current regime? (2-3 sentences, synthesized)
- **The Insight**: What specific dynamic are we exploiting? (2-3 sentences)
- **The Connection**: Why does this favor our strategy? (2-3 sentences)

Don't write a comprehensive market overview. Write the specific insight that makes this strategy compelling right now.

### 2. Strategy Selection (400-600 words)

**Purpose**: Why THIS strategy vs the 4 alternatives.

Structure:
- **The Edge**: What's the core thesis? What inefficiency are we exploiting?
- **Why This One**: What made it stand out? (reference Edge Scorecard dimensions, but explain *why* they scored high)
- **Why Not The Others**: 1 sentence per rejected alternative - the key weakness
- **Accepted Tradeoffs**: What are we sacrificing? Be honest.

Focus on conviction and reasoning, not score breakdowns.

### 3. Expected Behavior (300-500 words)

**Purpose**: What should we see if our thesis is right (or wrong)?

Structure:
- **If We're Right**: What confirms our thesis? What does success look like?
- **If We're Partially Right**: What does muddy-but-okay look like?
- **If We're Wrong**: What specific dynamic would prove our reasoning was flawed? (Not just "market goes down")

Focus on thesis validation signals, not performance predictions.

### 4. Failure Modes (3-7 items)

**Purpose**: What would invalidate our thesis?

Each failure mode should answer: "If [condition], then our thesis about [X] was wrong because [reason]."

Types:
- **Thesis failures**: The core insight was wrong
- **Regime failures**: The market shifted unexpectedly
- **Execution failures**: The strategy mechanics didn't work as expected

Be specific and falsifiable. Not "market crashes" but "value underperforms growth by 5%+ despite declining rates, which would invalidate our thesis that rate easing favors value."

### 5. 90-Day Outlook (200-400 words)

**Purpose**: What are we watching over the evaluation period?

Structure:
- **Key Catalysts**: Events that could accelerate or derail the thesis
- **Thesis Checkpoints**: What should we see at Day 30, 60, 90 if it's working?
- **What Would Change Our Mind**: What evidence would cause adaptation?

Remember: This charter guides but doesn't lock in the strategy. The AI can adapt during execution.

---

## Tone & Style

Write like a hedge fund pitch memo, not a compliance document.

<wrong label="Compliance document">
"The strategy will be monitored daily for VIX levels. If VIX exceeds threshold, rebalancing protocols will be initiated per the risk framework..."
</wrong>

<right label="Pitch memo">
"The main risk is a volatility spike that breaks momentum. If VIX sustains above 30, our thesis is likely wrong - but we don't expect this given the macro setup."
</right>

Write with conviction. You're making a pitch, not hedging every statement.

---

## Common Mistakes

1. **Data dumping**: Reciting all context pack numbers instead of synthesizing
2. **Excessive hedging**: "typically", "historically tends to", "may potentially"
3. **Fabricated statistics**: "65% historical win rate" - don't invent numbers
4. **Generic failure modes**: "market crashes", "black swan event"
5. **Compliance tone**: Reading like an operations manual instead of a thesis

---

## Integrity Checks

Before finalizing, complete these three:

1. **The bet**: Complete both sentences:
   - "This wins if ___"
   - "This loses if ___"

2. **Evidence or assumption**: Any claim about market state (oversold, rate-sensitive, behavioral edge, underweight) needs data. No data? Write "we assume X" explicitly.

3. **Internal contradiction**: Name the biggest tension in this charter and address it.

---

## Quality Check

Before returning the charter, verify:

- [ ] Core thesis clear in 30 seconds?
- [ ] Synthesized data into insight?
- [ ] Clear why THIS vs alternatives?
- [ ] Failure modes about thesis invalidation?
- [ ] Reads like a pitch memo?
- [ ] Completed 3 integrity checks?

---

## Output

Return a Charter object with all 5 sections. Total ~1400-2000 words.

A concise, compelling pitch beats an exhaustive report.
