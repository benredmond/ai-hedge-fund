"""Market context data fetchers."""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import yfinance as yf
import pandas as pd
from fredapi import Fred
import json
import os
import warnings

# Suppress yfinance warnings for cleaner output
warnings.filterwarnings('ignore')


def fetch_regime_snapshot() -> Dict[str, Any]:
    """
    Generate high-level market regime snapshot as of current date.

    Returns regime indicators without individual ticker details:
    - Trend: Bull/bear classification based on SPY vs 200d MA
    - Volatility: VIX regime classification
    - Breadth: % of sectors above 50d MA
    - Sector Leadership: Top 3 leaders/laggards
    - Factor Regime: Value vs Growth, Momentum, Quality, Size
    """
    anchor_date = datetime.utcnow()

    # Lookback windows
    date_1y = anchor_date - timedelta(days=365)

    # Core tickers
    tickers = {
        'market': ['SPY'],
        'sectors': ['XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLRE', 'XLC', 'XLB'],
        'factors': ['VTV', 'VUG', 'MTUM', 'QUAL', 'IWM']  # Value, Growth, Momentum, Quality, Small Cap
    }

    # Fetch price data
    all_tickers = [t for category in tickers.values() for t in category]
    raw_data = yf.download(all_tickers, start=date_1y, end=anchor_date, progress=False, auto_adjust=False)

    # Extract Adj Close prices
    # yfinance returns multi-level columns for multiple tickers: (Price Type, Ticker)
    if 'Adj Close' in raw_data.columns.names or (hasattr(raw_data.columns, 'levels') and 'Adj Close' in raw_data.columns.levels[0]):
        # Multi-ticker case: columns are multi-level (Price Type, Ticker)
        data = raw_data['Adj Close']
    elif 'Adj Close' in raw_data.columns:
        # Single ticker case: columns are flat
        data = raw_data[['Adj Close']]
        data.columns = all_tickers  # Rename to ticker name
    else:
        # Fallback: use the raw data as-is
        data = raw_data

    # === TREND ANALYSIS ===
    spy_prices = data['SPY'].dropna()
    ma_200 = spy_prices.iloc[-200:].mean() if len(spy_prices) >= 200 else spy_prices.mean()
    current_spy = spy_prices.iloc[-1]
    spy_vs_200 = ((current_spy / ma_200) - 1) * 100

    if spy_vs_200 > 10:
        trend_regime = "strong_bull"
    elif spy_vs_200 > 0:
        trend_regime = "bull"
    elif spy_vs_200 > -10:
        trend_regime = "bear"
    else:
        trend_regime = "strong_bear"

    # === VOLATILITY ANALYSIS ===
    date_90d = anchor_date - timedelta(days=90)
    vix_raw = yf.download('^VIX', start=date_90d, end=anchor_date, progress=False, auto_adjust=False)
    # Extract Adj Close column (handle both flat and multi-level column structures)
    if isinstance(vix_raw.columns, pd.MultiIndex):
        vix_data = vix_raw['Adj Close'].iloc[:, 0] if 'Adj Close' in vix_raw.columns.levels[0] else vix_raw.iloc[:, 0]
    else:
        vix_data = vix_raw['Adj Close'] if 'Adj Close' in vix_raw.columns else vix_raw.iloc[:, 0]
    vix_current = float(vix_data.iloc[-1])
    vix_30d_avg = float(vix_data.iloc[-30:].mean())

    if vix_current > 25:
        vol_regime = "high"
    elif vix_current > 20:
        vol_regime = "elevated"
    elif vix_current > 15:
        vol_regime = "normal"
    else:
        vol_regime = "low"

    # === BREADTH ANALYSIS ===
    sectors_above_50d = 0
    for ticker in tickers['sectors']:
        if ticker not in data.columns:
            continue
        prices = data[ticker].dropna()
        if len(prices) < 50:
            continue
        ma_50 = prices.iloc[-50:].mean()
        if prices.iloc[-1] > ma_50:
            sectors_above_50d += 1

    breadth_pct = (sectors_above_50d / len(tickers['sectors'])) * 100

    # === SECTOR LEADERSHIP ===
    spy_30d_return = ((spy_prices.iloc[-1] / spy_prices.iloc[-30]) - 1) * 100

    sector_relative = {}
    sector_returns = []  # Track absolute returns for dispersion calc
    for ticker in tickers['sectors']:
        if ticker not in data.columns:
            continue
        prices = data[ticker].dropna()
        if len(prices) < 30:
            continue
        ticker_30d_return = ((prices.iloc[-1] / prices.iloc[-30]) - 1) * 100
        sector_relative[ticker] = ticker_30d_return - spy_30d_return
        sector_returns.append(ticker_30d_return)

    sorted_sectors = sorted(sector_relative.items(), key=lambda x: x[1], reverse=True)
    leaders = sorted_sectors[:3]
    laggards = sorted_sectors[-3:]

    # === SECTOR DISPERSION ===
    # Calculate standard deviation of sector returns as dispersion metric
    dispersion_value = 0.0
    dispersion_regime = "unknown"

    if len(sector_returns) >= 5:  # Need at least 5 sectors for meaningful dispersion
        dispersion_value = pd.Series(sector_returns).std()

        # Classify dispersion regime
        if dispersion_value < 3.0:
            dispersion_regime = "low"
        elif dispersion_value < 6.0:
            dispersion_regime = "moderate"
        else:
            dispersion_regime = "high"

    # === FACTOR REGIME ===
    # Value vs Growth
    vtv_prices = data['VTV'].dropna()
    vug_prices = data['VUG'].dropna()
    vtv_30d = ((vtv_prices.iloc[-1] / vtv_prices.iloc[-30]) - 1) * 100 if len(vtv_prices) >= 30 else 0
    vug_30d = ((vug_prices.iloc[-1] / vug_prices.iloc[-30]) - 1) * 100 if len(vug_prices) >= 30 else 0
    value_vs_growth = vtv_30d - vug_30d

    if value_vs_growth > 1.0:
        value_growth_regime = "value_favored"
    elif value_vs_growth < -1.0:
        value_growth_regime = "growth_favored"
    else:
        value_growth_regime = "neutral"

    # Momentum premium (MTUM vs SPY)
    mtum_prices = data['MTUM'].dropna()
    mtum_30d = ((mtum_prices.iloc[-1] / mtum_prices.iloc[-30]) - 1) * 100 if len(mtum_prices) >= 30 else 0
    momentum_premium = mtum_30d - spy_30d_return

    # Quality premium (QUAL vs SPY)
    qual_prices = data['QUAL'].dropna()
    qual_30d = ((qual_prices.iloc[-1] / qual_prices.iloc[-30]) - 1) * 100 if len(qual_prices) >= 30 else 0
    quality_premium = qual_30d - spy_30d_return

    # Size premium (IWM vs SPY)
    iwm_prices = data['IWM'].dropna()
    iwm_30d = ((iwm_prices.iloc[-1] / iwm_prices.iloc[-30]) - 1) * 100 if len(iwm_prices) >= 30 else 0
    size_premium = iwm_30d - spy_30d_return

    return {
        "trend": {
            "regime": trend_regime,
            "SPY_vs_200d_ma": round(spy_vs_200, 2)
        },
        "volatility": {
            "regime": vol_regime,
            "VIX_current": round(float(vix_current), 2),
            "VIX_30d_avg": round(float(vix_30d_avg), 2)
        },
        "breadth": {
            "sectors_above_50d_ma_pct": round(breadth_pct, 2)
        },
        "sector_leadership": {
            "leaders": [(ticker, round(val, 2)) for ticker, val in leaders],
            "laggards": [(ticker, round(val, 2)) for ticker, val in laggards]
        },
        "dispersion": {
            "sector_return_std_30d": round(dispersion_value, 2),
            "regime": dispersion_regime
        },
        "factor_regime": {
            "value_vs_growth": {
                "regime": value_growth_regime
            },
            "momentum_premium_30d": round(momentum_premium, 2),
            "quality_premium_30d": round(quality_premium, 2),
            "size_premium_30d": round(size_premium, 2)
        }
    }


