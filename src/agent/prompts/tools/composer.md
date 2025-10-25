# Composer MCP Tools

Create, backtest, and deploy automated trading strategies (symphonies).

## Available Tools

**Strategy Creation:**
- `composer_create_symphony(config)` - Define new strategy
- `composer_search_symphonies(query)` - Search 1000+ existing strategies
- `composer_save_symphony(symphony)` - Save strategy

**Backtesting:**
- `composer_backtest_symphony(symphony_config)` - Test strategy with risk metrics
- Returns: Sharpe, max drawdown, total return, volatility

**Portfolio Monitoring:**
- `composer_list_accounts()` - Get available accounts
- `composer_get_account_holdings(account_id)` - Current positions
- `composer_get_symphony_daily_performance(symphony_id)` - Performance tracking

## Symphony Structure

Symphonies are built from composable blocks:

**Assets:** `EQUITIES::AAPL//USD`, `CRYPTO::BTC//USD`
**Weighting:** Equal, specified, inverse volatility, market cap
**Conditionals:** IF-THEN-ELSE based on technical indicators
**Filters:** Dynamic selection from asset pools

## Usage Patterns

**Learn from existing strategies:**
```python
composer_search_symphonies("momentum tech")
composer_search_symphonies("defensive rotation")
```

**Backtest candidate:**
```python
symphony = {
  "name": "Tech Momentum",
  "assets": ["EQUITIES::NVDA//USD", "EQUITIES::MSFT//USD"],
  "weights": {"NVDA": 0.6, "MSFT": 0.4},
  "rebalance_frequency": "monthly"
}
composer_backtest_symphony(symphony)
```

## Composer Constraints

- ❌ Cannot hold 100% cash (use BIL for cash proxy)
- ❌ No direct shorts (use inverse ETFs like SH, PSQ)
- ❌ No direct leverage (use leveraged ETFs like UPRO, TQQQ)
- ⚠️ Trades execute near market close (~3:50 PM ET)
- ⚠️ Daily price data only (no intraday)
