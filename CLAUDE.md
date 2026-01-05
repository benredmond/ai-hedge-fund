# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **AI Trading Strategy Evaluation Framework** that tests AI models' ability to create and manage sophisticated trading strategies under genuine market uncertainty. It's both a research study and a model comparison benchmark.

**Key principle:** Individual 90-day cohorts are inherently noisy, but longitudinal analysis across multiple cohorts reveals patterns in strategic decision-making capabilities.

## Token Management

The workflow uses two key strategies to manage token usage:

1. **Comprehensive Context Pack** - Pre-analyzes market regime to minimize redundant API calls
   - Macro regime (interest rates, inflation, employment)
   - Market regime (trend, volatility, breadth, sector leadership)
   - Factor premiums (value vs growth, momentum, quality, size)
   - Benchmark performance (30d returns, Sharpe, volatility)
   - Recent market events (30d lookback, curated)

2. **Per-Stage History Limits** - Optimized message retention per workflow stage
   - Candidate Generation: 20 messages (iterative with tools)
   - Edge Scoring: 10 messages (single evaluation)
   - Backtesting: 5 messages (single tool call wrapper)
   - Winner Selection: 10 messages (single-pass reasoning)
   - Charter Generation: 20 messages (complex synthesis)

**Result:** ~52-57k tokens per workflow run (30% reduction from initial 2-phase architecture)

See `docs/TOKEN_MANAGEMENT.md` for detailed token optimization strategies.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # or ./venv/bin/activate on macOS

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Create .env file with:
#   FRED_API_KEY=your_key_here
#   GOOGLE_API_KEY=your_key_here  # Gemini (Google Generative Language API)
#   DEEPSEEK_API_KEY=sk-...  # Recommended: 90% cheaper than GPT-4o
#   DEFAULT_MODEL=openai:gpt-5.2  # Optional: LLM model (default: openai:gpt-4o)
# Get FRED key at: https://fred.stlouisfed.org/docs/api/api_key.html
# Get DeepSeek key at: https://platform.deepseek.com
# Get Gemini key at: https://aistudio.google.com
```

### Environment Variables

**Required:**
- **FRED_API_KEY**: Federal Reserve Economic Data API key. Get free key at https://fred.stlouisfed.org/docs/api/api_key.html

**LLM Provider (choose one or more):**
- **OPENAI_API_KEY**: OpenAI GPT-4o (default, ~$2.50-10/M tokens)
- **ANTHROPIC_API_KEY**: Anthropic Claude
- **GOOGLE_API_KEY**: Google Gemini (requires `pydantic-ai-slim[google]`)
- **DEEPSEEK_API_KEY**: DeepSeek ($0.56/$1.68 per M tokens, 90% cheaper, excellent quality) - Get key at https://platform.deepseek.com
- **KIMI_API_KEY**: Kimi/Moonshot (~$0.50-1/$1.50-3 per M tokens, 85% cheaper) - Get key at https://platform.moonshot.ai

**Optional:**
- **DEFAULT_MODEL**: LLM model identifier for strategy creation workflow. Default: `openai:gpt-4o`
  - Format: `<provider>:<model>` (e.g., `openai:gpt-5.2`, `anthropic:claude-opus-4-5`, `google-gla:gemini-3-pro-preview`)
  - OpenAI: `openai:gpt-5.2` (Thinking), `openai:gpt-5.2-chat-latest` (Instant), `openai:gpt-5.2-pro` (Pro)
  - Anthropic: `anthropic:claude-opus-4-5`
  - Gemini: `google-gla:gemini-3-pro-preview`
  - DeepSeek: `openai:deepseek-chat` (V3.2), `openai:deepseek-reasoner` (V3.2 Thinking)
  - Kimi: `openai:kimi-k2-thinking` or `openai:kimi-k2-thinking-turbo` (reasoning models)
  - Reasoning defaults to ON unless model matches the non-reasoning allowlist (gpt-4o, gpt-4.1, gpt-4-turbo, gpt-4, gpt-3.5, claude-3/2, deepseek-chat, moonshot-*, kimi-* non-thinking).
  - Used by `create_strategy_workflow()` when model parameter not specified
- **COMPOSER_API_KEY**, **COMPOSER_API_SECRET**: Required for Composer backtesting and deployment

### Testing
```bash
# Run all tests
./venv/bin/pytest tests/market_context/ -v

# Run specific test suite
./venv/bin/pytest tests/market_context/test_fetchers.py -v
./venv/bin/pytest tests/market_context/test_assembler.py -v
./venv/bin/pytest tests/market_context/test_validation.py -v
./venv/bin/pytest tests/market_context/test_integration.py -v

# Run single test
./venv/bin/pytest tests/market_context/test_fetchers.py::TestFetchRegimeSnapshot -v

# Run with short traceback for debugging
./venv/bin/pytest tests/market_context/ -v --tb=short

# Run with coverage
./venv/bin/pytest tests/market_context/ --cov=src/market_context
```

### Market Context Pack Generation
```bash
# Generate and display context pack
python -m src.market_context.cli generate

