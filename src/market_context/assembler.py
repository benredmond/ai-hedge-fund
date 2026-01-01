"""Market context pack assembler."""

from datetime import datetime
from typing import Dict, Any, Optional
from src.market_context.fetchers import (
    fetch_regime_snapshot,
    fetch_macro_indicators,
    fetch_recent_events,
    fetch_benchmark_performance,
    fetch_international_and_commodities,
    fetch_intra_sector_divergence,
    SECTOR_TOP_HOLDINGS
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

    # Fetch intra-sector divergence for all sectors
    # This seeds stock-level thinking by showing top/bottom performers within sectors
    all_sector_tickers = list(SECTOR_TOP_HOLDINGS.keys())
    intra_sector = fetch_intra_sector_divergence(
        sector_tickers=all_sector_tickers,
        anchor_date=anchor_date,
        top_n=4
    )
    regime["intra_sector_divergence"] = intra_sector

    # Merge international and commodities into macro indicators
    macro.update(international_commodities)

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
        "recent_events": events
    }

    return context_pack