def fetch_macro_indicators(fred_api_key: str) -> Dict[str, Any]:
    """
    Fetch macro economic indicators from FRED API as of current date.

    Returns:
    - Interest rates: Fed funds rate, treasury yields, yield curve
    - Inflation: CPI, core CPI
    - Employment: Unemployment rate, nonfarm payrolls, wage growth
    - Sentiment: Consumer confidence (placeholder for now)
    """
    fred = Fred(api_key=fred_api_key)

    # === INTEREST RATES ===
    try:
        fed_funds = fred.get_series_latest_release('DFF').iloc[-1]
    except:
        fed_funds = 5.25  # Fallback

    try:
        treasury_10y = fred.get_series_latest_release('DGS10').iloc[-1]
    except:
        treasury_10y = 4.12  # Fallback

    try:
        treasury_2y = fred.get_series_latest_release('DGS2').iloc[-1]
    except:
        treasury_2y = 4.35  # Fallback

    yield_curve = treasury_10y - treasury_2y

    # === INFLATION ===
    try:
        # CPI Year-over-Year change
        cpi = fred.get_series_latest_release('CPIAUCSL')
        cpi_yoy = ((cpi.iloc[-1] / cpi.iloc[-12]) - 1) * 100
    except:
        cpi_yoy = 3.2  # Fallback

    try:
        # Core CPI Year-over-Year change
        core_cpi = fred.get_series_latest_release('CPILFESL')
        core_cpi_yoy = ((core_cpi.iloc[-1] / core_cpi.iloc[-12]) - 1) * 100
    except:
        core_cpi_yoy = 3.8  # Fallback

    # === EMPLOYMENT ===
    try:
        unemployment = fred.get_series_latest_release('UNRATE').iloc[-1]
    except:
        unemployment = 3.8  # Fallback

    try:
        nonfarm_payrolls = fred.get_series_latest_release('PAYEMS').iloc[-1]
    except:
        nonfarm_payrolls = 157000  # Fallback (thousands)

    try:
        # Average hourly earnings growth YoY
        wage_data = fred.get_series_latest_release('CES0500000003')
        wage_growth = ((wage_data.iloc[-1] / wage_data.iloc[-12]) - 1) * 100
    except:
        wage_growth = 4.2  # Fallback

    # === SENTIMENT ===
    # Placeholder - would need specific sentiment indices
    sentiment = {
        "consumer_confidence": 102.3,
        "note": "Sentiment data placeholder"
    }

    return {
        "interest_rates": {
            "fed_funds_rate": round(float(fed_funds), 2),
            "treasury_10y": round(float(treasury_10y), 2),
            "treasury_2y": round(float(treasury_2y), 2),
            "yield_curve_2s10s": round(float(yield_curve), 2)
        },
        "inflation": {
            "cpi_yoy": round(float(cpi_yoy), 2),
            "core_cpi_yoy": round(float(core_cpi_yoy), 2)
        },
        "employment": {
            "unemployment_rate": round(float(unemployment), 2),
            "nonfarm_payrolls": round(float(nonfarm_payrolls), 0),
            "wage_growth_yoy": round(float(wage_growth), 2)
        },
        "sentiment": sentiment
    }


