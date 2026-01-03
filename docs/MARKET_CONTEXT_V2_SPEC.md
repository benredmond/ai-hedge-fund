# Market Context Pack v2.0 Enhancement Specification

**Version:** 2.0.0  
**Status:** Approved for Implementation  
**Date:** 2025-11-02

## Executive Summary

This specification defines the enhancement of the Market Context Pack from static single-point snapshots to comprehensive historical time series with expanded macro/market coverage. The goal is to provide AI models with sufficient context to understand trends, momentum, and regime transitions without requiring extensive tool usage.

**Key Changes:**
- Convert all indicators to time series (current, 1m, 3m, 6m, 12m ago)
- Add 19 new economic/market indicators
- Expand benchmark performance to multi-period (30d, 60d, 90d, 1y)
- Maintain raw data only (no derived fields like "regime" or "changes")
- Version bump: v1.0.0 → v2.0.0

**Impact:**
- JSON size: ~3 KB → ~18-22 KB (6-7x increase)
- Total indicators: ~15 → ~35 time series
- Estimated implementation: 12-18 hours

---

## Design Principles

### 1. Raw Data Only
**No derived fields.** The v1.0 context pack included derived classifications like:
- `"regime": "easing_cycle"`
- `"trend": "rising"`
- `regime_tags: ["strong_bull", "volatility_normal"]`

These are **removed** in v2.0. AI models will interpret raw data themselves.

### 2. Monthly Snapshots
All historical data uses **monthly frequency** for consistency:
- `current`: As of anchor_date
- `1m_ago`: 1 month prior to anchor_date
- `3m_ago`: 3 months prior
- `6m_ago`: 6 months prior
- `12m_ago`: 12 months prior

**Rationale:** Monthly frequency balances signal vs noise, aligns with economic data publication schedules, and keeps data volume manageable.

### 3. Comprehensive Coverage
Context pack must address five key dimensions:
1. **Monetary Policy & Liquidity** - Rates, money supply, Fed balance sheet
2. **Economic Activity** - Manufacturing, employment, housing, consumption
3. **Market Positioning** - Sentiment, options positioning
4. **International Context** - Dollar strength, EM performance
5. **Risk Conditions** - Credit spreads, volatility, commodities

### 4. Temporal Integrity
All historical data must respect `anchor_date`:
- No future knowledge leakage
- Publication lags respected (e.g., CPI published 2 weeks after month-end)
- Validation tests enforce temporal consistency

---

## Part 1: Historical Time Series Conversion

### Pattern
Convert single-value fields to nested time series:

**Before (v1.0):**
```json
"fed_funds_rate": 3.87
```

**After (v2.0):**
```json
"fed_funds_rate": {
  "current": 3.87,
  "1m_ago": 4.12,
  "3m_ago": 4.58,
  "6m_ago": 4.83,
  "12m_ago": 5.33
}
```

### Indicators to Convert

#### Interest Rates
- `fed_funds_rate` - FRED: `DFF`
- `treasury_10y` - FRED: `DGS10`
- `treasury_2y` - FRED: `DGS2`
- `yield_curve_2s10s` - Calculated (10Y - 2Y)

#### Inflation
- `cpi_yoy` - FRED: `CPIAUCSL` (calculate YoY)
- `core_cpi_yoy` - FRED: `CPILFESL` (calculate YoY)

#### Employment
- `unemployment_rate` - FRED: `UNRATE`
- `nonfarm_payrolls` - FRED: `PAYEMS`
- `wage_growth_yoy` - FRED: `CES0500000003` (calculate YoY)

#### Market Regime
- `SPY_vs_200d_ma` - Calculate from yfinance SPY data
- `VIX_current` - yfinance `^VIX`
- `sectors_above_50d_ma_pct` - Calculate from sector ETF data
- `momentum_premium_30d` - MTUM vs SPY
- `quality_premium_30d` - QUAL vs SPY
- `size_premium_30d` - IWM vs SPY

---

## Part 2: New Economic Indicators

### Manufacturing & Production

#### ISM Manufacturing PMI
- **FRED Series:** `NAPM`
- **Description:** Purchasing Managers' Index for manufacturing sector
- **Interpretation:** >50 = expansion, <50 = contraction
- **Frequency:** Monthly
- **Time Series:** current, 1m, 3m, 6m, 12m
- **Why Important:** Leading indicator for economic activity, predicts GDP growth

#### Industrial Production Index
- **FRED Series:** `INDPRO`
- **Description:** Real output of manufacturing, mining, utilities (2017=100)
- **Frequency:** Monthly
- **Time Series:** current, 1m, 3m, 6m, 12m
- **Why Important:** Captures manufacturing output trends

