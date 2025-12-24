# Symphony Deployment Workflow

Deploy the provided strategy to Composer.trade.

## Step 1: Analyze Strategy

Review the strategy context:
- `name` - Strategy name
- `assets` - List of tickers
- `weights` - Allocation per asset
- `rebalance_frequency` - daily/weekly/monthly
- `logic_tree` - Conditional logic (if any)

## Step 2: Handle Conditional Logic

If strategy has a `logic_tree`:

**Option A (Recommended):** Build if-block with full structured JSON schema. Use the If Node Structure from Composer tools documentation with all predicate fields (comparator, lhs-val, lhs-fn, lhs-fn-params, rhs-val, etc.).

**Option B:** Flatten to static weights using the `if_false` branch (normal market conditions) for simpler strategies.

If no logic_tree, proceed directly to Step 3.

## Step 3: Build symphony_score

Create hierarchical structure: root → weighting node → asset nodes.

Refer to the Composer tools documentation for:
- Schema rules (weight=null, no id, no children on assets)
- Node types and examples
- Asset node field requirements

## Step 4: Pre-Flight Check

Before calling `composer_save_symphony`:

1. ☐ NO `id` field on ANY node (NEVER add id fields - Composer assigns them)
2. ☐ NO `children` field on asset nodes (assets are leaf nodes)
3. ☐ `weight: null` on EVERY node (literal null, never a number)
4. ☐ Each asset has EXACTLY: ticker, exchange, name, step, weight
5. ☐ If using `wt-cash-specified`: each child has `allocation` field (decimal, must sum to 1.0)

## Step 5: Save and Report

Call `composer_save_symphony` with:
- `symphony_score` - The hierarchical structure
- `color` - Hex color (e.g., "#AEC3C6")
- `hashtag` - Strategy tag (e.g., "#MOMENTUM")

Report the `symphony_id` on success, or the full error message on failure.
