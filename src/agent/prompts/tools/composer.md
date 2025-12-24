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

---

## symphony_score Schema

Symphonies use a hierarchical tree structure. The schema is strict - violations cause validation failure.

### Critical Rules

**1. `weight: null` on EVERY node**
- ✅ CORRECT: `"weight": null`
- ❌ WRONG: `"weight": {"num": 40, "den": 100}` (fraction format)
- ❌ WRONG: `"weight": 0.4` (decimal)
- ❌ WRONG: omitting weight entirely

**2. NO `id` field on ANY node**
- Composer assigns IDs internally - never provide them
- ❌ WRONG: `"id": "abc-123"`
- ❌ WRONG: `"id": "e1ac253e-52b5-402c-a2a8-a4d34e323a16"`
- ❌ WRONG: `"id": "spy-asset-id"`

**3. NO `children` on asset nodes**
- Asset nodes are LEAF nodes
- ❌ WRONG: `"children": []` on asset (even empty array is forbidden)

**4. `wt-cash-specified` children MUST have `allocation` field**
- Each child asset needs `"allocation": 0.X` (decimal weight, must sum to 1.0)
- ✅ CORRECT: `{"ticker": "SPY", "exchange": "XNYS", "name": "...", "step": "asset", "weight": null, "allocation": 0.6}`
- ❌ WRONG: `{"ticker": "SPY", "exchange": "XNYS", "name": "...", "step": "asset", "weight": null}` (missing allocation)
- Note: `wt-cash-equal` does NOT use allocation (weights are equal automatically)

**5. Conditional `if` blocks require COMPLETE structure**
- Must include predicate fields (comparison-operator, lhs, rhs)
- ❌ WRONG: `if` block with only children and no predicate

### Basic Structure

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

### Node Types

| Step | Purpose | Notes |
|------|---------|-------|
| `root` | Top level container | Required, includes name/description/rebalance |
| `wt-cash-equal` | Equal weight children | No allocation field needed |
| `wt-cash-specified` | Custom weights | Add `"allocation": 0.6` to each child |
| `wt-inverse-vol` | Inverse vol weighting | Optional: `window-days` parameter |
| `asset` | Individual security | LEAF node - no children |
| `if` | Conditional logic | Contains `if-child` nodes for branches |
| `if-child` | Branch of conditional | `is-else-condition?`: false (true branch) or true (else branch) |
| `filter` | Ranking/selection | `sort-by-fn`, `select-fn`, `select-n` |
| `group` | Nested grouping | Contains weighting nodes only |

### Asset Node Requirements

Asset nodes must have EXACTLY these 5 fields (or 6 if child of `wt-cash-specified` - add `allocation`):
- `ticker` - Raw symbol (e.g., "SPY", "XLE")
- `exchange` - XNYS (NYSE), XNGS (NASDAQ), or ARCX (ARCA)
- `name` - Full asset name
- `step` - Must be "asset"
- `weight` - Must be null

**CORRECT asset node:**
```json
{"ticker": "XLE", "exchange": "ARCX", "name": "Energy Select Sector SPDR Fund", "step": "asset", "weight": null}
```

**WRONG asset node (has forbidden fields):**
```json
{"name": "Energy ETF", "step": "asset", "weight": null, "children": [], "id": "xle-node-123"}
```

### Specified Weights Example

```json
{
  "step": "wt-cash-specified",
  "weight": null,
  "children": [
    {"ticker": "SPY", "exchange": "XNYS", "name": "SPDR S&P 500 ETF Trust", "step": "asset", "weight": null, "allocation": 0.6},
    {"ticker": "QQQ", "exchange": "XNGS", "name": "Invesco QQQ Trust", "step": "asset", "weight": null, "allocation": 0.4}
  ]
}
```

### Complete Symphony Example (3 assets with specified weights)

Use this as your template for multi-asset portfolios:

```json
{
  "step": "root",
  "name": "Defensive Sectors Strategy",
  "description": "Holds SPY core with defensive sector tilts (utilities, staples)",
  "rebalance": "monthly",
  "rebalance-corridor-width": null,
  "weight": null,
  "children": [
    {
      "step": "wt-cash-specified",
      "weight": null,
      "children": [
        {"ticker": "SPY", "exchange": "XNYS", "name": "SPDR S&P 500 ETF Trust", "step": "asset", "weight": null, "allocation": 0.5},
        {"ticker": "XLU", "exchange": "ARCX", "name": "Utilities Select Sector SPDR Fund", "step": "asset", "weight": null, "allocation": 0.25},
        {"ticker": "XLP", "exchange": "ARCX", "name": "Consumer Staples Select Sector SPDR Fund", "step": "asset", "weight": null, "allocation": 0.25}
      ]
    }
  ]
}
```

**Key points in this example:**
- NO `id` fields anywhere
- `weight: null` on EVERY node (root, wt-cash-specified, all assets)
- `allocation` on EACH asset (0.5 + 0.25 + 0.25 = 1.0)
- Each asset has exactly: ticker, exchange, name, step, weight, allocation

### Conditional Logic (if blocks)

**⚠️ CRITICAL: Composer only supports PRICE-BASED conditions on TRADEABLE assets.**

**✅ VALID conditions:**
- Asset price vs moving average: `SPY_price > SPY_200d_MA`
- Cumulative returns: `SPY_cumulative_return_30d > 0.05`
- RSI: `SPY_RSI_14d > 70`
- Volatility via ETF proxy: `VIXY_price > 22` (NOT `VIX > 22`)

**❌ INVALID conditions (will cause deployment failure):**
- Macro indicators: `fed_funds_rate`, `inflation`, `GDP`, `unemployment`
- VIX index directly: `VIX > 25` (use `VIXY_price > 22` instead)
- Conceptual conditions: `fed_pivot_dovish`, `recession_risk_high`