#### Housing Starts
- **FRED Series:** `HOUST`
- **Description:** New residential housing units started (thousands)
- **Frequency:** Monthly
- **Time Series:** current, 1m, 3m, 6m, 12m
- **Why Important:** Leading indicator for economic growth, consumer confidence

### Consumer Indicators

#### Consumer Confidence Index
- **FRED Series:** `UMCSENT`
- **Description:** University of Michigan Consumer Sentiment Index
- **Frequency:** Monthly
- **Time Series:** current, 1m, 3m, 6m, 12m
- **Why Important:** Predicts consumer spending behavior
- **Note:** Replace v1.0 placeholder with real data

#### Retail Sales
- **FRED Series:** `RSXFS`
- **Description:** Retail Sales Excluding Food Services (millions)
- **Calculation:** YoY growth rate
- **Frequency:** Monthly
- **Time Series:** current, 1m, 3m, 6m, 12m
- **Why Important:** Direct measure of consumer spending

### Labor Market

#### Initial Unemployment Claims (4-week avg)
- **FRED Series:** `ICSA`
- **Description:** 4-week moving average of initial jobless claims (thousands)
- **Frequency:** Weekly (use 4-week MA)
- **Time Series:** current, 1m, 3m, 6m, 12m
- **Why Important:** Early warning signal for labor market deterioration

### Credit Conditions

#### Investment Grade Corporate Spread
- **FRED Series:** `BAMLC0A4CBBB`
- **Description:** BBB-rated corporate bond spread over treasury (basis points)
- **Frequency:** Daily (use month-end)
- **Time Series:** current, 1m, 3m, 6m, 12m
- **Why Important:** Measures corporate credit risk, risk appetite

#### High Yield Spread
- **FRED Series:** `BAMLH0A0HYM2`
- **Description:** High yield corporate spread over treasury (basis points)
- **Frequency:** Daily (use month-end)
- **Time Series:** current, 1m, 3m, 6m, 12m
- **Why Important:** Credit stress indicator, early recession signal

### Recession Indicators

#### Sahm Rule Recession Indicator
- **FRED Series:** `SAHMREALTIME`
- **Description:** Real-time unemployment-based recession indicator
- **Interpretation:** Value ≥0.50 signals recession onset
- **Frequency:** Monthly
- **Format:** **Single current value only** (not time series)
- **Why Important:** Reliable real-time recession signal

#### NBER Recession Indicator
- **FRED Series:** `USREC`
- **Description:** NBER-based recession periods (binary)
- **Values:** 1 = recession, 0 = expansion
- **Frequency:** Monthly
- **Format:** **Single current value only** (not time series)
- **Why Important:** Official recession dating

---

## Part 3: Tier 1 High-Priority Indicators

### Monetary Policy & Liquidity

#### M2 Money Supply
- **FRED Series:** `M2SL`
- **Description:** M2 money stock (billions of dollars)
- **Calculation:** YoY growth rate
- **Frequency:** Monthly
- **Time Series:** current, 1m, 3m, 6m, 12m
- **Why Critical:** Captures QE/QT impact on liquidity; 2022's bear market driven by M2 contraction
- **Investor Note:** "Rate policy is only half the story - quantitative tightening/easing matters enormously for asset prices"

#### Fed Balance Sheet Total Assets
- **FRED Series:** `WALCL`
- **Description:** Total Federal Reserve assets (millions)
- **Frequency:** Weekly (use month-end)
- **Time Series:** current, 1m, 3m, 6m, 12m
- **Why Critical:** Direct QE/QT indicator; balance sheet expansion/contraction drives liquidity
- **Investor Note:** Essential for understanding liquidity conditions

### Inflation Expectations

#### 10-Year TIPS Spread
- **FRED Series:** `T10YIE`
- **Description:** Market-implied inflation expectations (10Y Treasury - 10Y TIPS)
- **Frequency:** Daily (use month-end)
- **Time Series:** current, 1m, 3m, 6m, 12m
- **Why Critical:** Forward-looking inflation expectations from bond market
- **Investor Note:** Shows what market actually believes about inflation vs realized CPI

### International Context

#### US Dollar Index (DXY)
- **Source:** yfinance `DX-Y.NYB` or `UUP` (dollar ETF)
- **Description:** Dollar strength vs basket of currencies
- **Calculation:** 30d return for each period
- **Frequency:** Daily (calculate monthly returns)
- **Time Series:** current, 1m, 3m, 6m, 12m (30d returns)
- **Why Critical:** Impacts multinationals, commodities, emerging markets
- **Investor Note:** US-only focus misses global macro drivers

