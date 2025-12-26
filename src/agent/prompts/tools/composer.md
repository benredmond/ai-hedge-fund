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

**2. `id` field REQUIRED on EVERY node (UUID format)**
- Each node must have a unique UUID: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- ✅ CORRECT: `"id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"`
- ❌ WRONG: `"id": "abc-123"` (not UUID format)
- ❌ WRONG: `"id": "spy-asset-id"` (not UUID format)
- ❌ WRONG: omitting id entirely

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
  "id": "11111111-1111-1111-1111-111111111111",
  "name": "Strategy Name",
  "description": "Strategy description",
  "rebalance": "monthly",
  "rebalance-corridor-width": null,
  "weight": null,
  "children": [
    {
      "step": "wt-cash-equal",
      "id": "22222222-2222-2222-2222-222222222222",
      "weight": null,
      "children": [
        {
          "step": "asset",
          "id": "33333333-3333-3333-3333-333333333333",
          "ticker": "SPY",
          "exchange": "XNYS",
          "name": "SPDR S&P 500 ETF Trust",
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

Asset nodes must have EXACTLY these 6 fields (or 7 if child of `wt-cash-specified` - add `allocation`):
- `step` - Must be "asset"
- `id` - UUID format (e.g., "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
- `ticker` - Raw symbol (e.g., "SPY", "XLE")
- `exchange` - XNYS (NYSE), XNGS (NASDAQ), or ARCX (ARCA)
- `name` - Full asset name
- `weight` - Must be null

**CORRECT asset node:**
```json
{"step": "asset", "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "ticker": "XLE", "exchange": "ARCX", "name": "Energy Select Sector SPDR Fund", "weight": null}
```

**WRONG asset node (invalid id format, has forbidden children):**
```json
{"step": "asset", "id": "xle-node-123", "name": "Energy ETF", "weight": null, "children": []}
```

### Specified Weights Example

```json
{
  "step": "wt-cash-specified",
  "id": "44444444-4444-4444-4444-444444444444",
  "weight": null,
  "children": [
    {"step": "asset", "id": "55555555-5555-5555-5555-555555555555", "ticker": "SPY", "exchange": "XNYS", "name": "SPDR S&P 500 ETF Trust", "weight": null, "allocation": 0.6},
    {"step": "asset", "id": "66666666-6666-6666-6666-666666666666", "ticker": "QQQ", "exchange": "XNGS", "name": "Invesco QQQ Trust", "weight": null, "allocation": 0.4}
  ]
}
```

### Complete Symphony Example (3 assets with specified weights)

Use this as your template for multi-asset portfolios:

```json
{
  "step": "root",
  "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  "name": "Defensive Sectors Strategy",
  "description": "Holds SPY core with defensive sector tilts (utilities, staples)",
  "rebalance": "monthly",
  "rebalance-corridor-width": null,
  "weight": null,
  "children": [
    {
      "step": "wt-cash-specified",
      "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
      "weight": null,
      "children": [
        {"step": "asset", "id": "cccccccc-cccc-cccc-cccc-cccccccccccc", "ticker": "SPY", "exchange": "XNYS", "name": "SPDR S&P 500 ETF Trust", "weight": null, "allocation": 0.5},
        {"step": "asset", "id": "dddddddd-dddd-dddd-dddd-dddddddddddd", "ticker": "XLU", "exchange": "ARCX", "name": "Utilities Select Sector SPDR Fund", "weight": null, "allocation": 0.25},
        {"step": "asset", "id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee", "ticker": "XLP", "exchange": "ARCX", "name": "Consumer Staples Select Sector SPDR Fund", "weight": null, "allocation": 0.25}
      ]
    }
  ]
}
```

**Key points in this example:**
- `id` field on EVERY node (UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
- `weight: null` on EVERY node (root, wt-cash-specified, all assets)
- `allocation` on EACH asset (0.5 + 0.25 + 0.25 = 1.0)
- Each asset has exactly: step, id, ticker, exchange, name, weight, allocation

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
  "id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
  "weight": null,
  "children": [
    {
      "step": "if-child",
      "id": "11111111-2222-3333-4444-555555555555",
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
        {"step": "asset", "id": "66666666-7777-8888-9999-aaaaaaaaaaaa", "ticker": "SPY", "exchange": "XNYS", "name": "SPDR S&P 500 ETF Trust", "weight": null}
      ]
    },
    {
      "step": "if-child",
      "id": "bbbbbbbb-cccc-dddd-eeee-ffffffffffff",
      "is-else-condition?": true,
      "weight": null,
      "children": [
        {"step": "asset", "id": "00000000-1111-2222-3333-444444444444", "ticker": "BIL", "exchange": "ARCX", "name": "SPDR Bloomberg 1-3 Month T-Bill ETF", "weight": null}
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
  "id": "12345678-1234-1234-1234-123456789012",
  "weight": null,
  "sort-by-fn": "cumulative-return",
  "sort-by-fn-params": {"window": 30},
  "select-fn": "top",
  "select-n": 3,
  "children": [
    {"step": "asset", "id": "11111111-aaaa-bbbb-cccc-111111111111", "ticker": "XLK", "exchange": "ARCX", "name": "Technology Select Sector SPDR Fund", "weight": null},
    {"step": "asset", "id": "22222222-aaaa-bbbb-cccc-222222222222", "ticker": "XLV", "exchange": "ARCX", "name": "Health Care Select Sector SPDR Fund", "weight": null},
    {"step": "asset", "id": "33333333-aaaa-bbbb-cccc-333333333333", "ticker": "XLF", "exchange": "ARCX", "name": "Financial Select Sector SPDR Fund", "weight": null},
    {"step": "asset", "id": "44444444-aaaa-bbbb-cccc-444444444444", "ticker": "XLE", "exchange": "ARCX", "name": "Energy Select Sector SPDR Fund", "weight": null},
    {"step": "asset", "id": "55555555-aaaa-bbbb-cccc-555555555555", "ticker": "XLI", "exchange": "ARCX", "name": "Industrial Select Sector SPDR Fund", "weight": null}
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
  "id": "gggggggg-gggg-gggg-gggg-gggggggggggg",
  "name": "Equity Sleeve",
  "weight": null,
  "children": [
    {
      "step": "wt-cash-equal",
      "id": "hhhhhhhh-hhhh-hhhh-hhhh-hhhhhhhhhhhh",
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

Before calling `composer_create_symphony`, verify:

1. ☐ `id` field on EVERY node (UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
2. ☐ NO `children` field on asset nodes (assets are LEAF nodes)
3. ☐ `weight: null` on EVERY node (literal null, not a number)
4. ☐ Each asset has EXACTLY: step, id, ticker, exchange, name, weight
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