# Save to file
python -m src.market_context.cli generate -o data/context_packs/latest.json

# Save with timestamp
python -m src.market_context.cli generate -o data/context_packs/$(date +%Y-%m-%d).json
```

## Code Architecture

### Market Context Pack System (src/market_context/)

The implemented component generates date-anchored market context snapshots for AI strategy evaluation.

**Design Philosophy:**
- **Date-anchored**: All data strictly <= anchor_date to prevent future knowledge leakage
- **Synthesis-first**: Provides high-level regime summary without overwhelming detail
- **Validation-first**: Automated temporal consistency and schema checks
- **Test-driven**: Built using strict TDD (26 passing tests)

**Module Structure:**

```
src/market_context/
├── fetchers.py          # Data collection (yfinance, FRED API)
│   ├── fetch_regime_snapshot()        # Market regime indicators
│   ├── fetch_macro_indicators()       # Economic data (rates, inflation, employment)
│   ├── fetch_recent_events()          # Human-curated market events
│   └── fetch_benchmark_performance()  # 30d benchmark returns
│
├── assembler.py         # Context pack assembly
│   ├── assemble_market_context_pack() # Main entry point
│   └── classify_regime()              # Regime tag generation
│
├── validation.py        # Quality & temporal checks
│   └── validate_context_pack()        # Ensures no future leakage
│
└── cli.py              # Command-line interface
    ├── generate_context_pack()        # CLI generate command
    └── print_summary()                # Human-readable output
```

**Key Implementation Details:**

1. **Data Sources (free, no auth except FRED):**
   - yfinance: Market data (SPY, sectors, VIX, factor ETFs)
   - FRED API: Federal Reserve economic data (requires free API key)
   - Events: Human-curated from `tests/fixtures/events.json`

2. **Regime Snapshot Structure:**
   - Trend classification (bull/bear based on SPY vs 200d MA)
   - Volatility regime (VIX-based: low/normal/elevated/high)
   - Market breadth (% sectors above 50d MA)
   - Sector leadership (top 3 leaders/laggards vs SPY)
   - Sector dispersion (standard deviation of sector returns)
   - Factor regime (value vs growth, momentum, quality, size premiums)

3. **Temporal Safety:**
   - All timestamps validated <= anchor_date
   - Generated_at must be within 1 hour of anchor_date
   - Validation catches future data leakage automatically

4. **Testing Strategy:**
   - 14 tests in test_fetchers.py (unit tests for data collection)
   - 4 tests in test_assembler.py (assembly integration)
   - 5 tests in test_validation.py (temporal/schema validation)
   - 3 tests in test_integration.py (end-to-end)

### Python API Usage

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
benchmarks = context_pack['benchmark_performance_30d']
```

### Context Pack Schema

See `docs/market_context_schema.md` for complete schema documentation.

**Key sections:**
- `metadata`: Timestamps and version info
- `regime_snapshot`: Market state (trend, volatility, breadth, leadership, factors)
- `macro_indicators`: Economic data (rates, inflation, employment)
- `benchmark_performance_30d`: 30-day returns for SPY, QQQ, AGG, 60/40, risk parity
- `recent_events`: Human-curated significant events (30-day lookback)
- `regime_tags`: Automated classification for cross-cohort analysis

## Core Architecture

### Evaluation Flow (4 Phases)

**Phase 1: Strategy Creation**
- AI receives: comprehensive market context pack (pre-analyzed regime data), historical data access, Composer tools
- Market context pack includes: macro indicators, market regime, sector leadership, factor premiums, benchmark performance, recent events, optional manual Composer pattern examples
- AI generates: 5 candidate strategies (context pack provides macro/sectors; tools used for stocks, factor ETFs, fundamentals)
- AI outputs: 1 selected "symphony" + charter document
- Charter must include: market thesis, why now, expected behavior, failure modes, selection reasoning

**Phase 2: Validation Check**
- Automated sanity filter on hidden validation period
- Red flags: Sharpe > 5, perfect timing, < 5 rebalances, > 50% single asset
- Purpose: Catch obviously overfit strategies, not prevent overfitting generally

**Phase 3: Live Trading (90 Days)**
- Strategies execute on Composer.trade automatically
- Board meetings every 30 days (Day 30, 60, 90)
- AI receives: performance report, market context, benchmark comparisons
- AI decides: HOLD (with explanation) or ADJUST (with justification)

**Phase 4: Evaluation & Scoring**
- 50% Process Quality: Charter (20%) + Board Meetings (30%)
- 50% Quantitative Performance: Sharpe vs benchmarks (25%), drawdown (15%), consistency (10%)
- Longitudinal analysis across cohorts for pattern recognition

### Benchmarking Strategy

Always compare against 6 baselines (percentile ranking):
1. SPY (US large cap)
2. QQQ (Nasdaq tech)
3. AGG (US bonds)
4. 60/40 portfolio
5. Risk Parity
6. Random strategy

**Why:** Relative performance gives cleaner signal than absolute returns in noisy markets.

## Composer.trade Platform