#### Emerging Markets Relative Performance
- **Source:** yfinance `EEM` minus `SPY`
- **Description:** EEM 30d return minus SPY 30d return
- **Frequency:** Daily (calculate monthly)
- **Time Series:** current, 1m, 3m, 6m, 12m (30d relative returns)
- **Why Critical:** Risk-on/risk-off indicator, global growth proxy
- **Investor Note:** Signals global risk appetite and growth expectations

### Positioning & Sentiment

#### AAII Investor Sentiment
- **Source:** https://www.aaii.com/sentimentsurvey/sent_results
- **Description:** Bullish %, Bearish %, Neutral % from weekly survey
- **Frequency:** Weekly (use latest)
- **Time Series:** 
  - `bullish_pct`: current, 1m, 3m, 6m, 12m
  - `bearish_pct`: current, 1m, 3m, 6m, 12m
  - `neutral_pct`: current, 1m, 3m, 6m, 12m
- **Why Critical:** Contrarian indicator (extreme bullishness = caution)
- **Investor Note:** "Helps distinguish 'fundamentally bullish regime' from 'everyone already positioned bullish' (vulnerable to reversal)"
- **Implementation Note:** No free API; may require web scraping or manual CSV update

#### CBOE Put/Call Ratio
- **Source:** yfinance `^CPCE` (equity P/C ratio) or manual
- **Description:** Total put volume / call volume
- **Frequency:** Daily (use 4-week MA)
- **Time Series:** current, 1m, 3m, 6m, 12m
- **Why Critical:** Options market positioning, fear gauge
- **Investor Note:** High ratio = defensive positioning, potential capitulation signal
- **Implementation Note:** Try yfinance first; if unavailable, defer to v2.1

### Commodities

#### Gold Performance
- **Source:** yfinance `GLD`
- **Description:** Gold ETF 30-day return
- **Frequency:** Daily (calculate monthly returns)
- **Time Series:** current, 1m, 3m, 6m, 12m (30d returns)
- **Why Critical:** Safe haven + inflation hedge behavior
- **Investor Note:** Flight to safety indicator

#### Oil Performance
- **Source:** yfinance `USO` or `CL=F`
- **Description:** Oil price 30-day return
- **Frequency:** Daily (calculate monthly returns)
- **Time Series:** current, 1m, 3m, 6m, 12m (30d returns)
- **Why Critical:** Inflation + growth signal, energy sector driver
- **Investor Note:** Captures inflation expectations and economic activity

---

## Part 4: Expanded Benchmark Performance

### Current State (v1.0)
Only 30-day returns and volatility for benchmarks.

### Enhanced State (v2.0)
Multi-period analysis: 30d, 60d, 90d, 1y

### Structure (per benchmark)
```json
"SPY": {
  "returns": {
    "30d": 2.28,
    "60d": 5.12,
    "90d": 8.45,
    "1y": 18.23
  },
  "volatility_annualized": {
    "30d": 12.42,
    "60d": 14.21,
    "90d": 15.33
  },
  "sharpe_ratio": {
    "30d": 2.24,
    "60d": 2.85,
    "90d": 3.12
  },
  "max_drawdown": {
    "30d": -2.1,
    "90d": -5.3
  }
}
```

### Benchmarks
- SPY (US large cap)
- QQQ (Nasdaq tech)
- AGG (US bonds)
- 60_40 (60% SPY, 40% AGG)
- risk_parity (simplified approximation)

### Calculations
- **Returns:** Total return over period
- **Volatility:** Annualized standard deviation of daily returns
- **Sharpe Ratio:** Annualized return / annualized volatility (0% risk-free rate)
- **Max Drawdown:** Largest peak-to-trough decline during period

---

## Complete Data Structure (v2.0)

