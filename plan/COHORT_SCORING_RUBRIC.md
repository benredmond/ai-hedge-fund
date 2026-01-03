# Cohort 0 Scoring Rubric

Manual scoring guide for evaluating AI-generated trading strategies after 90-day live period.

**Scoring Philosophy:** Good reasoning with bad outcomes > Bad reasoning with good outcomes. We're evaluating strategic thinking capability, not prediction accuracy.

---

## Scoring Summary

| Component | Weight | Points | Method |
|-----------|--------|--------|--------|
| Charter Quality | 40% | 0-40 | Manual |
| Quantitative Performance | 30% | 0-30 | Automated |
| Charter-Reality Alignment | 30% | 0-30 | Manual |
| **Total** | 100% | 0-100 | |

---

## 1. Charter Quality (40 points)

Evaluate the quality of reasoning in the original charter, independent of outcomes.

### 1.1 Edge Articulation (10 points)

*Does the strategy exploit a specific, structural market inefficiency?*

| Score | Criteria |
|-------|----------|
| 9-10 | Specific structural inefficiency with causal mechanism. Explains WHY edge exists (behavioral/structural/informational/risk premium) and why it persists. |
| 7-8 | Clear edge with reasonable justification. May lack full causal chain but demonstrates understanding of market mechanics. |
| 5-6 | Edge claimed but generic ("momentum works", "diversification"). Some justification but could apply to many strategies. |
| 3-4 | Vague edge or circular reasoning ("buy winners because they win"). Description of what, not why. |
| 1-2 | No discernible edge. Pure beta exposure dressed up as alpha. |
| 0 | No edge articulation attempted. |

**Score: ___ / 10**

**Notes:**
```
[Your reasoning here - important for LLM training]
```

---

### 1.2 Falsifiability (10 points)

*Are predictions specific enough to be proven wrong?*

| Score | Criteria |
|-------|----------|
| 9-10 | Quantitative thresholds + early warning signals + time bounds. Example: "VIXY triggers >3 times in 30 days with no SPY drawdown >2%" |
| 7-8 | Specific failure conditions with some quantitative thresholds. May lack early warnings or time bounds. |
| 5-6 | Failure modes identified but not quantitatively testable. Example: "fails if volatility spikes" (how much? for how long?) |
| 3-4 | Generic failure modes. Example: "fails if market crashes" or "fails if thesis is wrong" |
| 1-2 | Unfalsifiable claims or no failure modes. Example: "works in all conditions" |
| 0 | No failure modes or expected behavior articulated. |

**Checklist for high scores:**
- [ ] Specific numerical thresholds (VIX > 25, drawdown > 15%, etc.)
- [ ] Early warning signals defined
- [ ] Time bounds specified (30 days, 60 days, etc.)
- [ ] Multiple scenarios described (thesis correct, partially right, wrong)
- [ ] Failure modes have observable triggers

**Score: ___ / 10**

**Notes:**
```
[Your reasoning here]
```

---

### 1.3 Regime Awareness (10 points)

*Does the strategy fit current market conditions? Is "why now" articulated?*

| Score | Criteria |
|-------|----------|
| 9-10 | Precise regime diagnosis with evidence. Clear "why now" tied to specific current conditions. Articulates what regime shift would invalidate thesis. |
| 7-8 | Good regime awareness. References current conditions (VIX level, trend, sector leadership) and explains fit. |
| 5-6 | Some regime awareness but generic. Mentions market conditions without specific connection to strategy logic. |
| 3-4 | Minimal regime consideration. Strategy could apply to any market. No "why now." |
| 1-2 | Regime-agnostic or misaligned. Strategy seems designed for different conditions than current market. |
| 0 | No regime analysis. |

**Score: ___ / 10**

**Notes:**
```
[Your reasoning here]
```

---

### 1.4 Internal Coherence (10 points)

*Do the pieces fit together? Does position sizing match conviction?*

| Score | Criteria |
|-------|----------|
| 9-10 | Thesis → assets → weights → rebalancing all logically connected. Concentration justified. Conditional logic matches edge timescale. |
| 7-8 | Mostly coherent with minor gaps. May have one element that doesn't quite fit. |
| 5-6 | Some internal consistency but notable gaps. Example: defensive thesis but aggressive concentration. |
| 3-4 | Multiple contradictions. Example: momentum strategy with quarterly rebalancing, or "defensive" with 80% equity. |
| 1-2 | Fundamental incoherence. Thesis and implementation don't match. |
| 0 | No logical structure. |

**Coherence checklist:**
- [ ] Asset selection matches thesis
- [ ] Weights reflect stated conviction levels
- [ ] Rebalancing frequency matches edge timescale
- [ ] Conditional logic triggers make sense for thesis
- [ ] Risk management aligns with stated risk tolerance

**Score: ___ / 10**

**Notes:**
```
[Your reasoning here]
```

---

### Charter Quality Total: ___ / 40

---

## 2. Quantitative Performance (30 points)

Automated scoring based on 90-day performance vs benchmarks.

### 2.1 Sharpe Ratio Percentile (15 points)

Compare strategy Sharpe ratio to 5 benchmarks: SPY, QQQ, AGG, 60/40, Risk Parity.

| Benchmarks Beaten | Points |
|-------------------|--------|
| 5/5 | 15 |
| 4/5 | 12 |
| 3/5 | 9 |
| 2/5 | 6 |
| 1/5 | 3 |
| 0/5 | 0 |

**Strategy Sharpe:** ___
**Benchmark Sharpes:** SPY ___ | QQQ ___ | AGG ___ | 60/40 ___ | Risk Parity ___

**Benchmarks beaten:** ___ / 5

