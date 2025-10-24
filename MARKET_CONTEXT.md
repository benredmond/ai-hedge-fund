 Design Philosophy

  Goal: Provide enough context for informed forward-looking decisions, but not so much that the AI drowns in noise or cherry-picks narratives.

  Key principle: Strictly date-anchored to cohort launch date - ZERO future knowledge leakage.

  Architecture: Three-Tier Market Context

  Tier 1: Quantitative Market State (Objective, Always Included)

  This is pure data - no interpretation. Generate programmatically from market data APIs.

  from datetime import datetime, timedelta
  import yfinance as yf
  import pandas as pd

  def generate_quantitative_context(anchor_date: datetime) -> dict:
      """
      Generate objective market metrics as of anchor_date.
      All data must have timestamps <= anchor_date.

      Data Sources (Free, High-Quality):
      - Yahoo Finance (yfinance): Price data, returns, volatility
      - FRED API: Macro indicators (rates, inflation, employment)
      - Alpha Vantage: Backup/supplementary technical indicators (free tier limited)
      """

      # Lookback windows
      date_30d = anchor_date - timedelta(days=30)
      date_90d = anchor_date - timedelta(days=90)
      date_1y = anchor_date - timedelta(days=365)

      # Core market indices
      tickers = {
          'market': ['SPY', 'QQQ', 'IWM', 'DIA'],
          'sectors': ['XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLRE', 'XLC', 'XLB'],
          'fixed_income': ['AGG', 'TLT', 'LQD', 'HYG', 'TIP'],
          'alternatives': ['GLD', 'DBC', 'VIX'],
          'international': ['EFA', 'EEM', 'FXI'],
          'factors': ['VTV', 'VUG', 'MTUM', 'QUAL']  # Value, Growth, Momentum, Quality
      }

      context = {
          "anchor_date": anchor_date.isoformat(),
          "market_levels": {},
          "returns": {},
          "volatility": {},
          "correlations": {},
          "regime_indicators": {}
      }

      # Fetch price data (with strict date filter)
      all_tickers = [t for category in tickers.values() for t in category]
      data = yf.download(all_tickers, start=date_1y, end=anchor_date, progress=False)['Adj Close']

      for category, ticker_list in tickers.items():
          for ticker in ticker_list:
              if ticker not in data.columns:
                  continue

              prices = data[ticker].dropna()

              # Current levels vs moving averages
              current = prices.iloc[-1]
              ma_50 = prices.iloc[-50:].mean()
              ma_200 = prices.iloc[-200:].mean()

              context['market_levels'][ticker] = {
                  'current': round(current, 2),
                  '50d_ma': round(ma_50, 2),
                  '200d_ma': round(ma_200, 2),
                  'vs_50d_ma': round((current / ma_50 - 1) * 100, 2),  # % above/below
                  'vs_200d_ma': round((current / ma_200 - 1) * 100, 2),
                  'support': round(prices.iloc[-90:].min(), 2),
                  'resistance': round(prices.iloc[-90:].max(), 2)
              }

              # Returns across windows
              ret_30d = (prices.iloc[-1] / prices.iloc[-30] - 1) * 100
              ret_90d = (prices.iloc[-1] / prices.iloc[-90] - 1) * 100
              ret_1y = (prices.iloc[-1] / prices.iloc[0] - 1) * 100

              context['returns'][ticker] = {
                  '30d': round(ret_30d, 2),
                  '90d': round(ret_90d, 2),
                  '1y': round(ret_1y, 2)
              }

              # Realized volatility (annualized)
              returns = prices.pct_change().dropna()
              vol_30d = returns.iloc[-30:].std() * (252 ** 0.5) * 100
              vol_90d = returns.iloc[-90:].std() * (252 ** 0.5) * 100

              context['volatility'][ticker] = {
                  '30d_annualized': round(vol_30d, 2),
                  '90d_annualized': round(vol_90d, 2)
              }

      # Regime indicators
      spy_prices = data['SPY'].dropna()
      spy_returns = spy_prices.pct_change().dropna()

      vix_data = yf.download('^VIX', start=date_90d, end=anchor_date, progress=False)['Adj Close']

      context['regime_indicators'] = {
          'trend': {
              'SPY_vs_200d_ma': context['market_levels']['SPY']['vs_200d_ma'],
              'trend_strength': 'strong_bull' if context['market_levels']['SPY']['vs_200d_ma'] > 10
                              else 'bull' if context['market_levels']['SPY']['vs_200d_ma'] > 0
                              else 'bear' if context['market_levels']['SPY']['vs_200d_ma'] < -10
                              else 'weak_bear'
          },
          'volatility': {
              'VIX_current': round(vix_data.iloc[-1], 2),
              'VIX_30d_avg': round(vix_data.iloc[-30:].mean(), 2),
              'VIX_90d_avg': round(vix_data.iloc[-90:].mean(), 2),
              'regime': 'high' if vix_data.iloc[-1] > 25
                       else 'elevated' if vix_data.iloc[-1] > 20
                       else 'normal' if vix_data.iloc[-1] > 15
                       else 'low'
          },
          'breadth': {
              # What % of sectors are above their 50d MA?
              'sectors_above_50d_ma': sum(1 for t in tickers['sectors']
                                          if t in context['market_levels']
                                          and context['market_levels'][t]['vs_50d_ma'] > 0) / len(tickers['sectors']) * 100
          }
      }

      # Sector leadership (relative performance vs SPY)
      spy_30d = context['returns']['SPY']['30d']
      sector_relative = {
          ticker: context['returns'][ticker]['30d'] - spy_30d
          for ticker in tickers['sectors']
          if ticker in context['returns']
      }

      # Top 3 leaders, bottom 3 laggards
      sorted_sectors = sorted(sector_relative.items(), key=lambda x: x[1], reverse=True)
      context['regime_indicators']['sector_leadership'] = {
          'leaders': sorted_sectors[:3],
          'laggards': sorted_sectors[-3:]
      }

      # Factor regime (style, momentum, quality, size)
      spy_30d = context['returns']['SPY']['30d']

      # Value vs Growth
      vtv_return = context['returns'].get('VTV', {}).get('30d', 0)
      vug_return = context['returns'].get('VUG', {}).get('30d', 0)
      value_vs_growth = vtv_return - vug_return

      # Momentum premium (MTUM vs SPY)
      mtum_return = context['returns'].get('MTUM', {}).get('30d', 0)
      momentum_premium = mtum_return - spy_30d

      # Quality premium (QUAL vs SPY)
      qual_return = context['returns'].get('QUAL', {}).get('30d', 0)
      quality_premium = qual_return - spy_30d

      # Size premium (IWM vs SPY) - small cap vs large cap
      iwm_return = context['returns'].get('IWM', {}).get('30d', 0)
      size_premium = iwm_return - spy_30d

      context['regime_indicators']['factor_regime'] = {
          'value_vs_growth': {
              'return_differential_30d': round(value_vs_growth, 2),
              'regime': 'value_favored' if value_vs_growth > 1.0
                       else 'growth_favored' if value_vs_growth < -1.0
                       else 'neutral'
          },
          'momentum_premium_30d': round(momentum_premium, 2),
          'quality_premium_30d': round(quality_premium, 2),
          'size_premium_30d': round(size_premium, 2)
      }

      return context

  Output example (compressed for readability):
  {
    "anchor_date": "2025-01-15T00:00:00",
    "market_levels": {
      "SPY": {
        "current": 485.23,
        "50d_ma": 478.12,
        "200d_ma": 458.34,
        "vs_50d_ma": 1.49,
        "vs_200d_ma": 5.87,
        "support": 465.00,
        "resistance": 495.50
      }
    },
    "returns": {
      "SPY": {"30d": 3.2, "90d": 8.7, "1y": 24.3}
    },
    "regime_indicators": {
      "trend": {
        "SPY_vs_200d_ma": 5.87,
        "trend_strength": "bull"
      },
      "volatility": {
        "VIX_current": 24.3,
        "VIX_30d_avg": 21.8,
        "VIX_90d_avg": 18.2,
        "regime": "elevated"
      },
      "sector_leadership": {
        "leaders": [["XLK", 4.2], ["XLY", 2.1], ["XLC", 1.8]],
        "laggards": [["XLE", -6.3], ["XLU", -2.1], ["XLRE", -1.4]]
      },
      "factor_regime": {
        "value_vs_growth": {
          "return_differential_30d": -2.3,
          "regime": "growth_favored"
        },
        "momentum_premium_30d": 1.8,
        "quality_premium_30d": 0.6,
        "size_premium_30d": -1.2
      }
    }
  }

  Tier 2: Macro & Event Context (Semi-Automated)

  This layer interprets recent macro data and filters significant events.

  def generate_macro_context(anchor_date: datetime) -> dict:
      """
      Macro economic context + significant market events.

      Data Sources:
      - FRED API (Federal Reserve Economic Data): Free, high-quality macro indicators
      - Events: Human-curated (generated via Perplexity/ChatGPT, then reviewed)
      """

      context = {
          "macro_indicators": fetch_macro_data(anchor_date),
          "significant_events": fetch_recent_events(anchor_date, lookback_days=30),
          "narrative_summary": None  # Will be populated by LLM in final assembly
      }

      return context

  def fetch_macro_data(anchor_date: datetime) -> dict:
      """
      Pull from FRED API (free Federal Reserve data).
      Focus on: rates, inflation, employment, sentiment.
      """
      # Use FRED API for all macro indicators (free, official source)
      return {
          "interest_rates": {
              "fed_funds_rate": 5.25,  # Current FFR
              "10y_treasury": 4.12,
              "2y_treasury": 4.35,
              "yield_curve_2s10s": -0.23,  # Inverted
              "recent_fed_action": "Held rates at 5.25-5.50% (Dec 2024 meeting)",
              "market_implied_cuts_next_12m": 2.5  # From fed funds futures
          },
          "inflation": {
              "cpi_yoy": 3.2,  # Most recent print
              "core_cpi_yoy": 3.8,
              "pce_yoy": 2.9,
              "trend": "declining_but_sticky"
          },
          "employment": {
              "unemployment_rate": 3.8,
              "nonfarm_payrolls_3m_avg": 185000,
              "wage_growth_yoy": 4.2,
              "trend": "softening_but_resilient"
          },
          "sentiment": {
              "consumer_confidence": 102.3,  # Univ of Michigan
              "ceo_confidence": 48,  # Conference Board
              "aaii_bull_bear_spread": 12.3  # Bullish - bearish %
          }
      }

  def fetch_recent_events(anchor_date: datetime, lookback_days: int = 30) -> list:
      """
      Event curation strategy: HUMAN-CURATED

      Process:
      1. Use Perplexity or ChatGPT to generate market event report for the period
      2. Human reviews and filters for significance
      3. Events must be date-anchored (no future knowledge leakage)

      Why human-curated:
      - Higher quality than automated keyword matching
      - Avoids LLM hallucinations about market events
      - Allows nuanced judgment on significance
      - Perplexity/ChatGPT have good market news coverage
      """

      # Human-curated event feed (generated via Perplexity/ChatGPT, then reviewed)
      events = [
          {
              "date": "2025-01-10",
              "headline": "Fed minutes signal patience on rate cuts; 2025 outlook cautious",
              "category": "monetary_policy",
              "market_impact": "SPY -0.8%, VIX +2.1",
              "significance": "high"
          },
          {
              "date": "2025-01-08",
              "headline": "December jobs report beats: 250k vs 180k expected; wage growth 4.2%",
              "category": "employment",
              "market_impact": "10Y yield +8bps, SPY -0.3%",
              "significance": "high"
          },
          {
              "date": "2024-12-18",
              "headline": "NVDA Q4 earnings beat but guidance cautious on China export restrictions",
              "category": "earnings",
              "market_impact": "NVDA -3%, XLK -1.2%",
              "significance": "medium"
          }
      ]

      # Filter to only events before anchor_date
      return [e for e in events if datetime.fromisoformat(e['date']) <= anchor_date]

  Key decision: Should macro context include forward-looking indicators (e.g., "market pricing in 2 rate cuts by Dec 2025")?

  My recommendation: YES, but only market-derived expectations (futures, options), NOT analyst predictions. This is information the AI would have access to in real trading.

  Tier 3: Narrative Summary - EXCLUDED BY DESIGN

  **DESIGN DECISION: NO NARRATIVE SUMMARY**

  The context pack deliberately does NOT include LLM-generated narrative synthesis.

  **Rationale:**
  - This is an **evaluation framework** testing AI strategic reasoning capabilities
  - Pre-digested narrative would anchor all models on the same interpretation
  - Reduces strategy diversity, defeating the core purpose of the evaluation
  - Introduces uncontrolled bias from the narrative-generating model
  - AI models being tested are capable of synthesizing raw data themselves
  - We want to test "Can AI reason about markets?" not "Can AI follow analysis?"

  **What we provide instead:**
  - Tier 1: Objective quantitative regime data
  - Tier 2: Factual macro indicators and recent events
  - NO interpretive layer that prescribes market understanding

  **If needed later:**
  After Cohort 1, if models consistently miss important patterns in the raw data:
  - Consider adding "guidance questions" (not prescriptive narrative)
  - Example: "What does negative momentum premium in a bull market suggest?"
  - Still lets AI reason, but nudges attention to important patterns

  **Bottom line:** Give all models the same raw, objective data. Let their reasoning diverge naturally. This is how we discriminate strategic thinking capability.

  Final Layer 2 Assembly

  def assemble_market_context_layer(anchor_date: datetime) -> dict:
      """
      Complete Layer 2 market context generation.

      NO narrative summary - provide only raw, objective data.
      """

      quant = generate_quantitative_context(anchor_date)
      macro = generate_macro_context(anchor_date)

      context = {
          "metadata": {
              "anchor_date": anchor_date.isoformat(),
              "data_cutoff": anchor_date.isoformat(),  # Strict: no future knowledge
              "generated_at": datetime.utcnow().isoformat(),
              "version": "v1.0.0"
          },
          "quantitative": quant,
          "macro": macro,
          # NO narrative_summary field - by design
      }

      # Regime tagging for longitudinal analysis (Phase 4 evaluation)
      context['regime_tags'] = classify_regime(quant, macro)

      return context

  def classify_regime(quant: dict, macro: dict) -> list:
      """
      Programmatic regime classification for later cohort comparison.
      These tags enable "compare within regime" analysis in Phase 4.
      """
      tags = []

      # Trend
      spy_vs_200 = quant['regime_indicators']['trend']['SPY_vs_200d_ma']
      if spy_vs_200 > 10:
          tags.append('strong_bull')
      elif spy_vs_200 > 0:
          tags.append('bull')
      elif spy_vs_200 > -10:
          tags.append('bear')
      else:
          tags.append('strong_bear')

      # Volatility
      vix_regime = quant['regime_indicators']['volatility']['regime']
      tags.append(f"volatility_{vix_regime}")

      # Macro
      if macro['macro_indicators']['interest_rates']['market_implied_cuts_next_12m'] > 1:
          tags.append('easing_expectations')
      elif macro['macro_indicators']['interest_rates']['market_implied_cuts_next_12m'] < -0.5:
          tags.append('tightening_expectations')

      # Sector rotation (are sectors moving in lockstep or diverging?)
      sector_dispersion = calculate_sector_dispersion(quant)
      if sector_dispersion > 5:
          tags.append('high_dispersion')  # Stock-picker's market
      else:
          tags.append('low_dispersion')  # Macro-driven market

      return tags