```json
{
  "metadata": {
    "anchor_date": "2025-11-02T03:53:36.608057",
    "data_cutoff": "2025-11-02T03:53:36.608057",
    "generated_at": "2025-11-02T03:53:42.597755",
    "version": "v2.0.0"
  },
  
  "macro_indicators": {
    "interest_rates": {
      "fed_funds_rate": {"current": 3.87, "1m_ago": 4.12, "3m_ago": 4.58, "6m_ago": 4.83, "12m_ago": 5.33},
      "treasury_10y": {"current": 4.11, "1m_ago": 4.03, "3m_ago": 4.15, "6m_ago": 4.28, "12m_ago": 4.45},
      "treasury_2y": {"current": 3.61, "1m_ago": 3.55, "3m_ago": 3.82, "6m_ago": 4.12, "12m_ago": 4.58},
      "yield_curve_2s10s": {"current": 0.50, "1m_ago": 0.48, "3m_ago": 0.33, "6m_ago": 0.16, "12m_ago": -0.13}
    },
    
    "inflation": {
      "cpi_yoy": {"current": 2.79, "1m_ago": 2.85, "3m_ago": 3.12, "6m_ago": 3.48, "12m_ago": 4.21},
      "core_cpi_yoy": {"current": 2.75, "1m_ago": 2.80, "3m_ago": 3.05, "6m_ago": 3.42, "12m_ago": 4.15},
      "tips_spread_10y": {"current": 2.35, "1m_ago": 2.38, "3m_ago": 2.42, "6m_ago": 2.51, "12m_ago": 2.68}
    },
    
    "employment": {
      "unemployment_rate": {"current": 4.30, "1m_ago": 4.20, "3m_ago": 3.90, "6m_ago": 3.70, "12m_ago": 3.50},
      "nonfarm_payrolls": {"current": 159540, "1m_ago": 159120, "3m_ago": 158650, "6m_ago": 158200, "12m_ago": 157800},
      "wage_growth_yoy": {"current": 3.40, "1m_ago": 3.50, "3m_ago": 3.80, "6m_ago": 4.20, "12m_ago": 4.80},
      "initial_claims_4wk_avg": {"current": 212, "1m_ago": 208, "3m_ago": 215, "6m_ago": 225, "12m_ago": 235}
    },
    
    "manufacturing": {
      "ism_pmi": {"current": 49.1, "1m_ago": 48.7, "3m_ago": 47.2, "6m_ago": 51.3, "12m_ago": 53.8},
      "industrial_production_index": {"current": 103.9, "1m_ago": 103.8, "3m_ago": 102.1, "6m_ago": 101.5, "12m_ago": 100.2},
      "housing_starts_thousands": {"current": 1425, "1m_ago": 1398, "3m_ago": 1456, "6m_ago": 1512, "12m_ago": 1580}
    },
    
    "consumer": {
      "confidence_index": {"current": 68.3, "1m_ago": 70.1, "3m_ago": 72.5, "6m_ago": 71.8, "12m_ago": 75.2},
      "retail_sales_yoy_pct": {"current": 3.2, "1m_ago": 3.8, "3m_ago": 4.1, "6m_ago": 5.2, "12m_ago": 6.8}
    },
    
    "monetary_liquidity": {
      "m2_supply_yoy_pct": {"current": 2.1, "1m_ago": 1.8, "3m_ago": 0.5, "6m_ago": -1.2, "12m_ago": -3.8},
      "fed_balance_sheet_billions": {"current": 6587, "1m_ago": 6620, "3m_ago": 6755, "6m_ago": 6980, "12m_ago": 7450}
    },
    
    "credit_conditions": {
      "investment_grade_spread_bps": {"current": 145, "1m_ago": 138, "3m_ago": 125, "6m_ago": 118, "12m_ago": 105},
      "high_yield_spread_bps": {"current": 425, "1m_ago": 415, "3m_ago": 385, "6m_ago": 365, "12m_ago": 325}
    },
    
    "international": {
      "dollar_index_30d_return": {"current": 2.1, "1m_ago": 1.8, "3m_ago": -0.5, "6m_ago": -1.2, "12m_ago": 3.5},
      "emerging_markets_rel_return_30d": {"current": -3.2, "1m_ago": -2.8, "3m_ago": 1.2, "6m_ago": 2.1, "12m_ago": -4.5}
    },
    
    "positioning": {
      "aaii_sentiment_bullish_pct": {"current": 32.5, "1m_ago": 35.2, "3m_ago": 42.1, "6m_ago": 38.5, "12m_ago": 28.3},
      "aaii_sentiment_bearish_pct": {"current": 38.2, "1m_ago": 35.8, "3m_ago": 28.5, "6m_ago": 32.1, "12m_ago": 42.5},
      "aaii_sentiment_neutral_pct": {"current": 29.3, "1m_ago": 29.0, "3m_ago": 29.4, "6m_ago": 29.4, "12m_ago": 29.2},
      "put_call_ratio": {"current": 0.88, "1m_ago": 0.93, "3m_ago": 1.05, "6m_ago": 0.95, "12m_ago": 1.12}
    },
    
    "commodities": {
      "gold_return_30d": {"current": 3.5, "1m_ago": 2.1, "3m_ago": -1.2, "6m_ago": 4.8, "12m_ago": -2.5},
      "oil_return_30d": {"current": -2.3, "1m_ago": 1.5, "3m_ago": 5.2, "6m_ago": -3.8, "12m_ago": 8.5}
    },
    
    "recession_indicators": {
      "sahm_rule_value": 0.13,
      "nber_recession_binary": 0
    }
  },
  
  "regime_snapshot": {
    "trend": {
      "regime": "strong_bull",
      "SPY_vs_200d_ma": {"current": 12.41, "1m_ago": 10.2, "3m_ago": 8.1, "6m_ago": 5.3, "12m_ago": 2.1}
    },
    "volatility": {
      "regime": "normal",
      "VIX_current": {"current": 17.44, "1m_ago": 18.21, "3m_ago": 19.55, "6m_ago": 21.33, "12m_ago": 23.12},
      "VIX_30d_avg": 17.64
    },
    "breadth": {
      "sectors_above_50d_ma_pct": {"current": 45.5, "1m_ago": 50.0, "3m_ago": 55.5, "6m_ago": 60.0, "12m_ago": 42.5}
    },
    "sector_leadership": {
      "leaders": [["XLK", 4.09], ["XLV", 3.29], ["XLU", 2.30]],
      "laggards": [["XLF", -5.30], ["XLC", -5.46], ["XLB", -7.48]]
    },
    "dispersion": {
      "sector_return_std_30d": 3.85,
      "regime": "moderate"
    },
    "factor_regime": {
      "value_vs_growth": {"regime": "growth_favored"},
      "momentum_premium_30d": {"current": -3.63, "1m_ago": -3.20, "3m_ago": -2.80, "6m_ago": -1.50, "12m_ago": 0.50},
      "quality_premium_30d": {"current": -0.98, "1m_ago": -0.85, "3m_ago": -0.50, "6m_ago": 0.20, "12m_ago": 1.10},
      "size_premium_30d": {"current": -1.53, "1m_ago": -1.40, "3m_ago": -1.10, "6m_ago": -0.50, "12m_ago": 0.80}
    }
  },
  
  "benchmark_performance": {
    "SPY": {
      "returns": {"30d": 2.28, "60d": 5.12, "90d": 8.45, "1y": 18.23},
      "volatility_annualized": {"30d": 12.42, "60d": 14.21, "90d": 15.33},
      "sharpe_ratio": {"30d": 2.24, "60d": 2.85, "90d": 3.12},
      "max_drawdown": {"30d": -2.1, "90d": -5.3}
    },
    "QQQ": {
      "returns": {"30d": 4.46, "60d": 8.23, "90d": 12.15, "1y": 24.88},
      "volatility_annualized": {"30d": 16.78, "60d": 18.45, "90d": 19.21},
      "sharpe_ratio": {"30d": 3.24, "60d": 3.65, "90d": 4.12},
      "max_drawdown": {"30d": -3.2, "90d": -7.8}
    },
    "AGG": {
      "returns": {"30d": 0.70, "60d": 1.25, "90d": 2.15, "1y": 3.88},
      "volatility_annualized": {"30d": 3.00, "60d": 3.15, "90d": 3.28},
      "sharpe_ratio": {"30d": 2.82, "60d": 2.95, "90d": 3.05},
      "max_drawdown": {"30d": -0.5, "90d": -1.2}
    },
    "60_40": {
      "returns": {"30d": 1.65, "60d": 3.52, "90d": 5.78, "1y": 12.45},
      "volatility_annualized": {"30d": 7.55, "60d": 8.12, "90d": 8.65},
      "sharpe_ratio": {"30d": 2.66, "60d": 3.08, "90d": 3.42},
      "max_drawdown": {"30d": -1.5, "90d": -3.8}
    },
    "risk_parity": {
      "returns": {"30d": 1.49, "60d": 3.22, "90d": 5.35, "1y": 11.28},
      "volatility_annualized": {"30d": 7.71, "60d": 8.25, "90d": 8.78},
      "sharpe_ratio": {"30d": 2.35, "60d": 2.88, "90d": 3.21},
      "max_drawdown": {"30d": -1.8, "90d": -4.2},
      "note": "Simplified approximation (equal-weight SPY/AGG)"
    }
  },
  
  "recent_events": [
    {
      "date": "2025-10-22",
      "headline": "Tesla Q3: revenue $28.10B vs $28.30B est; non-GAAP EPS $0.50 vs $0.55 est",
      "category": "earnings",
      "market_impact": "TSLA -7.0% afterhours; SPY -0.5% (session)",
      "significance": "high"
    }
  ]
}
```

