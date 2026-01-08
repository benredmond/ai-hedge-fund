"""Market context data fetchers."""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import yfinance as yf
import pandas as pd
from fredapi import Fred
import json
import os
import warnings
from dateutil.relativedelta import relativedelta

# Suppress yfinance warnings for cleaner output
warnings.filterwarnings('ignore')


# Top 15 holdings by weight for each Select Sector SPDR ETF (as of Dec 30, 2025)
# Used for intra-sector divergence analysis to seed stock-level thinking
SECTOR_TOP_HOLDINGS = {
    "XLK": ["NVDA", "AAPL", "MSFT", "AVGO", "PLTR", "AMD", "ORCL", "MU", "CSCO", "IBM", "CRM", "LRCX", "AMAT", "APP", "INTU"],
    "XLF": ["BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "C", "AXP", "SCHW", "SPGI", "BLK", "COF", "PGR"],
    "XLE": ["XOM", "CVX", "COP", "WMB", "SLB", "EOG", "KMI", "PSX", "VLO", "MPC", "OKE", "BKR", "TRGP", "EQT", "OXY"],
    "XLV": ["LLY", "JNJ", "ABBV", "UNH", "MRK", "TMO", "ABT", "ISRG", "AMGN", "GILD", "DHR", "BSX", "PFE", "MDT", "SYK"],
    "XLI": ["GE", "CAT", "RTX", "GEV", "BA", "UBER", "UNP", "HON", "ETN", "DE", "PH", "ADP", "LMT", "TT", "GD"],
    "XLP": ["WMT", "COST", "PG", "KO", "PM", "PEP", "MDLZ", "MO", "CL", "MNST", "TGT", "KDP", "KR", "SYY", "KMB"],
    "XLY": ["AMZN", "TSLA", "HD", "MCD", "BKNG", "TJX", "LOW", "SBUX", "DASH", "ORLY", "GM", "NKE", "RCL", "MAR", "HLT"],
    "XLU": ["NEE", "CEG", "SO", "DUK", "AEP", "SRE", "VST", "D", "EXC", "XEL", "ETR", "PEG", "ED", "PCG", "WEC"],
    "XLRE": ["WELL", "PLD", "AMT", "EQIX", "SPG", "CBRE", "O", "DLR", "PSA", "CCI", "VTR", "VICI", "CSGP", "EXR", "AVB"],
    "XLC": ["META", "GOOGL", "GOOG", "NFLX", "CMCSA", "DIS", "TTWO", "TMUS", "VZ", "T", "EA", "WBD", "OMC", "LYV", "CHTR"],
    "XLB": ["LIN", "NEM", "CRH", "SHW", "FCX", "ECL", "APD", "CTVA", "MLM", "NUE", "VMC", "STLD", "PPG", "IP", "SW"],
}


def _get_monthly_offsets(anchor_date: datetime) -> Dict[str, datetime]:
    """
    Calculate monthly offset dates for time series.
    
    Returns dict with keys: 'current', '1m_ago', '3m_ago', '6m_ago', '12m_ago'
    """
    return {
        'current': anchor_date,
        '1m_ago': anchor_date - relativedelta(months=1),
        '3m_ago': anchor_date - relativedelta(months=3),
        '6m_ago': anchor_date - relativedelta(months=6),
        '12m_ago': anchor_date - relativedelta(months=12)
    }


def _get_fred_time_series(fred: Fred, series_id: str, anchor_date: datetime, 
                          lookback_months: int = 12) -> Dict[str, float]:
    """
    Fetch FRED series and extract monthly snapshots.
    
    Returns dict with keys: 'current', '1m_ago', '3m_ago', '6m_ago', '12m_ago'
    """
    try:
        # Fetch data from 13 months ago to anchor_date (extra month for safety)
        start_date = anchor_date - relativedelta(months=lookback_months + 1)
        series_data = fred.get_series(series_id, start_date=start_date, end_date=anchor_date)
        
        if len(series_data) == 0:
            return None
        
        # Get monthly offsets
        offsets = _get_monthly_offsets(anchor_date)
        
        # Extract values at each offset (use nearest available date)
        result = {}
        for key, target_date in offsets.items():
            # Find nearest date in series (within 120 days tolerance for monthly economic data)
            # Note: Economic indicators have publication lags (1-2 months typical)
            idx = series_data.index.get_indexer([target_date], method='nearest', tolerance=pd.Timedelta(days=120))
            if idx[0] != -1:
                result[key] = round(float(series_data.iloc[idx[0]]), 2)
            else:
                result[key] = None
        
        return result
    except Exception as e:
        print(f"Warning: Failed to fetch FRED series {series_id}: {e}")
        return None


def _calculate_yoy_growth_time_series(fred: Fred, series_id: str, 
                                       anchor_date: datetime) -> Dict[str, float]:
    """
    Calculate year-over-year growth rates at monthly intervals.
    
    Returns dict with YoY growth rates at: current, 1m_ago, 3m_ago, 6m_ago, 12m_ago
    """
    try:
        # Fetch 24 months of data to calculate YoY for 12m_ago point
        start_date = anchor_date - relativedelta(months=24)
        series_data = fred.get_series(series_id, start_date=start_date, end_date=anchor_date)
        
        if len(series_data) < 13:  # Need at least 13 months for YoY calc
            return None
        
        # Get monthly offsets
        offsets = _get_monthly_offsets(anchor_date)
        
        # Calculate YoY growth at each offset
        result = {}
        for key, target_date in offsets.items():
            # Find nearest available data point to target_date (handles release lag)
            idx = series_data.index.get_indexer([target_date], method='nearest', tolerance=pd.Timedelta(days=120))
            if idx[0] == -1:
                result[key] = None
                continue

            current_idx = idx[0]
            current_date = series_data.index[current_idx].to_pydatetime()
            current_val = series_data.iloc[current_idx]

            # Compute YoY using the actual data date (not anchor_date) to avoid skew
            prior_date = current_date - relativedelta(months=12)
            idx_12m = series_data.index.get_indexer([prior_date], method='nearest', tolerance=pd.Timedelta(days=120))

            if idx_12m[0] == -1:
                result[key] = None
                continue

            prior_val = series_data.iloc[idx_12m[0]]
            yoy_growth = ((current_val / prior_val) - 1) * 100
            result[key] = round(float(yoy_growth), 2)
        
        return result
    except Exception as e:
        print(f"Warning: Failed to calculate YoY growth for {series_id}: {e}")
        return None


def fetch_regime_snapshot(anchor_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Generate high-level market regime snapshot with historical time series.

    Args:
        anchor_date: Date to anchor data (default: current UTC time)

    Returns regime indicators without individual ticker details:
    - Trend: Bull/bear classification based on SPY vs 200d MA (time series)
    - Volatility: VIX regime classification (time series)
    - Breadth: % of sectors above 50d MA (time series)
    - Sector Leadership: Top 3 leaders/laggards (current only)
    - Factor Regime: Value vs Growth, Momentum, Quality, Size (time series)
    """
    if anchor_date is None:
        anchor_date = datetime.utcnow()

    # Lookback windows - need 12 months for time series + 200 days for MA calculation
    # Need ~252 trading days per year. For 12m + 200 trading days:
    # 365 calendar days (12m) + 285 calendar days (200 trading days) = 650 + buffer
    # Add extra buffer for weekends/holidays
    start_date = anchor_date - timedelta(days=700)

    # Core tickers
    tickers = {
        'market': ['SPY'],
        'sectors': ['XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLRE', 'XLC', 'XLB'],
        'factors': ['VTV', 'VUG', 'MTUM', 'QUAL', 'IWM']  # Value, Growth, Momentum, Quality, Small Cap
    }

    # Fetch price data
    all_tickers = [t for category in tickers.values() for t in category]
    raw_data = yf.download(all_tickers, start=start_date, end=anchor_date, progress=False, auto_adjust=False)

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
    
    # Get monthly offsets for time series calculations
    offsets = _get_monthly_offsets(anchor_date)

    # === TREND ANALYSIS (TIME SERIES) ===
    spy_prices = data['SPY'].dropna()
    spy_vs_200_ts = {}
    
    for key, target_date in offsets.items():
        # Find nearest date in price data
        idx = spy_prices.index.get_indexer([target_date], method='nearest', tolerance=pd.Timedelta(days=5))
        if idx[0] != -1 and idx[0] >= 200:
            # Calculate 200d MA as of target date
            ma_200 = spy_prices.iloc[idx[0]-200:idx[0]].mean()
            current_spy = spy_prices.iloc[idx[0]]
            spy_vs_200 = ((current_spy / ma_200) - 1) * 100
            spy_vs_200_ts[key] = round(spy_vs_200, 2)
        else:
            spy_vs_200_ts[key] = None
    
    # Regime classification based on current value
    current_spy_vs_200 = spy_vs_200_ts.get('current', 0)
    if current_spy_vs_200 > 10:
        trend_regime = "strong_bull"
    elif current_spy_vs_200 > 0:
        trend_regime = "bull"
    elif current_spy_vs_200 > -10:
        trend_regime = "bear"
    else:
        trend_regime = "strong_bear"

    # === VOLATILITY ANALYSIS (TIME SERIES) ===
    vix_raw = yf.download('^VIX', start=start_date, end=anchor_date, progress=False, auto_adjust=False)
    # Extract Adj Close column (handle both flat and multi-level column structures)
    if isinstance(vix_raw.columns, pd.MultiIndex):
        vix_data = vix_raw['Adj Close'].iloc[:, 0] if 'Adj Close' in vix_raw.columns.levels[0] else vix_raw.iloc[:, 0]
    else:
        vix_data = vix_raw['Adj Close'] if 'Adj Close' in vix_raw.columns else vix_raw.iloc[:, 0]
    
    # Calculate VIX time series
    vix_current_ts = {}
    for key, target_date in offsets.items():
        idx = vix_data.index.get_indexer([target_date], method='nearest', tolerance=pd.Timedelta(days=5))
        if idx[0] != -1:
            vix_current_ts[key] = round(float(vix_data.iloc[idx[0]]), 2)
        else:
            vix_current_ts[key] = None
    
    # Get current VIX for regime classification
    vix_current = vix_current_ts.get('current', 20)
    vix_30d_avg = float(vix_data.iloc[-30:].mean()) if len(vix_data) >= 30 else vix_current

    if vix_current > 25:
        vol_regime = "high"
    elif vix_current > 20:
        vol_regime = "elevated"
    elif vix_current > 15:
        vol_regime = "normal"
    else:
        vol_regime = "low"

    # === BREADTH ANALYSIS (TIME SERIES) ===
    breadth_ts = {}
    for key, target_date in offsets.items():
        sectors_above_50d = 0
        for ticker in tickers['sectors']:
            if ticker not in data.columns:
                continue
            prices = data[ticker].dropna()
            # Find index for target date
            idx = prices.index.get_indexer([target_date], method='nearest', tolerance=pd.Timedelta(days=5))
            if idx[0] != -1 and idx[0] >= 50:
                ma_50 = prices.iloc[idx[0]-50:idx[0]].mean()
                if prices.iloc[idx[0]] > ma_50:
                    sectors_above_50d += 1
        
        breadth_ts[key] = round((sectors_above_50d / len(tickers['sectors'])) * 100, 2)
    
    breadth_pct = breadth_ts.get('current', 0)

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

    # === FACTOR REGIME (TIME SERIES) ===
    # Value vs Growth
    vtv_prices = data['VTV'].dropna()
    vug_prices = data['VUG'].dropna()
    mtum_prices = data['MTUM'].dropna()
    qual_prices = data['QUAL'].dropna()
    iwm_prices = data['IWM'].dropna()
    
    momentum_premium_ts = {}
    quality_premium_ts = {}
    size_premium_ts = {}
    
    for key, target_date in offsets.items():
        # Find indices for target date
        spy_idx = spy_prices.index.get_indexer([target_date], method='nearest', tolerance=pd.Timedelta(days=5))
        
        if spy_idx[0] != -1 and spy_idx[0] >= 30:
            # Calculate SPY 30d return at target date
            spy_30d_return = ((spy_prices.iloc[spy_idx[0]] / spy_prices.iloc[spy_idx[0]-30]) - 1) * 100
            
            # Momentum premium (MTUM vs SPY)
            mtum_idx = mtum_prices.index.get_indexer([target_date], method='nearest', tolerance=pd.Timedelta(days=5))
            if mtum_idx[0] != -1 and mtum_idx[0] >= 30:
                mtum_30d = ((mtum_prices.iloc[mtum_idx[0]] / mtum_prices.iloc[mtum_idx[0]-30]) - 1) * 100
                momentum_premium_ts[key] = round(mtum_30d - spy_30d_return, 2)
            else:
                momentum_premium_ts[key] = None
            
            # Quality premium (QUAL vs SPY)
            qual_idx = qual_prices.index.get_indexer([target_date], method='nearest', tolerance=pd.Timedelta(days=5))
            if qual_idx[0] != -1 and qual_idx[0] >= 30:
                qual_30d = ((qual_prices.iloc[qual_idx[0]] / qual_prices.iloc[qual_idx[0]-30]) - 1) * 100
                quality_premium_ts[key] = round(qual_30d - spy_30d_return, 2)
            else:
                quality_premium_ts[key] = None
            
            # Size premium (IWM vs SPY)
            iwm_idx = iwm_prices.index.get_indexer([target_date], method='nearest', tolerance=pd.Timedelta(days=5))
            if iwm_idx[0] != -1 and iwm_idx[0] >= 30:
                iwm_30d = ((iwm_prices.iloc[iwm_idx[0]] / iwm_prices.iloc[iwm_idx[0]-30]) - 1) * 100
                size_premium_ts[key] = round(iwm_30d - spy_30d_return, 2)
            else:
                size_premium_ts[key] = None
        else:
            momentum_premium_ts[key] = None
            quality_premium_ts[key] = None
            size_premium_ts[key] = None
    
    # Classify value/growth regime based on current values
    vtv_current_idx = vtv_prices.index.get_indexer([anchor_date], method='nearest', tolerance=pd.Timedelta(days=5))
    vug_current_idx = vug_prices.index.get_indexer([anchor_date], method='nearest', tolerance=pd.Timedelta(days=5))
    
    if vtv_current_idx[0] != -1 and vug_current_idx[0] != -1 and vtv_current_idx[0] >= 30 and vug_current_idx[0] >= 30:
        vtv_30d = ((vtv_prices.iloc[vtv_current_idx[0]] / vtv_prices.iloc[vtv_current_idx[0]-30]) - 1) * 100
        vug_30d = ((vug_prices.iloc[vug_current_idx[0]] / vug_prices.iloc[vug_current_idx[0]-30]) - 1) * 100
        value_vs_growth_spread = vtv_30d - vug_30d

        if value_vs_growth_spread > 1.0:
            value_growth_regime = "value_favored"
        elif value_vs_growth_spread < -1.0:
            value_growth_regime = "growth_favored"
        else:
            value_growth_regime = "neutral"
    else:
        value_growth_regime = "neutral"
        value_vs_growth_spread = None

    return {
        "trend": {
            "regime": trend_regime,
            "SPY_vs_200d_ma": spy_vs_200_ts
        },
        "volatility": {
            "regime": vol_regime,
            "VIX_current": vix_current_ts,
            "VIX_30d_avg": round(float(vix_30d_avg), 2)
        },
        "breadth": {
            "sectors_above_50d_ma_pct": breadth_ts
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
                "regime": value_growth_regime,
                "spread_30d": round(float(value_vs_growth_spread), 2) if value_vs_growth_spread is not None else None
            },
            "momentum_premium_30d": momentum_premium_ts,
            "quality_premium_30d": quality_premium_ts,
            "size_premium_30d": size_premium_ts
        }
    }


def fetch_macro_indicators(fred_api_key: str, anchor_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Fetch macro economic indicators from FRED API with historical time series.

    Args:
        fred_api_key: FRED API key
        anchor_date: Date to anchor data (default: current UTC time)

    Returns:
    - Interest rates: Fed funds rate, treasury yields, yield curve (time series)
    - Inflation: CPI, core CPI (time series)
    - Employment: Unemployment rate, nonfarm payrolls, wage growth (time series)
    - Sentiment: Consumer confidence (placeholder for now)
    
    Each indicator returns dict with keys: current, 1m_ago, 3m_ago, 6m_ago, 12m_ago
    """
    if anchor_date is None:
        anchor_date = datetime.utcnow()
    
    fred = Fred(api_key=fred_api_key)

    # === INTEREST RATES ===
    fed_funds_ts = _get_fred_time_series(fred, 'DFF', anchor_date)
    treasury_10y_ts = _get_fred_time_series(fred, 'DGS10', anchor_date)
    treasury_2y_ts = _get_fred_time_series(fred, 'DGS2', anchor_date)
    
    # Calculate yield curve for each time point
    yield_curve_ts = {}
    if treasury_10y_ts and treasury_2y_ts:
        for key in ['current', '1m_ago', '3m_ago', '6m_ago', '12m_ago']:
            if treasury_10y_ts.get(key) is not None and treasury_2y_ts.get(key) is not None:
                yield_curve_ts[key] = round(treasury_10y_ts[key] - treasury_2y_ts[key], 2)
            else:
                yield_curve_ts[key] = None

    # === INFLATION (Year-over-Year growth) ===
    cpi_yoy_ts = _calculate_yoy_growth_time_series(fred, 'CPIAUCSL', anchor_date)
    core_cpi_yoy_ts = _calculate_yoy_growth_time_series(fred, 'CPILFESL', anchor_date)
    tips_spread_ts = _get_fred_time_series(fred, 'T10YIE', anchor_date)

    # === EMPLOYMENT ===
    unemployment_ts = _get_fred_time_series(fred, 'UNRATE', anchor_date)
    nonfarm_payrolls_ts = _get_fred_time_series(fred, 'PAYEMS', anchor_date)
    wage_growth_yoy_ts = _calculate_yoy_growth_time_series(fred, 'CES0500000003', anchor_date)
    initial_claims_ts = _get_fred_time_series(fred, 'ICSA', anchor_date)

    # === MANUFACTURING & PRODUCTION ===
    # Note: ISM PMI (NAPM) not available in FRED, use alternative or skip
    industrial_production_ts = _get_fred_time_series(fred, 'INDPRO', anchor_date)
    housing_starts_ts = _get_fred_time_series(fred, 'HOUST', anchor_date)

    # === CONSUMER ===
    consumer_confidence_ts = _get_fred_time_series(fred, 'UMCSENT', anchor_date)
    retail_sales_yoy_ts = _calculate_yoy_growth_time_series(fred, 'RSXFS', anchor_date)

    # === CREDIT CONDITIONS ===
    # Note: FRED returns credit spreads in percentage points, convert to basis points (* 100)
    ig_spread_raw = _get_fred_time_series(fred, 'BAMLC0A4CBBB', anchor_date)
    hy_spread_raw = _get_fred_time_series(fred, 'BAMLH0A0HYM2', anchor_date)
    
    # Convert to basis points
    ig_spread_ts = {}
    if ig_spread_raw:
        for key, value in ig_spread_raw.items():
            ig_spread_ts[key] = round(value * 100, 0) if value is not None else None
    
    hy_spread_ts = {}
    if hy_spread_raw:
        for key, value in hy_spread_raw.items():
            hy_spread_ts[key] = round(value * 100, 0) if value is not None else None

    # === MONETARY LIQUIDITY ===
    m2_supply_yoy_ts = _calculate_yoy_growth_time_series(fred, 'M2SL', anchor_date)
    fed_balance_sheet_ts = _get_fred_time_series(fred, 'WALCL', anchor_date)
    
    # Convert Fed balance sheet from millions to billions
    fed_balance_sheet_billions_ts = {}
    if fed_balance_sheet_ts:
        for key, value in fed_balance_sheet_ts.items():
            fed_balance_sheet_billions_ts[key] = round(value / 1000, 0) if value is not None else None

    # === RECESSION INDICATORS (single values, not time series) ===
    try:
        sahm_rule = fred.get_series('SAHMREALTIME', start_date=anchor_date - relativedelta(months=1), end_date=anchor_date)
        sahm_rule_value = round(float(sahm_rule.iloc[-1]), 2) if len(sahm_rule) > 0 else None
    except:
        sahm_rule_value = None

    try:
        nber_recession = fred.get_series('USREC', start_date=anchor_date - relativedelta(months=1), end_date=anchor_date)
        nber_recession_value = int(nber_recession.iloc[-1]) if len(nber_recession) > 0 else None
    except:
        nber_recession_value = None

    # === LEADING INDICATORS (forward-looking regime signals) ===
    # Yield curve 3m10y spread (better recession predictor than 2s10s)
    yield_curve_3m10y_ts = _get_fred_time_series(fred, 'T10Y3M', anchor_date)

    # Credit spread differential (HY - IG) - wider = credit stress
    credit_spread_diff_ts = {}
    if hy_spread_ts and ig_spread_ts:
        for key in ['current', '1m_ago', '3m_ago', '6m_ago', '12m_ago']:
            hy_val = hy_spread_ts.get(key)
            ig_val = ig_spread_ts.get(key)
            if hy_val is not None and ig_val is not None:
                credit_spread_diff_ts[key] = round(hy_val - ig_val, 0)
            else:
                credit_spread_diff_ts[key] = None

    # Leading Economic Index (Philadelphia Fed composite)
    lei_composite_ts = _get_fred_time_series(fred, 'USSLIND', anchor_date)

    # Building permits (leading indicator for construction/housing)
    building_permits_ts = _get_fred_time_series(fred, 'PERMIT', anchor_date)

    # Manufacturing new orders (leading indicator for manufacturing demand)
    manufacturing_orders_ts = _get_fred_time_series(fred, 'AMTMNO', anchor_date)

    # Convert manufacturing orders from raw to millions (already in millions from FRED)
    # No conversion needed - FRED AMTMNO is in millions of dollars

    return {
        "interest_rates": {
            "fed_funds_rate": fed_funds_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "treasury_10y": treasury_10y_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "treasury_2y": treasury_2y_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "yield_curve_2s10s": yield_curve_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None}
        },
        "inflation": {
            "cpi_yoy": cpi_yoy_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "core_cpi_yoy": core_cpi_yoy_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "tips_spread_10y": tips_spread_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None}
        },
        "employment": {
            "unemployment_rate": unemployment_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "nonfarm_payrolls": nonfarm_payrolls_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "wage_growth_yoy": wage_growth_yoy_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "initial_claims_4wk_avg": initial_claims_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None}
        },
        "manufacturing": {
            "industrial_production_index": industrial_production_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "housing_starts_thousands": housing_starts_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None}
        },
        "consumer": {
            "confidence_index": consumer_confidence_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "retail_sales_yoy_pct": retail_sales_yoy_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None}
        },
        "credit_conditions": {
            "investment_grade_spread_bps": ig_spread_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "high_yield_spread_bps": hy_spread_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None}
        },
        "monetary_liquidity": {
            "m2_supply_yoy_pct": m2_supply_yoy_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "fed_balance_sheet_billions": fed_balance_sheet_billions_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None}
        },
        "recession_indicators": {
            "sahm_rule_value": sahm_rule_value,
            "nber_recession_binary": nber_recession_value
        },
        "leading_indicators": {
            "yield_curve_3m10y": yield_curve_3m10y_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "credit_spread_differential_bps": credit_spread_diff_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "lei_composite": lei_composite_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "building_permits_thousands": building_permits_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "manufacturing_new_orders_millions": manufacturing_orders_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None}
        }
    }