**Score: ___ / 15**

---

### 2.2 Drawdown Management (10 points)

| Criteria | Points |
|----------|--------|
| Max DD better than all benchmarks | 10 |
| Max DD better than 4/5 benchmarks | 8 |
| Max DD better than 3/5 benchmarks | 6 |
| Max DD better than 2/5 benchmarks | 4 |
| Max DD better than 1/5 benchmarks | 2 |
| Max DD worse than all benchmarks | 0 |

**Penalty:** If max DD > 50%, automatic 0 points (catastrophic failure).

**Strategy Max DD:** ___%
**Benchmark Max DDs:** SPY ___% | QQQ ___% | AGG ___% | 60/40 ___% | Risk Parity ___%

**Score: ___ / 10**

---

### 2.3 Return Comparison (5 points)

| Benchmarks Beaten (Total Return) | Points |
|----------------------------------|--------|
| 5/5 | 5 |
| 4/5 | 4 |
| 3/5 | 3 |
| 2/5 | 2 |
| 1/5 | 1 |
| 0/5 | 0 |

**Strategy Return:** ___%
**Benchmark Returns:** SPY ___% | QQQ ___% | AGG ___% | 60/40 ___% | Risk Parity ___%

**Score: ___ / 5**

---

### Quantitative Performance Total: ___ / 30

---

## 3. Charter-Reality Alignment (30 points)

*Did the strategy behave as the charter predicted?*

### 3.1 Scenario Identification (5 points)

First, determine which scenario from the charter actually occurred.

**What the charter predicted for each scenario:**

Thesis Correct:
```
[Copy from charter - expected behavior if thesis correct]
```

Partially Right:
```
[Copy from charter - expected behavior if partially right]
```

Thesis Wrong:
```
[Copy from charter - expected behavior if thesis wrong]
```

**What actually happened (market conditions):**
```
[Describe actual market: trend, volatility, sector leadership, notable events]
```

**Which scenario occurred?** [ ] Thesis Correct  [ ] Partially Right  [ ] Thesis Wrong  [ ] None of the above

**Score: ___ / 5** (5 = clearly matches one scenario, 3 = roughly matches, 0 = market did something not described)

---

### 3.2 Behavior Match (15 points)

*Given the scenario that occurred, did the strategy behave as predicted?*

| Score | Criteria |
|-------|----------|
| 13-15 | Strategy behaved exactly as charter predicted for the actual scenario. Triggers fired when expected, allocations matched, performance aligned with stated expectations. |
| 10-12 | Strategy behaved mostly as predicted. Minor divergences explainable by market microstructure or timing. |
| 7-9 | Strategy partially matched predictions. Some elements worked as described, others didn't. |
| 4-6 | Strategy behavior diverged significantly from predictions, but failure mode was pre-identified in charter. |
| 1-3 | Strategy behavior diverged in ways not anticipated. Charter predictions were wrong. |
| 0 | Complete disconnect between charter predictions and actual behavior. |

**Evidence:**
```
Charter said: [specific prediction]
Actually happened: [what occurred]
Match? [yes/no/partial]

Charter said: [specific prediction]
Actually happened: [what occurred]
Match? [yes/no/partial]

[Add more as needed]
```

**Score: ___ / 15**

**Notes:**
```
[Your reasoning here]
```

---

### 3.3 Failure Mode Validation (10 points)

*If the strategy underperformed or failed, was this failure mode pre-identified?*

| Score | Criteria |
|-------|----------|
| 9-10 | Strategy performed well OR failure matched a pre-identified failure mode with the stated early warning signals. |
| 7-8 | Failure partially matched a pre-identified mode. Early warnings may not have triggered as described. |
| 5-6 | Failure was in the general category of a pre-identified mode but specifics didn't match. |
| 3-4 | Failure occurred that was tangentially related to identified modes. |
| 1-2 | Failure occurred that was not anticipated in any failure mode. |
| 0 | Catastrophic failure not anticipated; charter claimed robustness. |

**If strategy failed, which failure mode (if any) matched?**
```
Identified failure mode: [from charter]
Actual failure: [what happened]
Early warning triggered? [yes/no]
Match quality: [exact/partial/tangential/none]
```

**Score: ___ / 10**

**Notes:**
```
[Your reasoning here]
```

---

### Charter-Reality Alignment Total: ___ / 30

---

## Final Score

| Component | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Charter Quality | /40 | 40% | |
| Quantitative Performance | /30 | 30% | |
| Charter-Reality Alignment | /30 | 30% | |
| **Total** | | | **/100** |

---

## Scoring Notes

**Key observations:**
```
[What stood out about this strategy? What did the AI do well/poorly?]
```

**Edge cases encountered:**
```
[Any judgment calls you made that future scoring should be consistent with]
```

**Questions for future rubric refinement:**
```
[Anything unclear or that needs better criteria]
```

---

## Appendix: Quick Reference

### Red Flags (automatic penalties or close scrutiny)
- Max drawdown > 50%
- Sharpe ratio > 5 in backtest (overfit)
- No failure modes articulated
- Strategy behaved opposite to predictions
- "Works in all conditions" claims

### Green Flags (indicators of quality)
- Specific quantitative thresholds in failure modes
- Early warning signals defined
- Clear "why now" tied to current regime
- Thesis → assets → weights logical chain
- Honest acknowledgment of tradeoffs

### Context-Dependent Judgments
Document these carefully for LLM training:
- Threshold tolerance (e.g., "capture 70-80%" vs actual 65%)
- Market conditions that weren't clearly in any scenario
- Strategies that adapted mid-period (no board meetings in Cohort 0)
- Technical issues (Composer bugs, data gaps, etc.)