---

## FRED Series Reference

```python
FRED_SERIES_V2 = {
    # Existing (v1.0)
    'DFF': 'fed_funds_rate',
    'DGS10': 'treasury_10y',
    'DGS2': 'treasury_2y',
    'CPIAUCSL': 'cpi',
    'CPILFESL': 'core_cpi',
    'UNRATE': 'unemployment_rate',
    'PAYEMS': 'nonfarm_payrolls',
    'CES0500000003': 'avg_hourly_earnings',
    
    # New - Manufacturing
    'NAPM': 'ism_pmi',
    'INDPRO': 'industrial_production',
    'HOUST': 'housing_starts',
    
    # New - Consumer
    'UMCSENT': 'consumer_confidence',
    'RSXFS': 'retail_sales_ex_food',
    
    # New - Labor
    'ICSA': 'initial_claims_4wk',
    
    # New - Credit
    'BAMLC0A4CBBB': 'ig_corporate_spread',
    'BAMLH0A0HYM2': 'hy_corporate_spread',
    
    # New - Liquidity
    'M2SL': 'm2_money_supply',
    'WALCL': 'fed_balance_sheet',
    
    # New - Inflation Expectations
    'T10YIE': 'tips_spread_10y',
    
    # New - Recession
    'SAHMREALTIME': 'sahm_rule',
    'USREC': 'nber_recession'
}
```