def fetch_international_and_commodities(anchor_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Fetch international context and commodity indicators.
    
    Args:
        anchor_date: Date to anchor data (default: current UTC time)
    
    Returns:
        Dict with international and commodities sections containing time series data
    """
    if anchor_date is None:
        anchor_date = datetime.utcnow()
    
    # Fetch 13 months of data for time series calculations
    start_date = anchor_date - timedelta(days=450)
    
    # Get monthly offsets
    offsets = _get_monthly_offsets(anchor_date)
    
    # === INTERNATIONAL CONTEXT ===
    # Dollar Index (DXY) - 30-day returns at each offset
    try:
        dxy_data = yf.download('DX-Y.NYB', start=start_date, end=anchor_date, progress=False, auto_adjust=False)
        if isinstance(dxy_data.columns, pd.MultiIndex):
            dxy_prices = dxy_data['Adj Close'].iloc[:, 0] if 'Adj Close' in dxy_data.columns.levels[0] else dxy_data['Close'].iloc[:, 0]
        elif 'Adj Close' in dxy_data.columns:
            dxy_prices = dxy_data['Adj Close']
        else:
            dxy_prices = dxy_data['Close'] if 'Close' in dxy_data.columns else None
        
        if dxy_prices is not None:
            dxy_prices = dxy_prices.dropna()
    except:
        dxy_prices = None
    
    dollar_index_ts = {}
    if dxy_prices is not None and len(dxy_prices) > 30:
        for key, target_date in offsets.items():
            idx = dxy_prices.index.get_indexer([target_date], method='nearest', tolerance=pd.Timedelta(days=5))
            if idx[0] != -1 and idx[0] >= 30:
                # Calculate 30-day return
                current_price = float(dxy_prices.iloc[idx[0]])
                past_price = float(dxy_prices.iloc[idx[0]-30])
                return_30d = ((current_price / past_price) - 1) * 100
                dollar_index_ts[key] = round(return_30d, 2)
            else:
                dollar_index_ts[key] = None
    
    # Emerging Markets relative performance (EEM vs SPY)
    try:
        eem_spy_data = yf.download(['EEM', 'SPY'], start=start_date, end=anchor_date, progress=False, auto_adjust=False)
        if 'Adj Close' in eem_spy_data.columns.names or (hasattr(eem_spy_data.columns, 'levels') and 'Adj Close' in eem_spy_data.columns.levels[0]):
            prices = eem_spy_data['Adj Close']
        else:
            prices = eem_spy_data
        
        eem_prices = prices['EEM'].dropna()
        spy_prices = prices['SPY'].dropna()
    except:
        eem_prices = None
        spy_prices = None
    
    em_relative_ts = {}
    if eem_prices is not None and spy_prices is not None and len(eem_prices) > 30 and len(spy_prices) > 30:
        for key, target_date in offsets.items():
            eem_idx = eem_prices.index.get_indexer([target_date], method='nearest', tolerance=pd.Timedelta(days=5))
            spy_idx = spy_prices.index.get_indexer([target_date], method='nearest', tolerance=pd.Timedelta(days=5))
            
            if eem_idx[0] != -1 and spy_idx[0] != -1 and eem_idx[0] >= 30 and spy_idx[0] >= 30:
                # Calculate 30d returns for both
                eem_return = ((float(eem_prices.iloc[eem_idx[0]]) / float(eem_prices.iloc[eem_idx[0]-30])) - 1) * 100
                spy_return = ((float(spy_prices.iloc[spy_idx[0]]) / float(spy_prices.iloc[spy_idx[0]-30])) - 1) * 100
                relative_return = eem_return - spy_return
                em_relative_ts[key] = round(relative_return, 2)
            else:
                em_relative_ts[key] = None
    
    # === COMMODITIES ===
    # Gold (GLD) - 30-day returns
    try:
        gld_data = yf.download('GLD', start=start_date, end=anchor_date, progress=False, auto_adjust=False)
        if isinstance(gld_data.columns, pd.MultiIndex):
            gld_prices = gld_data['Adj Close'].iloc[:, 0] if 'Adj Close' in gld_data.columns.levels[0] else gld_data['Close'].iloc[:, 0]
        elif 'Adj Close' in gld_data.columns:
            gld_prices = gld_data['Adj Close']
        else:
            gld_prices = gld_data['Close'] if 'Close' in gld_data.columns else None
        
        if gld_prices is not None:
            gld_prices = gld_prices.dropna()
    except:
        gld_prices = None
    
    gold_return_ts = {}
    if gld_prices is not None and len(gld_prices) > 30:
        for key, target_date in offsets.items():
            idx = gld_prices.index.get_indexer([target_date], method='nearest', tolerance=pd.Timedelta(days=5))
            if idx[0] != -1 and idx[0] >= 30:
                current_price = float(gld_prices.iloc[idx[0]])
                past_price = float(gld_prices.iloc[idx[0]-30])
                return_30d = ((current_price / past_price) - 1) * 100
                gold_return_ts[key] = round(return_30d, 2)
            else:
                gold_return_ts[key] = None
    
    # Oil (USO) - 30-day returns
    try:
        uso_data = yf.download('USO', start=start_date, end=anchor_date, progress=False, auto_adjust=False)
        if isinstance(uso_data.columns, pd.MultiIndex):
            uso_prices = uso_data['Adj Close'].iloc[:, 0] if 'Adj Close' in uso_data.columns.levels[0] else uso_data['Close'].iloc[:, 0]
        elif 'Adj Close' in uso_data.columns:
            uso_prices = uso_data['Adj Close']
        else:
            uso_prices = uso_data['Close'] if 'Close' in uso_data.columns else None
        
        if uso_prices is not None:
            uso_prices = uso_prices.dropna()
    except:
        uso_prices = None
    
    oil_return_ts = {}
    if uso_prices is not None and len(uso_prices) > 30:
        for key, target_date in offsets.items():
            idx = uso_prices.index.get_indexer([target_date], method='nearest', tolerance=pd.Timedelta(days=5))
            if idx[0] != -1 and idx[0] >= 30:
                current_price = float(uso_prices.iloc[idx[0]])
                past_price = float(uso_prices.iloc[idx[0]-30])
                return_30d = ((current_price / past_price) - 1) * 100
                oil_return_ts[key] = round(return_30d, 2)
            else:
                oil_return_ts[key] = None
    
    return {
        "international": {
            "dollar_index_30d_return": dollar_index_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "emerging_markets_rel_return_30d": em_relative_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None}
        },
        "commodities": {
            "gold_return_30d": gold_return_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None},
            "oil_return_30d": oil_return_ts or {"current": None, "1m_ago": None, "3m_ago": None, "6m_ago": None, "12m_ago": None}
        }
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


def fetch_benchmark_performance(anchor_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Fetch multi-period performance metrics for all evaluation benchmarks.

    Returns 30d, 60d, 90d, 1y returns and volatility for benchmarks:
    - SPY (US large cap)
    - QQQ (Nasdaq tech)
    - AGG (US bonds)
    - 60/40 portfolio (computed)
    - Risk Parity (simplified approximation)

    Args:
        anchor_date: Date to anchor data (default: current UTC time)

    Returns:
        Dict with structure:
        {
          "SPY": {
            "returns": {"30d": 2.28, "60d": 5.12, "90d": 8.45, "1y": 18.23},
            "volatility_annualized": {"30d": 12.42, "60d": 14.21, "90d": 15.33},
            "sharpe_ratio": {"30d": 2.24, "60d": 2.85, "90d": 3.12},
            "max_drawdown": {"30d": -2.1, "90d": -5.3}
          },
          ...
        }
    """
    if anchor_date is None:
        anchor_date = datetime.utcnow()
    
    # Fetch price data (need 1 year for 1y + extra for calculations)
    start_date = anchor_date - timedelta(days=450)

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
    
    # Helper function to calculate metrics for a given period
    def calc_period_metrics(prices, period_days):
        """Calculate returns, vol, sharpe, and drawdown for a period."""
        if len(prices) < period_days + 30:
            return None
        
        # Calculate return over period
        start_price = float(prices.iloc[-period_days])
        end_price = float(prices.iloc[-1])
        return_pct = ((end_price / start_price) - 1) * 100
        
        # Calculate annualized volatility over period
        returns = prices.pct_change().dropna()
        vol_annualized = float(returns.iloc[-period_days:].std()) * (252 ** 0.5) * 100
        
        # Calculate Sharpe ratio (assuming 0% risk-free rate)
        annualized_return = return_pct * (365 / period_days)
        sharpe = annualized_return / vol_annualized if vol_annualized > 0 else 0
        
        # Calculate max drawdown over period
        period_prices = prices.iloc[-period_days:]
        cummax = period_prices.cummax()
        drawdowns = ((period_prices - cummax) / cummax) * 100
        max_dd = float(drawdowns.min())
        
        return {
            "return": round(return_pct, 2),
            "vol": round(vol_annualized, 2),
            "sharpe": round(sharpe, 2),
            "max_dd": round(max_dd, 2)
        }
    
    # Calculate 1y start (trailing 365 calendar days)
    one_year_start = anchor_date - timedelta(days=365)
    
    # Calculate metrics for each ticker across periods
    for ticker in tickers:
        if ticker not in data.columns:
            continue

        prices = data[ticker].dropna()
        if len(prices) < 30:
            continue
        
        # Calculate for each period
        metrics_30d = calc_period_metrics(prices, 30)
        metrics_60d = calc_period_metrics(prices, 60)
        metrics_90d = calc_period_metrics(prices, 90)
        
        # 1y calculation
        one_year_metrics = None
        one_year_idx = prices.index.get_indexer([one_year_start], method='nearest', tolerance=pd.Timedelta(days=10))
        if one_year_idx[0] != -1:
            one_year_days = len(prices) - one_year_idx[0]
            if one_year_days > 0:
                one_year_metrics = calc_period_metrics(prices, one_year_days)
        
        results[ticker] = {
            "returns": {
                "30d": metrics_30d["return"] if metrics_30d else None,
                "60d": metrics_60d["return"] if metrics_60d else None,
                "90d": metrics_90d["return"] if metrics_90d else None,
                "1y": one_year_metrics["return"] if one_year_metrics else None
            },
            "volatility_annualized": {
                "30d": metrics_30d["vol"] if metrics_30d else None,
                "60d": metrics_60d["vol"] if metrics_60d else None,
                "90d": metrics_90d["vol"] if metrics_90d else None
            },
            "sharpe_ratio": {
                "30d": metrics_30d["sharpe"] if metrics_30d else None,
                "60d": metrics_60d["sharpe"] if metrics_60d else None,
                "90d": metrics_90d["sharpe"] if metrics_90d else None
            },
            "max_drawdown": {
                "30d": metrics_30d["max_dd"] if metrics_30d else None,
                "90d": metrics_90d["max_dd"] if metrics_90d else None
            }
        }

    # Calculate 60/40 portfolio (60% SPY, 40% AGG) for each period
    if 'SPY' in results and 'AGG' in results:
        periods = ['30d', '60d', '90d', '1y']
        
        returns_60_40 = {}
        vol_60_40 = {}
        sharpe_60_40 = {}
        dd_60_40 = {}
        
        for period in periods:
            spy_ret = results['SPY']['returns'].get(period)
            agg_ret = results['AGG']['returns'].get(period)
            
            if spy_ret is not None and agg_ret is not None:
                returns_60_40[period] = round(0.6 * spy_ret + 0.4 * agg_ret, 2)
            else:
                returns_60_40[period] = None
            
            if period != '1y':  # Vol only for fixed periods
                spy_vol = results['SPY']['volatility_annualized'].get(period)
                agg_vol = results['AGG']['volatility_annualized'].get(period)
                
                if spy_vol is not None and agg_vol is not None:
                    vol_60_40[period] = round(((0.6**2 * spy_vol**2 + 0.4**2 * agg_vol**2) ** 0.5), 2)
                else:
                    vol_60_40[period] = None
                
                # Sharpe
                spy_sharpe = results['SPY']['sharpe_ratio'].get(period)
                agg_sharpe = results['AGG']['sharpe_ratio'].get(period)
                if spy_sharpe is not None and agg_sharpe is not None and vol_60_40.get(period):
                    sharpe_60_40[period] = round(0.6 * spy_sharpe + 0.4 * agg_sharpe, 2)
                else:
                    sharpe_60_40[period] = None
            
            # Max drawdown only for 30d and 90d
            if period in ['30d', '90d']:
                spy_dd = results['SPY']['max_drawdown'].get(period)
                agg_dd = results['AGG']['max_drawdown'].get(period)
                
                if spy_dd is not None and agg_dd is not None:
                    dd_60_40[period] = round(0.6 * spy_dd + 0.4 * agg_dd, 2)
                else:
                    dd_60_40[period] = None

        results['60_40'] = {
            "returns": returns_60_40,
            "volatility_annualized": vol_60_40,
            "sharpe_ratio": sharpe_60_40,
            "max_drawdown": dd_60_40
        }

    # Risk Parity approximation (simplified equal-weight SPY/AGG)
    if 'SPY' in results and 'AGG' in results:
        periods = ['30d', '60d', '90d', '1y']
        
        returns_rp = {}
        vol_rp = {}
        sharpe_rp = {}
        dd_rp = {}
        
        for period in periods:
            spy_ret = results['SPY']['returns'].get(period)
            agg_ret = results['AGG']['returns'].get(period)
            
            if spy_ret is not None and agg_ret is not None:
                returns_rp[period] = round((spy_ret + agg_ret) / 2, 2)
            else:
                returns_rp[period] = None
            
            if period != '1y':
                spy_vol = results['SPY']['volatility_annualized'].get(period)
                agg_vol = results['AGG']['volatility_annualized'].get(period)
                
                if spy_vol is not None and agg_vol is not None:
                    vol_rp[period] = round((spy_vol + agg_vol) / 2, 2)
                else:
                    vol_rp[period] = None
                
                spy_sharpe = results['SPY']['sharpe_ratio'].get(period)
                agg_sharpe = results['AGG']['sharpe_ratio'].get(period)
                if spy_sharpe is not None and agg_sharpe is not None:
                    sharpe_rp[period] = round((spy_sharpe + agg_sharpe) / 2, 2)
                else:
                    sharpe_rp[period] = None
            
            if period in ['30d', '90d']:
                spy_dd = results['SPY']['max_drawdown'].get(period)
                agg_dd = results['AGG']['max_drawdown'].get(period)
                
                if spy_dd is not None and agg_dd is not None:
                    dd_rp[period] = round((spy_dd + agg_dd) / 2, 2)
                else:
                    dd_rp[period] = None

        results['risk_parity'] = {
            "returns": returns_rp,
            "volatility_annualized": vol_rp,
            "sharpe_ratio": sharpe_rp,
            "max_drawdown": dd_rp,
            "note": "Simplified approximation (equal-weight SPY/AGG)"
        }

    return results


def fetch_intra_sector_divergence(
    sector_tickers: List[str],
    anchor_date: Optional[datetime] = None,
    top_n: int = 2
) -> Dict[str, Any]:
    """
    Fetch intra-sector stock divergence for given sector ETFs.

    Calculates 30-day returns for top holdings within each sector and
    identifies top performers and underperformers to seed stock-level thinking.

    Args:
        sector_tickers: List of sector ETF tickers (e.g., ['XLF', 'XLB', 'XLC'])
        anchor_date: Date to anchor data (default: current UTC time)
        top_n: Number of top/bottom performers to return per sector (default: 2)

    Returns:
        Dict with structure:
        {
            "XLF": {
                "top": [["JPM", 8.2], ["GS", 5.1]],
                "bottom": [["C", -2.1], ["WFC", -1.4]],
                "spread_pct": 10.3,
                "holdings_analyzed": 15
            },
            ...
        }
    """
    if anchor_date is None:
        anchor_date = datetime.utcnow()

    # Need 60 days of data for 30-day returns with buffer
    start_date = anchor_date - timedelta(days=60)

    results = {}

    for sector in sector_tickers:
        if sector not in SECTOR_TOP_HOLDINGS:
            continue

        holdings = SECTOR_TOP_HOLDINGS[sector]

        # Fetch price data for all holdings in one batch
        try:
            raw_data = yf.download(
                holdings,
                start=start_date,
                end=anchor_date,
                progress=False,
                auto_adjust=False
            )

            # Extract Adj Close prices
            if len(holdings) == 1:
                # Single ticker case
                if 'Adj Close' in raw_data.columns:
                    data = pd.DataFrame({holdings[0]: raw_data['Adj Close']})
                else:
                    continue
            else:
                # Multi-ticker case
                if 'Adj Close' in raw_data.columns.names or (
                    hasattr(raw_data.columns, 'levels') and
                    'Adj Close' in raw_data.columns.levels[0]
                ):
                    data = raw_data['Adj Close']
                elif 'Adj Close' in raw_data.columns:
                    data = raw_data[['Adj Close']]
                else:
                    continue

            # Calculate 30-day returns for each stock
            stock_returns = {}
            for ticker in holdings:
                if ticker not in data.columns:
                    continue

                prices = data[ticker].dropna()
                if len(prices) < 30:
                    continue

                # Calculate 30-day return
                current_price = float(prices.iloc[-1])
                past_price = float(prices.iloc[-30])
                return_30d = ((current_price / past_price) - 1) * 100
                stock_returns[ticker] = round(return_30d, 2)

            if len(stock_returns) < 3:
                # Need at least 3 stocks for meaningful analysis
                continue

            # Sort by return
            sorted_returns = sorted(
                stock_returns.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Extract top and bottom performers
            top_performers = sorted_returns[:top_n]
            bottom_performers = sorted_returns[-top_n:]

            # Calculate spread (difference between best and worst)
            spread = top_performers[0][1] - bottom_performers[-1][1]

            results[sector] = {
                "top": [[ticker, ret] for ticker, ret in top_performers],
                "bottom": [[ticker, ret] for ticker, ret in bottom_performers],
                "spread_pct": round(spread, 2),
                "holdings_analyzed": len(stock_returns)
            }

        except Exception as e:
            print(f"Warning: Failed to fetch intra-sector data for {sector}: {e}")
            continue

    return results
