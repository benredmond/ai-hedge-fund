"""Market context pack assembler."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from src.market_context.fetchers import (
    fetch_regime_snapshot,
    fetch_macro_indicators,
    fetch_recent_events,
    fetch_benchmark_performance,
    fetch_international_and_commodities
)


def assemble_market_context_pack(fred_api_key: str, anchor_date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Assemble complete market context pack from all data sources.

    Args:
        fred_api_key: FRED API key
        anchor_date: Date to anchor data (default: current UTC time)

    Combines:
    - Regime snapshot (market state with historical time series)
    - Macro indicators (economic data with historical time series)
    - Recent events (human-curated)
    - Benchmark performance

    Returns structured context pack with metadata and regime tags.
    """
    if anchor_date is None:
        anchor_date = datetime.utcnow()

    # Fetch all data sources
    regime = fetch_regime_snapshot(anchor_date=anchor_date)
    macro = fetch_macro_indicators(fred_api_key=fred_api_key, anchor_date=anchor_date)
    international_commodities = fetch_international_and_commodities(anchor_date=anchor_date)
    events = fetch_recent_events(lookback_days=30)
    benchmarks = fetch_benchmark_performance(anchor_date=anchor_date)
    
    # Merge international and commodities into macro indicators
    macro.update(international_commodities)

    # Generate regime tags for longitudinal analysis
    regime_tags = classify_regime(regime, macro)

    # Assemble context pack
    context_pack = {
        "metadata": {
            "anchor_date": anchor_date.isoformat(),
            "data_cutoff": anchor_date.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "version": "v2.0.0"
        },
        "regime_snapshot": regime,
        "macro_indicators": macro,
        "benchmark_performance": benchmarks,
        "recent_events": events,
        "regime_tags": regime_tags
    }

    return context_pack


def classify_regime(regime: Dict[str, Any], macro: Dict[str, Any]) -> List[str]:
    """
    Generate regime classification tags for longitudinal analysis.

    Tags enable "compare within regime" analysis across cohorts.
    """
    tags = []

    # Trend classification
    trend = regime.get("trend", {}).get("regime", "unknown")
    tags.append(trend)

    # Volatility classification
    vol_regime = regime.get("volatility", {}).get("regime", "unknown")
    tags.append(f"volatility_{vol_regime}")

    # Factor regime
    factor = regime.get("factor_regime", {})
    value_growth = factor.get("value_vs_growth", {}).get("regime", "neutral")
    if value_growth != "neutral":
        tags.append(value_growth)

    # Monetary policy stance (simplified)
    fed_funds_data = macro.get("interest_rates", {}).get("fed_funds_rate", 0)
    # Handle time series (v2.0) or single value (v1.0)
    if isinstance(fed_funds_data, dict):
        fed_funds = fed_funds_data.get("current", 0)
    else:
        fed_funds = fed_funds_data
    
    if fed_funds and fed_funds > 4.5:
        tags.append("tight_monetary_policy")
    elif fed_funds and fed_funds < 2.0:
        tags.append("loose_monetary_policy")

    # Yield curve
    yield_curve_data = macro.get("interest_rates", {}).get("yield_curve_2s10s", 0)
    # Handle time series (v2.0) or single value (v1.0)
    if isinstance(yield_curve_data, dict):
        yield_curve = yield_curve_data.get("current", 0)
    else:
        yield_curve = yield_curve_data
    
    if yield_curve and yield_curve < -0.1:
        tags.append("inverted_yield_curve")

    return tags