---

## Implementation Plan

### Phase 1: Core Historical Time Series (3-4 hours)
**Files:** `src/market_context/fetchers.py`

1. Modify `fetch_macro_indicators(fred_api_key, anchor_date)`
   - Accept `anchor_date` parameter
   - For each FRED series, fetch data from 12 months prior to current
   - Extract monthly values at: current, -1m, -3m, -6m, -12m
   - Return nested structure: `{"current": X, "1m_ago": Y, ...}`
   - Calculate YoY growth rates for CPI, wages

2. Modify `fetch_regime_snapshot(anchor_date)`
   - Accept `anchor_date` parameter
   - Fetch yfinance data from 12 months prior to current
   - Calculate historical VIX values at monthly intervals
   - Calculate historical breadth (sectors above 50d MA)
   - Calculate historical factor premiums (momentum, quality, size)
   - Return nested time series structure

### Phase 2: New FRED Indicators (2-3 hours)
**Files:** `src/market_context/fetchers.py`

3. Add new FRED indicators to `fetch_macro_indicators()`
   - Manufacturing: ISM PMI, industrial production, housing starts
   - Consumer: consumer confidence, retail sales (calculate YoY)
   - Labor: initial claims (4-week MA)
   - Credit: IG spread, HY spread
   - Liquidity: M2 supply (calculate YoY), Fed balance sheet
   - Inflation expectations: TIPS spread
   - Recession: Sahm Rule (single value), NBER (single value)

### Phase 3: Market Data Indicators (2-3 hours)
**Files:** `src/market_context/fetchers.py`

4. Add new function `fetch_international_indicators(anchor_date)`
   - Dollar Index (DXY): 30d returns at monthly intervals
   - EM relative (EEM vs SPY): 30d relative returns

5. Add new function `fetch_positioning_indicators(anchor_date)`
   - AAII sentiment: bullish/bearish/neutral %
     - Implementation options:
       a. Web scraping from AAII site
       b. Manual CSV update (acceptable for v2.0)
       c. Alternative free source
   - Put/Call ratio: Try yfinance `^CPCE`
     - If unavailable, defer to v2.1

6. Add new function `fetch_commodity_indicators(anchor_date)`
   - Gold (GLD): 30d returns at monthly intervals
   - Oil (USO): 30d returns at monthly intervals

### Phase 4: Benchmark Expansion (1-2 hours)
**Files:** `src/market_context/fetchers.py`

7. Modify `fetch_benchmark_performance()`
   - Accept multiple periods: 30d, 60d, 90d, 1y
   - Calculate returns, volatility, Sharpe for each period
   - Calculate max drawdown for 30d and 90d
   - Return nested structure by period

### Phase 5: Integration & Testing (2-3 hours)
**Files:** `src/market_context/assembler.py`, `cli.py`, `validation.py`, tests

8. Update `assembler.py`
   - Modify `assemble_market_context_pack()` signature: add `anchor_date` parameter
   - Remove `classify_regime()` function
   - Remove `regime_tags` from output
   - Integrate all new data sources
   - Update version to "v2.0.0"

9. Update `cli.py`
   - Modify `print_summary()` to display time series
   - Format: "Fed Funds: 3.87% (was 5.33% 12m ago, Δ -1.46%)"
   - Add trend indicators: ↑ (rising), ↓ (falling), → (stable)
   - Display multi-period benchmark returns

