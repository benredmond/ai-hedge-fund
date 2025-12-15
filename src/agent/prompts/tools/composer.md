# Composer MCP Tools

Create, backtest, and deploy automated trading strategies (symphonies).

## Available Tools

**Strategy Creation:**
- `composer_create_symphony(symphony_score)` - Validate symphony structure
- `composer_search_symphonies(query)` - Search 1000+ existing strategies
- `composer_save_symphony(symphony_score, color, hashtag)` - Save strategy (returns symphony_id)

**Backtesting:**
- `composer_backtest_symphony(symphony_config)` - Test strategy with risk metrics
- Returns: Sharpe, max drawdown, total return, volatility

**Portfolio Monitoring:**
- `composer_list_accounts()` - Get available accounts
- `composer_get_account_holdings(account_id)` - Current positions
- `composer_get_symphony_daily_performance(symphony_id)` - Performance tracking

## symphony_score Structure (CRITICAL)

Symphonies use a hierarchical tree structure. **Every node MUST have `weight: null`**.

```json
{
  "step": "root",
  "name": "Strategy Name",
  "description": "Strategy description",
  "rebalance": "monthly",
  "rebalance-corridor-width": null,
  "weight": null,
  "children": [
    {
      "step": "wt-cash-equal",
      "weight": null,
      "children": [
        {
          "ticker": "SPY",
          "exchange": "XNYS",
          "name": "SPDR S&P 500 ETF Trust",
          "step": "asset",
          "weight": null
        }
      ]
    }
  ]
}
```

**Node types:**
- `root` - Top level (required)
- `wt-cash-equal` - Equal weight children
- `wt-cash-specified` - Custom weights (add `allocation` to children)
- `asset` - Individual security

**Exchange codes:** XNYS (NYSE), XNGS (NASDAQ), ARCX (ARCA)

## Usage Patterns

**Search for inspiration:**
```python
composer_search_symphonies("momentum tech")
composer_search_symphonies("defensive rotation")
```

**Save a symphony:**
```python
composer_save_symphony(
    symphony_score={...},  # Hierarchical structure above
    color="#AEC3C6",
    hashtag="#MOMENTUM"
)
```

## Composer Constraints

- ❌ Cannot hold 100% cash (use BIL for cash proxy)
- ❌ No direct shorts (use inverse ETFs like SH, PSQ)
- ❌ No direct leverage (use leveraged ETFs like UPRO, TQQQ)
- ⚠️ Trades execute near market close (~3:50 PM ET)
- ⚠️ Daily price data only (no intraday)
