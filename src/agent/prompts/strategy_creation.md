# Strategy Creation Workflow

Follow this structured workflow to create a 90-day trading strategy.

## Phase 1: Market Analysis (20 minutes)

### 1.1 Economic Environment
- Use `fred_search()` to find relevant indicators
- Analyze: interest rates, inflation, employment, GDP growth
- Identify economic regime: expansion, slowdown, recession, recovery

### 1.2 Market Regime
- Use `stock_get_historical_stock_prices()` for major indices (SPY, QQQ, VIX)
- Assess: trend (bull/bear), volatility, market breadth
- Check sector performance and leadership

### 1.3 Recent Developments
- Use `stock_get_yahoo_finance_news()` for major sectors
- Identify: key risks, opportunities, sentiment shifts

## Phase 2: Strategy Generation (30 minutes)

### 2.1 Research Similar Strategies
- Use `composer_search_symphonies()` to find proven approaches
- Analyze what works in current market regime
- Learn from successful patterns

### 2.2 Generate 5 Candidate Strategies
For each candidate, define:
- **Asset allocation**: Which ETFs/stocks to hold
- **Weighting logic**: Static weights or dynamic rules
- **Rebalancing frequency**: Daily, weekly, monthly, quarterly
- **Rationale**: Why this approach fits current regime

**Example candidates:**
1. **60/40 Portfolio**: SPY 60%, AGG 40% (classic balanced)
2. **Risk Parity**: Equal risk contribution across assets
3. **Momentum**: Top 5 sectors by 3-month returns
4. **Defensive**: Low-volatility stocks + bonds
5. **Tactical**: Dynamic allocation based on VIX levels

### 2.3 Backtest Each Candidate
- Use `composer_backtest_symphony()` for each strategy
- Review: Sharpe ratio, max drawdown, volatility, consistency
- Compare against SPY, QQQ, 60/40 benchmarks

## Phase 3: Selection (15 minutes)

### 3.1 Rank Candidates
Score each on:
- **Risk-adjusted returns**: Sharpe ratio, Sortino ratio
- **Regime alignment**: Does it fit current market?
- **Robustness**: Performance across conditions
- **Implementation**: Complexity, costs, liquidity

### 3.2 Select Winner
Choose the strategy that best balances:
- Expected performance in current regime
- Acceptable downside risk
- Practical implementation

## Phase 4: Charter Creation (15 minutes)

Document your selection in a Charter:

### Market Thesis
Explain current market environment:
- Economic regime and drivers
- Market sentiment and positioning
- Key risks and opportunities

### Strategy Selection
Justify your choice:
- Why this strategy over the other 4?
- What edge does it exploit?
- How does it fit the current regime?

### Expected Behavior
Describe performance expectations:
- Best case: [conditions] → [expected return]
- Base case: [conditions] → [expected return]
- Worst case: [conditions] → [expected return]

### Failure Modes
List conditions where strategy fails:
- "If VIX > 40, expect [outcome]"
- "If bonds sell off, expect [outcome]"
- "If [scenario], this strategy will [fail condition]"

### 90-Day Outlook
Forward-looking assessment:
- Expected market path
- Strategy positioning
- Key milestones to watch

## Output Format

Return a Strategy object with:
```python
Strategy(
    name="[Strategy Name]",
    assets=["[TICKER1]", "[TICKER2]", ...],
    weights={"[TICKER1]": 0.X, "[TICKER2]": 0.Y},
    rebalance_frequency="[daily|weekly|monthly|quarterly]",
    logic_tree={}  # Can be empty for static allocation
)
```

## Quality Checklist

Before submitting, verify:
- ✓ Used MCP tools for data analysis (not guessing)
- ✓ Backtested all 5 candidates
- ✓ Selected strategy has clear rationale
- ✓ Failure modes are specific and realistic
- ✓ Weights sum to 1.0
- ✓ All assets are valid tickers
- ✓ Charter explains the "why", not just the "what"