10. Update `validation.py`
    - Add schema validation for nested time series structure
    - Validate all historical timestamps <= anchor_date
    - Add test for time series completeness (no null values)

11. Update `docs/market_context_schema.md`
    - Document v2.0.0 structure
    - List all FRED series codes
    - Provide example output
    - Document breaking changes from v1.0

12. Update tests
    - Create v2.0 fixtures with time series structure
    - Update `test_fetchers.py` for new indicators
    - Update `test_assembler.py` for v2.0 structure
    - Update `test_validation.py` for nested schema
    - Add integration test for complete v2.0 pack

---

## Data Source Notes

### Confirmed Available (FRED API)
✅ All macro indicators  
✅ Manufacturing indicators (ISM PMI, industrial production, housing)  
✅ Consumer indicators (confidence, retail sales)  
✅ Credit spreads (IG, HY)  
✅ Recession indicators (Sahm Rule, NBER)  
✅ Liquidity (M2, Fed balance sheet)  
✅ TIPS spread  

### Confirmed Available (yfinance)
✅ SPY, QQQ, AGG, sector ETFs  
✅ VIX  
✅ Factor ETFs (VTV, VUG, MTUM, QUAL, IWM)  
✅ Gold (GLD)  
✅ Oil (USO)  
✅ Emerging Markets (EEM)  

### Requires Testing
⚠️ **DXY (Dollar Index):** Try `DX-Y.NYB` or fallback to `UUP` (dollar ETF)  
⚠️ **Put/Call Ratio:** Try `^CPCE` via yfinance  

### Requires Manual Process
⚠️ **AAII Sentiment:** No free API
- Option 1: Web scraping (implementation complexity)
- Option 2: Manual CSV update weekly (acceptable for v2.0)
- Option 3: Use alternative sentiment source

**Decision for v2.0:** Start with manual CSV update. Automate in v2.1 if needed.

---

## Migration Strategy

### Version Bump
- **v1.0.0 → v2.0.0** (breaking change)

### Breaking Changes
1. All single-value indicators → nested time series
2. `regime_tags` removed (no derived fields)
3. `sentiment` placeholder → real data structure
4. New top-level sections: `monetary_liquidity`, `positioning`, `commodities`, `international`

### Backward Compatibility
- Keep v1.0 tests as reference (`test_v1_backwards_compat.py`)
- Update all production code to v2.0
- Generate side-by-side comparison (v1 vs v2 output)

### Rollout
1. Implement v2.0 on feature branch
2. Generate sample v2.0 output for review
3. Validate against real FRED/yfinance data
4. Merge to main
5. Update documentation
6. Generate fresh context pack for next cohort

---

## Token Impact Analysis

### JSON Size
- **v1.0:** ~3 KB
- **v2.0:** ~18-22 KB (6-7x increase)

### Context Pack Usage
- Loaded **once per workflow** at start
- Not included in every message (only summary)
- Pre-processed into regime summary for AI consumption

### Token Savings
**Before (v1.0):** AI must make ~15-20 tool calls to discover trends
- "What was Fed rate 3 months ago?" → tool call
- "What was unemployment 6 months ago?" → tool call
- "How has M2 changed?" → tool call

**After (v2.0):** All trend data in context pack
- Saves ~15-20 tool calls × ~1k tokens each = ~15-20k tokens saved
- Net benefit: ~15k token savings despite larger context pack

### Total Workflow Impact
- Current workflow: ~52-57k tokens
- Context pack increase: ~15k tokens
- Tool call savings: ~15-20k tokens
- **Net impact:** Neutral to slightly positive

---

## Success Metrics

### Technical Validation (Implementation Complete)
- [ ] All FRED series fetch successfully
- [ ] All yfinance series fetch successfully
- [ ] Historical dates respect anchor_date
- [ ] No future data leakage in validation tests
- [ ] JSON validates against v2.0 schema
- [ ] All 26+ tests passing
- [ ] Sample v2.0 output generated

### Usage Validation (After 1-2 Cohorts)
- % of charters that reference trend data (e.g., "Fed has cut 3 times")
- % of charters that reference liquidity conditions (M2, Fed balance sheet)
- % that discuss positioning/sentiment (AAII, put/call)
- % that mention international dynamics (dollar, EM)
- Identify any indicators with zero mentions → remove in v3.0

### Quality Metrics
- Reduction in tool calls during strategy creation
- AI charter quality (more context-aware reasoning)
- Time to complete strategy creation workflow

