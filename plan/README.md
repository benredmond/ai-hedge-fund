# Market Context Pack Generator

Automated market context generation for AI trading strategy evaluation. Provides synthesis-focused market state snapshots with strict date-anchoring to prevent future knowledge leakage.

## Quick Start

```bash
# Generate context pack with current market data
python -m src.market_context.cli generate

# Save to file
python -m src.market_context.cli generate -o data/context_packs/latest.json
```

## What It Generates

**Synthesis-First Design**: Provides high-level regime summary without overwhelming detail. AI agents can query specifics via MCP tools.

### 📊 Market Regime Snapshot
- Trend classification (bull/bear based on SPY vs 200d MA)
- Volatility regime (VIX-based: low/normal/elevated/high)
- Market breadth (% sectors above 50d MA)
- Sector leadership (top 3 leaders/laggards)
- Factor regime (value vs growth, momentum, quality, size)

### 💰 Macro Indicators (FRED API)
- Interest rates (Fed funds, 10Y/2Y treasuries, yield curve)
- Inflation (CPI, Core CPI)
- Employment (unemployment, nonfarm payrolls, wage growth)

### 📰 Recent Events
- Human-curated significant market events (30-day lookback)

### 🏷️ Regime Tags
- Automated classification for cross-cohort analysis
- Examples: `strong_bull`, `volatility_elevated`, `inverted_yield_curve`

## Output Format

```json
{
  "metadata": {
    "anchor_date": "2025-10-23T02:37:44.886338",
    "data_cutoff": "2025-10-23T02:37:44.886338",
    "generated_at": "2025-10-23T02:37:49.385687",
    "version": "v1.0.0"
  },
  "regime_snapshot": { /* trend, volatility, breadth, leadership, factors */ },
  "macro_indicators": { /* rates, inflation, employment */ },
  "recent_events": [ /* human-curated events */ ],
  "regime_tags": ["strong_bull", "volatility_normal", "growth_favored"]
}
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get FRED API key** (free): https://fred.stlouisfed.org/docs/api/api_key.html

3. **Add to `.env`:**
   ```bash
   FRED_API_KEY=your_key_here
   ```

## Usage

### CLI

```bash
# Generate and display
python -m src.market_context.cli generate

# Save to file
python -m src.market_context.cli generate --output data/context_packs/latest.json

# Save with timestamp
python -m src.market_context.cli generate -o data/context_packs/$(date +%Y-%m-%d).json
```

### Python API

```python
from src.market_context.assembler import assemble_market_context_pack
from src.market_context.validation import validate_context_pack
import os

# Generate context pack
context_pack = assemble_market_context_pack(
    fred_api_key=os.getenv('FRED_API_KEY')
)

# Validate
is_valid, errors = validate_context_pack(context_pack)

# Access data
regime = context_pack['regime_snapshot']
macro = context_pack['macro_indicators']
tags = context_pack['regime_tags']
```

## Design Principles

**Date-Anchored**: All data strictly `<= anchor_date`. Zero future knowledge leakage.

**Validation-First**: Automated checks for temporal consistency, schema correctness, data freshness.

**Test-Driven**: 26 tests, all passing. Built using strict TDD methodology (RED-GREEN-REFACTOR).

**Synthesis Over Detail**: Provides regime summary; agents can drill down via MCP tools as needed.

## Data Sources

- **yfinance**: Market data (SPY, sectors, VIX, factor ETFs) - free, no auth
- **FRED API**: Federal Reserve economic data - free with API key
- **Events**: Human-curated from `tests/fixtures/events.json`

## Testing

```bash
# Run all tests (26 tests)
./venv/bin/pytest tests/market_context/ -v

# Run specific suite
./venv/bin/pytest tests/market_context/test_fetchers.py -v

# With coverage
./venv/bin/pytest tests/market_context/ --cov=src/market_context
```

**Status**: ✅ 26/26 tests passing

## Project Structure

```
src/market_context/
├── fetchers.py          # Data collection (yfinance, FRED)
├── assembler.py         # Context pack assembly
├── validation.py        # Quality & temporal checks
└── cli.py              # Command-line interface

tests/market_context/
├── test_fetchers.py     # Fetcher unit tests (14 tests)
├── test_assembler.py    # Assembly tests (4 tests)
├── test_validation.py   # Validation tests (5 tests)
└── test_integration.py  # End-to-end tests (3 tests)
```

## Validation Checks

Automated validation ensures:
- ✅ No future data leakage (all dates <= anchor_date)
- ✅ Required fields present
- ✅ Data freshness (generated_at within 1 hour of anchor_date)
- ✅ Schema correctness
- ✅ Regime tags are valid list

## Future Work

- [ ] Narrative generator (LLM synthesis of regime + macro + events)
- [ ] Real-time event curation pipeline
- [ ] Token counting in validation
- [ ] Historical context pack versioning
