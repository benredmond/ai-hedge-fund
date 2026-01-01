# Composer Symphony Schema Debugging

**Status:** ✅ RESOLVED
**Date:** 2026-01-01
**Error:** `Input validation error: {...} is not valid under any of the given schemas`
**Resolution Date:** 2026-01-01

## Root Cause

**`current-price` function is NOT valid for IF conditionals in Composer's schema.**

Tested and confirmed:
| Test | Result |
|------|--------|
| `cumulative-return` + any structure | ✅ SUCCESS |
| `moving-average-price` + any structure | ✅ SUCCESS |
| `current-price` + single asset | ❌ FAILS |
| `current-price` + wrapper | ❌ FAILS |

## Final Fix

**Replace `current-price` with `moving-average-price(window=1)` as a proxy for current price.**

This is semantically equivalent (1-day MA ≈ current price) but uses a function that Composer accepts in IF conditionals.

**Changes Applied:**
```python
# src/agent/stages/composer_deployer.py

# Line 126: Changed _price suffix mapping
"_price": ("moving-average-price", 1),  # Was: ("current-price", None)

# Line 187-188: Changed fallback case
return (operand, "moving-average-price", {"window": 1}, False)  # Was: current-price
```

**Before:**
```json
{
  "lhs-fn": "current-price",
  "lhs-fn-params": null
}
```

**After:**
```json
{
  "lhs-fn": "moving-average-price",
  "lhs-fn-params": {"window": 1}
}
```

## Failed Attempts

1. **`rhs-fn: null`** - Schema still rejected
2. **`lhs-fn-params: null`** - Schema still rejected
3. **`current-price` with single asset** - Schema still rejected

The issue was never about the structure or params format - **`current-price` is simply not a valid function for IF conditionals**.

---

## Working Example (CONFIRMED DEPLOYS SUCCESSFULLY)

```json
{
  "symphony_score": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "name": "Momentum Rotation Strategy",
    "step": "root",
    "weight": null,
    "children": [
      {
        "id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
        "step": "wt-cash-equal",
        "weight": null,
        "children": [
          {
            "id": "c3d4e5f6-a7b8-9012-cdef-345678901234",
            "step": "if",
            "weight": null,
            "children": [
              {
                "id": "d4e5f6a7-b8c9-0123-def0-456789012345",
                "step": "if-child",
                "lhs-fn": "cumulative-return",
                "rhs-fn": "cumulative-return",
                "weight": null,
                "lhs-val": "SPY",
                "rhs-val": 0,
                "children": [
                  {
                    "id": "e5f6a7b8-c9d0-1234-ef01-567890123456",
                    "name": "Invesco QQQ Trust",
                    "step": "asset",
                    "ticker": "QQQ",
                    "weight": null,
                    "exchange": "XNAS"
                  }
                ],
                "comparator": "gt",
                "lhs-fn-params": { "window": 50 },
                "rhs-fn-params": { "window": 50 },
                "lhs-window-days": null,
                "rhs-window-days": null,
                "rhs-fixed-value?": true,
                "is-else-condition?": false
              },
              {
                "id": "f6a7b8c9-d0e1-2345-f012-678901234567",
                "step": "if-child",
                "weight": null,
                "children": [
                  {
                    "id": "a7b8c9d0-e1f2-3456-0123-789012345678",
                    "step": "wt-cash-equal",
                    "weight": null,
                    "children": [
                      {
                        "id": "b8c9d0e1-f2a3-4567-1234-890123456789",
                        "name": "iShares 20+ Year Treasury Bond ETF",
                        "step": "asset",
                        "ticker": "TLT",
                        "weight": null,
                        "exchange": "XNAS"
                      },
                      {
                        "id": "c9d0e1f2-a3b4-5678-2345-901234567890",
                        "name": "SPDR Gold Shares",
                        "step": "asset",
                        "ticker": "GLD",
                        "weight": null,
                        "exchange": "ARCX"
                      }
                    ]
                  }
                ],
                "is-else-condition?": true
              }
            ]
          }
        ]
      }
    ],
    "rebalance": "weekly",
    "description": "Rotates between growth assets (QQQ) when SPY shows positive momentum, and defensive assets (TLT/GLD) when momentum is negative.",
    "rebalance-corridor-width": null
  }
}
```

---

## Failing Structure (CURRENT)

```json
{
  "symphony_score": {
    "id": "...",
    "name": "Dynamic Sector Leadership Rotation",
    "step": "root",
    "weight": null,
    "rebalance": "weekly",
    "description": "Test",
    "rebalance-corridor-width": null,
    "children": [
      {
        "id": "...",
        "step": "wt-cash-equal",
        "weight": null,
        "children": [
          {
            "id": "...",
            "step": "if",
            "weight": null,
            "children": [
              {
                "id": "...",
                "step": "if-child",
                "is-else-condition?": false,
                "weight": null,
                "comparator": "gt",
                "lhs-val": "VIXY",
                "lhs-fn": "current-price",
                "lhs-fn-params": {},
                "lhs-window-days": null,
                "rhs-val": 20,
                "rhs-fixed-value?": true,
                "rhs-fn": "current-price",
                "rhs-fn-params": {},
                "rhs-window-days": null,
                "children": [
                  {
                    "id": "...",
                    "step": "wt-cash-equal",
                    "weight": null,
                    "children": [
                      { "id": "...", "step": "asset", "ticker": "XLU", "exchange": "ARCX", "name": "XLU", "weight": null },
                      { "id": "...", "step": "asset", "ticker": "XLP", "exchange": "ARCX", "name": "XLP", "weight": null },
                      { "id": "...", "step": "asset", "ticker": "BIL", "exchange": "ARCX", "name": "BIL", "weight": null }
                    ]
                  }
                ]
              },
              {
                "id": "...",
                "step": "if-child",
                "is-else-condition?": true,
                "weight": null,
                "children": [
                  {
                    "id": "...",
                    "step": "wt-cash-equal",
                    "weight": null,
                    "children": [
                      { "id": "...", "step": "asset", "ticker": "XLB", "exchange": "ARCX", "name": "XLB", "weight": null },
                      { "id": "...", "step": "asset", "ticker": "XLF", "exchange": "ARCX", "name": "XLF", "weight": null },
                      { "id": "...", "step": "asset", "ticker": "XLC", "exchange": "ARCX", "name": "XLC", "weight": null }
                    ]
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  },
  "color": "#17BAFF",
  "hashtag": "#DynamicSector"
}
```