---

## Risk Assessment

### Risk 1: Data Availability Gaps
**Concern:** FRED series may have publication lags or missing months

**Mitigation:**
- Test all series for last 12 months availability
- Document known gaps (e.g., housing starts occasionally revised)
- Fallback: Use most recent available data, note in metadata

**Monitoring:** Track fetch success rates; alert if <95%

### Risk 2: External Data Sources (AAII, P/C Ratio)
**Concern:** Non-FRED data may be harder to automate

**Mitigation:**
- Start with manual CSV update (acceptable for MVP)
- Document update process clearly
- Plan automation for v2.1 if valuable

**Monitoring:** Track update frequency; ensure no stale data

### Risk 3: Token Budget
**Concern:** Larger context pack may exceed token limits

**Mitigation:**
- Context pack is small portion of total workflow
- Tool call savings offset size increase
- Can compress if needed (e.g., remove 6m snapshots, keep 1m/3m/12m)

**Monitoring:** Track total workflow token usage per cohort

### Risk 4: Maintenance Burden
**Concern:** 35 indicators = more surface area for breakage

**Mitigation:**
- Comprehensive test coverage (26+ tests)
- Monitoring/alerting on data fetch failures
- Graceful degradation (missing indicator doesn't break pack)

**Monitoring:** Weekly health checks; fix issues promptly

---

## Open Questions / Decisions

### Q1: AAII Sentiment Implementation
**Options:**
- A) Web scraping (complex, fragile)
- B) Manual CSV update weekly (simple, acceptable)
- C) Alternative sentiment source (e.g., CNN Fear & Greed)

**Decision:** Start with B (manual CSV). Revisit after 1-2 cohorts if heavily used.

### Q2: Put/Call Ratio Source
**Options:**
- A) yfinance `^CPCE` (test availability)
- B) Manual data entry
- C) Skip for v2.0, add in v2.1

**Decision:** Try A first. If unavailable, use C (defer to v2.1).

### Q3: DXY Source
**Options:**
- A) yfinance `DX-Y.NYB`
- B) Dollar ETF `UUP` as proxy
- C) Calculate from currency pairs

**Decision:** Try A first. If unavailable, use B.

### Q4: Time Series Compression
**Question:** Keep all 5 lookbacks (current, 1m, 3m, 6m, 12m) or reduce to 4?

**Decision:** Keep all 5 for v2.0. Can compress in v2.1 if token budget requires.

---

## Post-Implementation Checklist

- [ ] All implementation phases complete (1-5)
- [ ] Documentation updated (schema, README, CLAUDE.md)
- [ ] Tests passing (unit, integration, validation)
- [ ] Sample v2.0 output generated and reviewed
- [ ] Manual CSV update process documented (AAII)
- [ ] CLI `generate` command works with v2.0
- [ ] Validation catches temporal leakage
- [ ] Code review complete
- [ ] Merged to main branch
- [ ] First v2.0 context pack generated for production use

---

## Estimated Effort

| Phase | Task | Hours |
|-------|------|-------|
| 1 | Core historical time series | 3-4 |
| 2 | New FRED indicators | 2-3 |
| 3 | Market data indicators | 2-3 |
| 4 | Benchmark expansion | 1-2 |
| 5 | Integration & testing | 2-3 |
| **Total** | | **10-15** |

Additional:
- Documentation: 1-2 hours
- Code review & refinement: 2-3 hours
- **Grand Total: 13-20 hours**

---

## Next Steps

1. ✅ **Spec approved** - This document
2. ⏳ **Phase 1 implementation** - Historical time series conversion
3. ⏳ **Phase 2 implementation** - New FRED indicators
4. ⏳ **Phase 3 implementation** - Market data indicators
5. ⏳ **Phase 4 implementation** - Benchmark expansion
6. ⏳ **Phase 5 implementation** - Integration & testing
7. ⏳ **Generate sample output** - Review v2.0 pack
8. ⏳ **Documentation update** - Schema, README
9. ⏳ **Merge to main** - Production ready
10. ⏳ **First production run** - Generate context pack for Cohort 1

---

## References

- Market Context Pack v1.0: `docs/market_context_schema.md`
- FRED API Documentation: https://fred.stlouisfed.org/docs/api/
- yfinance Documentation: https://pypi.org/project/yfinance/
- Token Management Strategy: `docs/TOKEN_MANAGEMENT.md`
- Coding Guidelines: `CLAUDE.md`

---

**Document Status:** Approved  
**Implementation Status:** Ready to Begin  
**Next Review:** After Phase 1 Complete
