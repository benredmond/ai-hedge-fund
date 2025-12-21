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

**Option A (Recommended):** Call `composer_create_symphony` with a natural language description, then `composer_save_symphony` with the returned structure.

**Option B:** Flatten to static weights using the `if_false` branch (normal market conditions).

**Option C:** Build if-block manually (only if you understand the complete syntax with predicate fields).

If no logic_tree, proceed directly to Step 3.

## Step 3: Build symphony_score

Create hierarchical structure: root → weighting node → asset nodes.

Refer to the Composer tools documentation for:
- Schema rules (weight=null, no id, no children on assets)
- Node types and examples
- Asset node field requirements

## Step 4: Pre-Flight Check

Before calling `composer_save_symphony`:

1. ☐ NO `id` field on ANY node
2. ☐ NO `children` field on asset nodes
3. ☐ `weight: null` on EVERY node
4. ☐ Each asset has: ticker, exchange, name, step, weight

## Step 5: Save and Report

Call `composer_save_symphony` with:
- `symphony_score` - The hierarchical structure
- `color` - Hex color (e.g., "#AEC3C6")
- `hashtag` - Strategy tag (e.g., "#MOMENTUM")

Report the `symphony_id` on success, or the full error message on failure.