---

## Key Differences Identified

### 1. TRUE Branch Children Structure
| Working | Failing |
|---------|---------|
| Single asset directly under `if-child` | `wt-cash-equal` wrapper with 3 assets |

**Hypothesis:** TRUE branch (with condition fields) may not support `wt-cash-equal` as direct child.

### 2. Function Type
| Working | Failing |
|---------|---------|
| `cumulative-return` with `window: 50` | `current-price` with empty params `{}` |

**Hypothesis:** `current-price` may not be valid for conditional comparisons, or requires different field structure.

### 3. `rhs-fn` Field
| Working | Failing (tried both) |
|---------|---------|
| `"cumulative-return"` (matches lhs-fn) | First: `null`, Then: `"current-price"` |

**Confirmed by Gemini:** `rhs-fn` must always match `lhs-fn`, never be `null`.

### 4. Field Ordering
| Working | Failing |
|---------|---------|
| `lhs-fn`, `rhs-fn`, `weight`, `lhs-val`, `rhs-val`, `children`, ... | `is-else-condition?`, `weight`, `comparator`, `lhs-val`, ... |

**Status:** JSON field order shouldn't matter, but could be API-specific.

### 5. Asset `name` Field
| Working | Failing |
|---------|---------|
| Full name: `"Invesco QQQ Trust"` | Ticker only: `"XLU"` |

**Status:** Untested - may need full asset names.

### 6. Root Fields Order
| Working | Failing |
|---------|---------|
| `name`, `step`, `weight`, `children`, `rebalance`, `description`, ... | `name`, `step`, `weight`, `rebalance`, `description`, ..., `children` |

**Status:** Untested - may need specific ordering.

---

## Fixes Attempted

### Fix 1: `rhs-fn` = `null` when `rhs-fixed-value?` = `true`
- **Based on:** composer.md docs (line 202)
- **Result:** FAILED

### Fix 2: `rhs-fn` matches `lhs-fn` when function has params
- **Based on:** Working example uses `cumulative-return` for both
- **Result:** FAILED (only fixed for functions with params)

### Fix 3: `rhs-fn` ALWAYS matches `lhs-fn`
- **Based on:** Gemini analysis
- **Result:** FAILED - still getting schema error

### Fix 4: Removed `asset_class` from payload
- **Based on:** docs only show `symphony_score`, `color`, `hashtag`
- **Result:** FAILED - unrelated to core issue

---

## Remaining Hypotheses to Test

### A. TRUE Branch Cannot Have `wt-cash-equal` Child
The working example has:
- TRUE branch: single asset directly
- ELSE branch: `wt-cash-equal` with multiple assets

**Test:** Deploy with single asset per branch (like working example).

### B. `current-price` Function Not Valid for Conditionals
The working example uses `cumulative-return`. Maybe `current-price` has different schema requirements.

**Test:** Change condition to use `cumulative-return` instead:
```
SPY_cumulative_return_50d > 0
```

### C. Asset Names Must Be Full Names
Working example: `"name": "Invesco QQQ Trust"`
Our structure: `"name": "XLU"`

**Test:** Use full asset names.

### D. Field Ordering May Matter
The working example has a specific field order in `if-child`.

**Test:** Match exact field ordering from working example.

---

## API Details

**Endpoint:** `save_symphony` MCP tool
**Required arguments:**
- `symphony_score`: Hierarchical structure
- `color`: Hex color code (e.g., `"#17BAFF"`)
- `hashtag`: Strategy tag (e.g., `"#MOMENTUM"`)

**Node Types:**
- `root`: Top level container
- `wt-cash-equal`: Equal weight children
- `wt-cash-specified`: Custom weights (requires `allocation` field)
- `asset`: Individual security (LEAF node)
- `if`: Conditional logic container
- `if-child`: Branch of conditional

**Exchange Codes:**
- `XNYS`: NYSE
- `XNGS`: NASDAQ (per docs)
- `XNAS`: NASDAQ (per working example - may be alias)
- `ARCX`: NYSE Arca

---

## Files Modified

- `src/agent/stages/composer_deployer.py`
  - `_parse_condition()`: Updated `rhs-fn` logic
  - `_build_symphony_json()`: Removed `asset_class`
  - `_build_if_structure()`: Multiple iterations on branch structure

- `tests/agent/test_composer_deployer.py`
  - Updated assertions for `rhs-fn` behavior

---

## Next Steps

1. **Test simpler case:** Deploy with single asset per branch using `cumulative-return` condition
2. **If that works:** Incrementally add complexity to find breaking point
3. **If that fails:** Check if `current-price` specifically has issues
4. **Consider:** Fetching actual MCP schema from Composer API for validation
