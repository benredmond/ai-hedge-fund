# Symphony Deployment Workflow

Deploy the provided strategy to Composer.trade.

## Step 1: Build symphony_score Structure

Create a hierarchical `symphony_score` object. **CRITICAL: Every node MUST have `weight: null`**.

```json
{
  "step": "root",
  "name": "Strategy Name",
  "description": "Brief strategy description",
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
        },
        {
          "ticker": "QQQ",
          "exchange": "XNGS",
          "name": "Invesco QQQ Trust",
          "step": "asset",
          "weight": null
        }
      ]
    }
  ]
}
```

**Exchange codes:** XNYS (NYSE), XNGS (NASDAQ), ARCX (ARCA for ETFs)

**Weighting options:**
- `wt-cash-equal` - Equal weight across children
- `wt-cash-specified` - Custom weights (add `"allocation": 0.6` to each child)
- `wt-inverse-volatility` - Inverse volatility weighting

## Step 2: Save Symphony

Call `composer_save_symphony` with THREE required arguments:

```json
{
  "symphony_score": { ... },
  "color": "#AEC3C6",
  "hashtag": "#STRATEGY"
}
```

## Step 3: Report Result

- **Success**: Return the `symphony_id` from the response
- **Failure**: Report the full error message for debugging
