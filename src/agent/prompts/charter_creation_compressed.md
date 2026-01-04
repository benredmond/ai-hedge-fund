# Charter Creation Recipe (Compressed v2.0)

## Your Task

Synthesize the selection reasoning into an **investment thesis pitch memo**.

You've received:
- 5 candidate strategies + Edge Scorecards
- Selection reasoning (why winner was chosen)
- Market context pack

**This is a synthesis stage.** If your reasoning supports refining the strategy (weights, rebalancing, etc.), you can make changes. The charter captures your best thinking.

---

## The #1 Rule

**Synthesize, don't recite.**

<wrong>
"The Federal Reserve's policy rate sits at 3.88% (November 2025), having declined from prior cycle peaks, while the 10-year Treasury yield at 4.17% reflects market confidence in sustained growth..."
</wrong>

<right>
"We're in a disinflationary growth regime - rates easing (3.88%), inflation converging to target (2.71%), healthy curve (+70bps). This is the sweet spot for value."
</right>

**Ask**: "Am I adding insight or restating the context pack?"

---

## Charter Sections

### 1. Market Thesis (300-500 words)

**Purpose**: Why NOW is the right time.

- **The Setup**: Current regime (2-3 sentences, synthesized)
- **The Insight**: What dynamic are we exploiting? (2-3 sentences)
- **The Connection**: Why does this favor our strategy? (2-3 sentences)

Not a market overview. The specific insight that makes this compelling.

### 2. Strategy Selection (400-600 words)

**Purpose**: Why THIS strategy vs alternatives.

- **The Edge**: Core thesis, inefficiency we're exploiting
- **Why This One**: What made it stand out (reference Edge Scorecard, explain *why*)
- **Why Not Others**: 1 sentence per rejected alternative
- **Tradeoffs**: What are we sacrificing? Be honest.

### 3. Expected Behavior (300-500 words)

**Purpose**: Thesis validation signals.

- **If Right**: What confirms thesis? What does success look like?
- **If Partially Right**: Muddy but okay?
- **If Wrong**: What proves our reasoning was flawed? (Not just "market down")

### 4. Failure Modes (3-7 items)

**Purpose**: What invalidates our thesis?

Each answers: "If [condition], then our thesis about [X] was wrong because [reason]."

Types:
- **Thesis failures**: Core insight was wrong
- **Regime failures**: Market shifted unexpectedly
- **Execution failures**: Mechanics didn't work

Be specific. Not "market crashes" but "value underperforms growth 5%+ despite rate easing."

### 5. 90-Day Outlook (200-400 words)

**Purpose**: What we're watching.

- **Catalysts**: Events that could accelerate or derail
- **Checkpoints**: What should we see at Day 30, 60, 90?
- **Adaptation**: What evidence would cause us to change course?

### 6. Symphony Logic Audit (Required for transparency)

**Purpose**: Document exactly how the strategy implements its claimed edge.

**If logic_tree is populated with conditional branches:**
```
Condition: [paste actual condition from logic_tree]
If True: [assets and weights OR filter/weighting leaf]
If False: [assets and weights OR filter/weighting leaf]
```

**If a branch uses a filter leaf:**
```
Filter: sort_by=[cumulative_return|moving_average_return|...], window=[N or omit for current_price], select=[top|bottom], n=[N]
Assets: [list]
```

**If a branch uses a weighting leaf:**
```
Weighting: method=[inverse_vol], window=[N]
Assets: [list]
```

**If logic_tree is filter-only (no condition):**
```
Filter: sort_by=[...], window=[N or omit for current_price], select=[top|bottom], n=[N]
Assets: [list]
```

**Edge Implementation Mapping:**
| Claimed Edge | Implementing Mechanism | Trigger/Condition |
|--------------|------------------------|-------------------|
| [from thesis] | [specific logic_tree element] | [what activates it] |

**If logic_tree is empty (static allocation):**
- Confirm: Edge is in ASSET SELECTION, not timing
- Confirm: Archetype is DIRECTIONAL or MEAN_REVERSION (not MOMENTUM or VOLATILITY)

**Red Flag Check:**
- ❌ Thesis claims "rotation" but logic_tree is empty
- ❌ Thesis claims "momentum" but no ranking/comparison logic
- ❌ Thesis claims "sector leadership" but static ETF allocation
- ❌ Thesis claims "ranking/selection" but no filter leaf

---

## Tone

Write like a pitch memo, not a compliance doc.

<wrong>
"The strategy will be monitored daily for VIX levels. If VIX exceeds 30 for 7 days, rebalancing protocols..."
</wrong>

<right>
"Main risk is a vol spike breaking momentum. VIX above 30 sustained would invalidate our thesis."
</right>

Write with conviction.

---

## Common Mistakes

1. **Data dumping** - Reciting context pack instead of synthesizing
2. **Hedging** - "typically", "historically tends to", "may potentially"
3. **Fabricated stats** - "65% win rate" without source
4. **Generic failures** - "market crashes", "black swan"
5. **Compliance tone** - Operations manual instead of thesis

---

## Integrity Checks

1. **The bet**: "This wins if ___" and "This loses if ___"
2. **Evidence or assumption**: Claims need data. No data? "We assume X"
3. **Internal contradiction**: Name the biggest tension and address it

---

## Quality Check

- [ ] Core thesis clear in 30 seconds?
- [ ] Synthesized data into insight?
- [ ] Clear why THIS vs alternatives?
- [ ] Failure modes about thesis invalidation?
- [ ] Reads like a pitch memo?
- [ ] Completed 3 integrity checks?

---

## Output

```python
Charter(
    market_thesis: str,       # 300-500 words
    strategy_selection: str,  # 400-600 words
    expected_behavior: str,   # 300-500 words
    failure_modes: List[str], # 3-7 items
    outlook_90d: str          # 200-400 words
)
```

**~1400-2000 words total. Concise pitch beats exhaustive report.**