### Symphony Structure
Strategies ("symphonies") are built from composable blocks:
- **Assets:** Stocks, ETFs, crypto (format: `EQUITIES::AAPL//USD`, `CRYPTO::BTC//USD`)
- **Weighting:** Equal, specified, inverse volatility, market cap
- **Conditional Logic:** IF-THEN-ELSE based on technical indicators
- **Filters:** Dynamic selection from asset pools (top N by momentum, returns, etc.)
- **Groups:** Nested logic for complex decision trees

### Technical Indicators Available
- Moving averages (simple, exponential)
- Momentum (cumulative return, RSI)
- Volatility (standard deviation)
- Drawdown metrics
- Price comparisons

### Platform Constraints
- Daily price data only (no intraday)
- Must always be invested (can't hold 100% cash, use BIL for cash-like)
- No direct shorting (use inverse ETFs like SH, PSQ)
- No direct leverage (use leveraged ETFs like UPRO, TQQQ)
- Trades execute near market close (~3:50 PM ET)
- Historical backtests limited to ~3-5 years

## Key Design Decisions

### Time Horizon: 90 Days
Captures meaningful market moves while allowing 4 cohorts per year. Strategies continue running after 90 days for observational data (Days 91-180).

### Single Strategy Per Model
Forces strategic conviction. AI must choose its best idea from 5 candidates and commit.

### No Backtest Restrictions
AI can backtest freely. The eval tests whether AI creates strategies that work **forward**, not whether it can avoid overfitting backtests.

### Process + Outcomes Scoring
50/50 split ensures we evaluate both strategic thinking and results. Process evaluation catches "got lucky" scenarios.

## Rollout Strategy

**Cohort Structure:**
- New cohort every ~90 days (4 per year)
- 5-8 models per cohort
- Consider 30-day staggering for diverse market exposures

**Timeline to Insights:**
- Month 3: First cohort complete, initial observations
- Month 6: Two cohorts, early patterns
- Month 12: Four cohorts, meaningful preliminary findings
- Month 24: Eight cohorts, confident conclusions

## What This Evaluates

**Tests:**
- Forward-looking market analysis
- Strategic conviction under uncertainty
- Adaptation with new information
- Communication of complex reasoning
- Consistency across market regimes

**Does NOT test:**
- Pure prediction accuracy
- Code generation ability
- Historical pattern matching
- Backtest optimization skills

**Success criteria:** Over time, models that reason well about uncertainty should show consistency across conditions, even if individual cohorts are noisy.

## Infrastructure Requirements

### Composer Integration
- Trading account with automation enabled
- Symphony deployment via API/tools
- Automated data extraction pipeline
- Performance tracking dashboard

### Evaluation System
- Charter assessment rubric
- Board meeting scoring framework
- Quantitative metrics calculation (Sharpe, drawdown, consistency)
- Longitudinal database for cross-cohort analysis
- Benchmark strategy execution and tracking

### Board Meeting Report Generator
Must provide to AI:
- Performance vs benchmarks
- Current holdings and allocations
- Market context summary
- Drawdown metrics
- Original charter for reference

## Critical Constraints for AI Strategy Creation

When implementing strategy creation tools:
1. AI must generate exactly 5 candidates
2. AI must select 1 and explain why (vs other 4)
3. Charter must address all required sections
4. Strategy must be executable as Composer symphony
5. Validation check runs before deployment
6. No human intervention during autopilot periods

## Evaluation Rubrics

### Charter Quality (20% of total)
- Market thesis coherence
- Quality of reasoning
- Selection justification
- Clarity of expected behavior and failure modes

### Board Meeting Decisions (10% each, 30% total)
- Quality of diagnosis (what's working/not working)
- Reasoning quality
- Consistency with charter (or justified evolution)
- Strategic thinking under uncertainty

### Quantitative Metrics (50% of total)
- Sharpe ratio percentile vs 6 benchmarks (25%)
- Max drawdown management (15%)
- Consistency - % positive months, predicted behavior (10%)

## Anti-Patterns to Avoid

**Overfitting detection in validation:**
- Don't be overly strict - validation is sanity check, not prevention
- Red flags are statistical impossibilities, not just good performance
- Allow AI to iterate through its 5 candidates if needed

**Scoring:**
- Never use absolute returns as primary metric
- Always contextualize with market regime
- Don't compare across regimes without adjustment
- Focus on pairwise model comparisons over absolute scores

**Process evaluation:**
- Judge quality of reasoning, not correctness of predictions
- Value consistency with charter over pure adaptation
- Reward justified evolution, penalize thrashing

## Long-term Vision

This is a **longitudinal research project**, not a quick benchmark.

**Year 1:** Foundation - establish infrastructure, run 4 cohorts, preliminary findings

**Year 2:** Pattern recognition - 8 total cohorts, regime-specific insights, model comparison report

**Year 3+:** Scale - test variants, different time horizons, human baselines, prediction accuracy tracking

The dataset becomes more valuable over time as it captures multiple market regimes and builds statistical power.
- DO NOT SWITCH MODELS TO 4o for "efficiency"
- dont run the TestPhase5EndToEnd test