#### If Node Structure

```json
{
  "step": "if",
  "weight": null,
  "children": [
    {
      "step": "if-child",
      "is-else-condition?": false,
      "comparator": "gt",
      "lhs-val": "SPY",
      "lhs-fn": "cumulative-return",
      "lhs-fn-params": {"window": 200},
      "rhs-val": 0,
      "rhs-fixed-value?": true,
      "rhs-fn": null,
      "rhs-fn-params": {},
      "weight": null,
      "children": [
        {"ticker": "SPY", "exchange": "XNYS", "name": "SPDR S&P 500 ETF Trust", "step": "asset", "weight": null}
      ]
    },
    {
      "step": "if-child",
      "is-else-condition?": true,
      "weight": null,
      "children": [
        {"ticker": "BIL", "exchange": "ARCX", "name": "SPDR Bloomberg 1-3 Month T-Bill ETF", "step": "asset", "weight": null}
      ]
    }
  ]
}
```

**Comparators:** `"gt"`, `"gte"`, `"eq"`, `"lt"`, `"lte"`

**If-Child Fields:**
- `is-else-condition?`: `false` for TRUE branch, `true` for ELSE branch
- `lhs-val`: Left-hand ticker (e.g., `"SPY"`)
- `lhs-fn`: Function to apply (see Available Functions below)
- `lhs-fn-params`: `{"window": int}` - lookback window in days
- `rhs-val`: Right-hand value (number or ticker)
- `rhs-fixed-value?`: `true` if rhs-val is a number, `false` if ticker
- `rhs-fn` / `rhs-fn-params`: Function for right side (or null)

### Filter Node (Ranking/Selection)

Select top/bottom N assets from a pool based on a ranking function:

```json
{
  "step": "filter",
  "weight": null,
  "sort-by-fn": "cumulative-return",
  "sort-by-fn-params": {"window": 30},
  "select-fn": "top",
  "select-n": 3,
  "children": [
    {"ticker": "XLK", "exchange": "ARCX", "name": "Technology Select Sector SPDR Fund", "step": "asset", "weight": null},
    {"ticker": "XLV", "exchange": "ARCX", "name": "Health Care Select Sector SPDR Fund", "step": "asset", "weight": null},
    {"ticker": "XLF", "exchange": "ARCX", "name": "Financial Select Sector SPDR Fund", "step": "asset", "weight": null},
    {"ticker": "XLE", "exchange": "ARCX", "name": "Energy Select Sector SPDR Fund", "step": "asset", "weight": null},
    {"ticker": "XLI", "exchange": "ARCX", "name": "Industrial Select Sector SPDR Fund", "step": "asset", "weight": null}
  ]
}
```

**Filter Fields:**
- `sort-by-fn`: Ranking function (see Available Functions)
- `sort-by-fn-params`: `{"window": int}` - lookback window
- `select-fn`: `"top"` or `"bottom"`
- `select-n`: How many to select

### Group Node

Group assets with nested weighting:

```json
{
  "step": "group",
  "name": "Equity Sleeve",
  "weight": null,
  "children": [
    {
      "step": "wt-cash-equal",
      "weight": null,
      "children": [...]
    }
  ]
}
```

### Available Functions

Use these in `lhs-fn`, `rhs-fn`, or `sort-by-fn`:

| Function | Description |
|----------|-------------|
| `cumulative-return` | Total return over window |
| `current-price` | Current price |
| `exponential-moving-average-price` | EMA of price |
| `max-drawdown` | Maximum drawdown over window |
| `moving-average-price` | Simple moving average of price |
| `moving-average-return` | SMA of returns |
| `relative-strength-index` | RSI indicator |
| `standard-deviation-price` | Price volatility |
| `standard-deviation-return` | Return volatility |

### WeightMap Format

When using fraction-based weights (not for assets - use `allocation` instead):

```json
{"num": 60, "den": 100}
```

This represents 60%.

### Key Constraints

1. Root `children` must be weighting nodes (`wt-cash-equal`, `wt-cash-specified`, `wt-inverse-vol`)
2. `wt-cash-specified` children weights must sum to 100% (allocation values sum to 1.0)
3. Use `BIL` for cash allocation (no empty blocks)
4. Indexes like `^VIX` and `^TNX` are **not supported** (use ETF proxies)

---

For strategies with conditional logic, choose one approach:

**Option A (Recommended):** Build if-block with full structure (see If Node Structure above).

**Option B:** Flatten to static weights using the default branch for simpler strategies.

---

## Pre-Flight Checklist

Before calling `composer_save_symphony`, verify:

1. ☐ NO `id` field on ANY node
2. ☐ NO `children` field on asset nodes
3. ☐ `weight: null` on EVERY node (literal null, not a number)
4. ☐ Each asset has EXACTLY: ticker, exchange, name, step, weight
5. ☐ If parent is `wt-cash-specified`: each child has `allocation` field? (must sum to 1.0)
6. ☐ If using `if` blocks: all predicate fields present? (comparator, lhs-val, lhs-fn, rhs-val, etc.)

---

## save_symphony Arguments

```python
composer_save_symphony(
    symphony_score={...},  # Hierarchical structure
    color="#AEC3C6",       # Hex color code
    hashtag="#MOMENTUM"    # Strategy tag
)
```

---

## Platform Constraints

- ❌ Cannot hold 100% cash (use BIL for cash proxy)
- ❌ No direct shorts (use inverse ETFs: SH, PSQ, SQQQ)
- ❌ No direct leverage (use leveraged ETFs: UPRO, TQQQ, SSO)
- ⚠️ Trades execute near market close (~3:50 PM ET)
- ⚠️ Daily price data only (no intraday)
