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
