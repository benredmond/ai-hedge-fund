# Market Context Pack Schema

## Structure

```json
{
  "metadata": {
    "anchor_date": "ISO8601 timestamp",
    "data_cutoff": "ISO8601 timestamp",
    "generated_at": "ISO8601 timestamp",
    "version": "v1.0.0"
  },
  "regime_snapshot": {
    "trend": {
      "regime": "strong_bull | bull | bear | strong_bear",
      "SPY_vs_200d_ma": "float (percentage)"
    },
    "volatility": {
      "regime": "low | normal | elevated | high",
      "VIX_current": "float",
      "VIX_30d_avg": "float"
    },
    "breadth": {
      "sectors_above_50d_ma_pct": "float (0-100)"
    },
    "sector_leadership": {
      "leaders": [["ticker", relative_return], ...],
      "laggards": [["ticker", relative_return], ...]
    },
    "intra_sector_divergence": {
      "XLF": {
        "top": [["COF", 21.2], ["C", 18.7], ["GS", 12.3], ["MS", 10.1]],
        "bottom": [["BRK-B", -0.3], ["PGR", 1.3], ["SPGI", 2.1], ["BLK", 3.4]],
        "spread_pct": 21.5,
        "holdings_analyzed": 15
      },
      "XLK": { ... },
      "XLE": { ... },
      "...": "all 11 sectors"
    },
    "dispersion": {
      "sector_return_std_30d": "float",
      "regime": "low | moderate | high"
    },
    "factor_regime": {
      "value_vs_growth": {
        "regime": "value_favored | growth_favored | neutral"
      },
      "momentum_premium_30d": "float",
      "quality_premium_30d": "float",
      "size_premium_30d": "float"
    }
  },
  "macro_indicators": {
    "interest_rates": {
      "fed_funds_rate": "float",
      "treasury_10y": "float",
      "treasury_2y": "float",
      "yield_curve_2s10s": "float"
    },
    "inflation": {
      "cpi_yoy": "float",
      "core_cpi_yoy": "float"
    },
    "employment": {
      "unemployment_rate": "float",
      "nonfarm_payrolls": "float (thousands)",
      "wage_growth_yoy": "float"
    },
    "sentiment": {
      "consumer_confidence": "float",
      "note": "string"
    }
  },
  "benchmark_performance_30d": {
    "SPY": {
      "return_pct": "float",
      "volatility_annualized": "float",
      "sharpe_ratio": "float"
    },
    "QQQ": { ... },
    "AGG": { ... },
    "60_40": { ... },
    "risk_parity": { ... }
  },
  "recent_events": [
    {
      "date": "ISO8601 date",
      "headline": "string",
      "category": "monetary_policy | employment | earnings | geopolitical | sector_specific | inflation",
      "market_impact": "string (price moves)",
      "significance": "high | medium | low"
    }
  ],
  "regime_tags": ["string", ...]
}
```

## Field Descriptions

### regime_snapshot.dispersion
- **Purpose:** Assess whether sectors are moving together (macro-driven) or independently (stock-picker's market)
- **Calculation:** Standard deviation of sector 30-day returns
- **Interpretation:**
  - Low (<3%): Sectors moving in lockstep, macro forces dominant
  - Moderate (3-6%): Mixed environment
  - High (>6%): High sector divergence, stock selection matters

### regime_snapshot.intra_sector_divergence
- **Purpose:** Seed stock-level thinking by showing top/bottom performers within all sectors
- **Coverage:** All 11 Select Sector SPDR ETFs (XLK, XLF, XLE, XLV, XLI, XLP, XLY, XLU, XLRE, XLC, XLB)
- **Fields:**
  - `top`: Top 4 performers within sector with 30d returns (e.g., [["COF", 21.2], ["C", 18.7], ["GS", 12.3], ["MS", 10.1]])
  - `bottom`: Bottom 4 performers within sector with 30d returns
  - `spread_pct`: Difference between best and worst performer (stock selection opportunity)
  - `holdings_analyzed`: Number of stocks analyzed (from top 15 holdings of sector ETF)
- **Interpretation:**
  - High spread (>10%): Significant stock selection opportunity within sector
  - Low spread (<5%): Stocks moving together, sector ETF may be sufficient
- **Use case:** Encourages AI to consider stock-level strategies when divergence is high

### benchmark_performance_30d
- **Purpose:** Enable relative performance calibration
- **Metrics:**
  - `return_pct`: Total return over 30-day period
  - `volatility_annualized`: Annualized standard deviation of daily returns
  - `sharpe_ratio`: Annualized return / annualized volatility (assumes 0% risk-free rate)
- **Benchmarks:**
  - SPY: US large cap (S&P 500)
  - QQQ: Nasdaq tech
  - AGG: US aggregate bonds
  - 60_40: 60% SPY, 40% AGG
  - risk_parity: Simplified equal-weight approximation

### recent_events
- **Purpose:** Provide factual market context for "why now" reasoning
- **Format:** Factual headlines without interpretation
- **Categories:** Diverse to avoid narrative bias
- **Source:** Human-curated from Perplexity/ChatGPT + financial news
