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
| `wt-inverse-volatility` | Inverse vol weighting | Weights calculated automatically |
| `asset` | Individual security | LEAF node - no children |

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

### Conditional Logic (if blocks)

For strategies with conditional logic:

**Option A (Recommended):** Use `composer_create_symphony` with a description:
```
"Create a strategy: when VIX < 22, hold SPY 50%, QQQ 30%, AGG 20%.
When VIX > 22, rotate to TLT 50%, GLD 30%, BIL 20%. Rebalance weekly."
```
Then call `composer_save_symphony` with the returned structure.

**Option B:** Flatten to static weights using the `if_false` branch:
```json
{
  "logic_tree": {
    "condition": "VIX > 25",
    "if_true": {"assets": ["GLD", "BIL"], "weights": {"GLD": 0.5, "BIL": 0.5}},
    "if_false": {"assets": ["SPY", "QQQ"], "weights": {"SPY": 0.6, "QQQ": 0.4}}
  }
}
```
Becomes static symphony using if_false:
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

**Option C:** Build if-block manually (advanced) - must include ALL predicate fields:
```json
{
  "step": "if",
  "weight": null,
  "comparison-operator": ">",
  "lhs": {...},
  "rhs": 22,
  "children": [
    {"step": "if-child", "is-else-condition?": false, "weight": null, "children": [...]},
    {"step": "if-child", "is-else-condition?": true, "weight": null, "children": [...]}
  ]
}
```

---

## Pre-Flight Checklist

Before calling `composer_save_symphony`, verify:

1. ☐ NO `id` field on ANY node
2. ☐ NO `children` field on asset nodes
3. ☐ `weight: null` on EVERY node (literal null, not a number)
4. ☐ Each asset has EXACTLY: ticker, exchange, name, step, weight
5. ☐ If parent is `wt-cash-specified`: each child has `allocation` field? (must sum to 1.0)
6. ☐ If using `if` blocks: predicate fields present? → If not, use Option A or B

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
