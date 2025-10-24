# Charter Creation Workflow

Create a comprehensive charter document for a trading strategy.

## Purpose

The charter articulates:
- **Why now**: Market conditions that make this strategy appropriate
- **Strategic thesis**: The edge this strategy exploits
- **Expected outcomes**: Performance across different scenarios
- **Risk awareness**: Specific failure modes to monitor
- **Forward outlook**: 90-day expectations and key milestones

## Input Context

You will receive:
- A Strategy object (name, assets, weights, rebalancing logic)
- Market context data (regime, economic indicators, recent events)
- Optional: Backtest results and performance metrics

## Charter Components

### 1. Market Thesis (500-1000 words)

Analyze the current market environment:

**Economic Regime:**
- Where are we in the business cycle? (expansion, slowdown, recession, recovery)
- Key economic drivers: interest rates, inflation, employment, GDP
- Use `fred_get_series()` to reference current data points

**Market Sentiment:**
- Trend analysis: bull/bear market positioning
- Volatility regime: VIX levels and investor fear
- Sector leadership: which sectors are outperforming and why
- Use `stock_get_historical_stock_prices()` for market data

**Key Catalysts:**
- What risks dominate current market thinking?
- What opportunities are emerging?
- Use `stock_get_yahoo_finance_news()` for recent developments

### 2. Strategy Selection (400-800 words)

Justify why this specific strategy was chosen:

**Strategic Rationale:**
- What market inefficiency or edge does this exploit?
- Why is this approach well-suited to the current regime?
- How does this compare to obvious alternatives (60/40, SPY, etc.)?

**Competitive Analysis:**
- If you evaluated multiple candidates, explain the selection criteria
- Why did this strategy win vs the alternatives?
- What trade-offs were accepted?

**Risk-Reward Profile:**
- What is the expected Sharpe ratio?
- How does volatility compare to benchmarks?
- What is the acceptable maximum drawdown?

### 3. Expected Behavior (400-600 words)

Describe performance expectations across scenarios:

**Best Case Scenario:**
- Market conditions: [specific regime characteristics]
- Expected return: [quantitative estimate]
- Mechanism: Explain WHY strategy outperforms in this scenario

**Base Case Scenario:**
- Market conditions: [most likely path forward]
- Expected return: [quantitative estimate]
- Benchmark comparison: vs SPY, 60/40, etc.

**Worst Case Scenario:**
- Market conditions: [adverse scenario]
- Expected drawdown: [quantitative estimate]
- Recovery mechanism: How does strategy recover?

**Behavior Patterns:**
- How should this strategy perform in rising markets?
- How should it perform in falling markets?
- What happens during volatility spikes?
- What happens during regime transitions?

### 4. Failure Modes (3-8 specific conditions)

List concrete scenarios where this strategy will fail:

**Format:** Each failure mode should be specific and measurable.

**Good examples:**
- "If 10-year Treasury yields rise above 5%, bond allocation will suffer losses of 10-15%"
- "If VIX exceeds 40, low-volatility factor may lag high-beta stocks by 20%+"
- "If inflation exceeds 4%, real returns will be negative despite positive nominal performance"
- "If sector rotation accelerates (>3% daily moves), monthly rebalancing will miss gains"

**Bad examples:**
- "Market goes down" (too vague)
- "Black swan event" (not specific)
- "Strategy underperforms" (circular)

### 5. 90-Day Outlook (300-500 words)

Forward-looking assessment:

**Market Path Expectations:**
- Most likely trajectory for next 90 days
- Key economic events to monitor (Fed meetings, earnings, etc.)
- Technical levels or thresholds to watch

**Strategy Positioning:**
- How is this strategy positioned for the expected path?
- What adjustments might be needed?
- What would trigger a strategy review?

**Milestones & Triggers:**
- Day 30 checkpoints: What should we see?
- Day 60 checkpoints: Expected progress?
- Day 90 target: Success criteria?

**Red Flags:**
- What early warning signs indicate the thesis is breaking?
- What metrics to monitor daily/weekly?
- When should we consider exiting?

## Output Format

Return a Charter object:
```python
Charter(
    market_thesis="[Comprehensive market analysis...]",
    strategy_selection="[Justification for this strategy...]",
    expected_behavior="[Performance across scenarios...]",
    failure_modes=[
        "Specific failure condition 1",
        "Specific failure condition 2",
        "Specific failure condition 3"
    ],
    outlook_90d="[Forward-looking assessment...]"
)
```

## Quality Standards

**Data-Driven:**
- Reference specific economic indicators (with values)
- Cite recent market moves and levels
- Use MCP tools to verify claims

**Specific and Measurable:**
- Quantify expected returns and risks
- Define concrete failure thresholds
- Avoid vague statements like "might do well"

**Strategic Depth:**
- Explain the WHY, not just the WHAT
- Connect strategy mechanics to market conditions
- Show awareness of trade-offs and limitations

**Forward-Looking:**
- Focus on next 90 days, not past performance
- Identify specific milestones and triggers
- Acknowledge uncertainty and scenarios

## Common Pitfalls to Avoid

**Don't:**
- Make predictions without supporting data
- Use generic statements that apply to any strategy
- Focus only on upside (ignoring downside risks)
- Write failure modes that are circular or vague
- Assume perfect market timing
- Ignore transaction costs and rebalancing friction

**Do:**
- Ground analysis in current market data
- Be specific about conditions and expectations
- Balance optimism with risk awareness
- Define concrete, measurable failure modes
- Acknowledge what you don't know
- Think probabilistically, not deterministically

## Charter Checklist

Before submitting, verify:
- ✓ Used MCP tools to gather current market data
- ✓ Market thesis cites specific economic indicators
- ✓ Strategy selection explains the edge being exploited
- ✓ Expected behavior covers best/base/worst cases
- ✓ Failure modes are specific and measurable (not vague)
- ✓ 90-day outlook includes concrete milestones
- ✓ All sections are substantive (not placeholder text)
- ✓ Document is 1500-3000 words total (comprehensive but focused)