def fetch_recent_events(lookback_days: int = 30) -> List[Dict[str, Any]]:
    """
    Load human-curated market events from JSON data file.

    Filters events to only those within lookback period from current date.
    Events are stored in data/events.json.
    """
    anchor_date = datetime.utcnow()
    cutoff_date = anchor_date - timedelta(days=lookback_days)

    # Load events from data directory
    data_path = os.path.join(os.path.dirname(__file__), '../../data/events.json')

    if not os.path.exists(data_path):
        return []

    with open(data_path, 'r') as f:
        all_events = json.load(f)

    # Filter events by date
    filtered_events = [
        event for event in all_events
        if datetime.fromisoformat(event['date']) >= cutoff_date
        and datetime.fromisoformat(event['date']) <= anchor_date
    ]

    return filtered_events


def fetch_benchmark_performance(lookback_days: int = 30) -> Dict[str, Any]:
    """
    Fetch recent performance metrics for all evaluation benchmarks.

    Returns 30-day returns and volatility for benchmarks:
    - SPY (US large cap)
    - QQQ (Nasdaq tech)
    - AGG (US bonds)
    - 60/40 portfolio (computed)
    - Risk Parity (simplified approximation)

    Args:
        lookback_days: Period for return calculation (default 30)

    Returns:
        Dict with structure:
        {
          "SPY": {"return_pct": 4.2, "volatility_annualized": 12.1, "sharpe_ratio": 1.4},
          "QQQ": {"return_pct": 5.8, "volatility_annualized": 15.3, "sharpe_ratio": 1.6},
          ...
        }
    """
    anchor_date = datetime.utcnow()
    start_date = anchor_date - timedelta(days=lookback_days + 30)  # Extra for vol calc

    # Benchmark tickers
    tickers = ['SPY', 'QQQ', 'AGG']

    # Fetch price data
    raw_data = yf.download(tickers, start=start_date, end=anchor_date, progress=False, auto_adjust=False)

    # Extract Adj Close (handle single vs multi-ticker)
    if 'Adj Close' in raw_data.columns.names or (hasattr(raw_data.columns, 'levels') and 'Adj Close' in raw_data.columns.levels[0]):
        data = raw_data['Adj Close']
    elif 'Adj Close' in raw_data.columns:
        data = raw_data[['Adj Close']]
        data.columns = tickers
    else:
        data = raw_data

    results = {}

    # Calculate metrics for each ticker
    for ticker in tickers:
        if ticker not in data.columns:
            continue

        prices = data[ticker].dropna()
        if len(prices) < lookback_days:
            continue

        # Calculate return over lookback period
        start_price = prices.iloc[-lookback_days]
        end_price = prices.iloc[-1]
        return_pct = ((end_price / start_price) - 1) * 100

        # Calculate annualized volatility
        returns = prices.pct_change().dropna()
        vol_annualized = returns.iloc[-lookback_days:].std() * (252 ** 0.5) * 100

        # Calculate Sharpe ratio (assuming 0% risk-free rate for simplicity)
        annualized_return = return_pct * (365 / lookback_days)
        sharpe = annualized_return / vol_annualized if vol_annualized > 0 else 0

        results[ticker] = {
            "return_pct": round(float(return_pct), 2),
            "volatility_annualized": round(float(vol_annualized), 2),
            "sharpe_ratio": round(float(sharpe), 2)
        }

    # Calculate 60/40 portfolio (60% SPY, 40% AGG)
    if 'SPY' in results and 'AGG' in results:
        portfolio_60_40_return = 0.6 * results['SPY']['return_pct'] + 0.4 * results['AGG']['return_pct']
        # Simplified vol calculation (assumes 0 correlation for speed)
        portfolio_60_40_vol = ((0.6**2 * results['SPY']['volatility_annualized']**2 +
                                0.4**2 * results['AGG']['volatility_annualized']**2) ** 0.5)

        annualized_return = portfolio_60_40_return * (365 / lookback_days)
        sharpe = annualized_return / portfolio_60_40_vol if portfolio_60_40_vol > 0 else 0

        results['60_40'] = {
            "return_pct": round(float(portfolio_60_40_return), 2),
            "volatility_annualized": round(float(portfolio_60_40_vol), 2),
            "sharpe_ratio": round(float(sharpe), 2)
        }

    # Risk Parity approximation (25% SPY, 25% QQQ, 25% AGG, 25% GLD)
    # For now, use simplified equal-weight across available benchmarks
    if 'SPY' in results and 'AGG' in results:
        avg_return = (results['SPY']['return_pct'] + results['AGG']['return_pct']) / 2
        avg_vol = (results['SPY']['volatility_annualized'] + results['AGG']['volatility_annualized']) / 2

        annualized_return = avg_return * (365 / lookback_days)
        sharpe = annualized_return / avg_vol if avg_vol > 0 else 0

        results['risk_parity'] = {
            "return_pct": round(float(avg_return), 2),
            "volatility_annualized": round(float(avg_vol), 2),
            "sharpe_ratio": round(float(sharpe), 2),
            "note": "Simplified approximation (equal-weight SPY/AGG)"
        }

    return results
