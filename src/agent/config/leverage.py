"""Leveraged ETF configuration and utilities.

This module centralizes leverage-related constants to prevent duplication
across candidate_generator and edge_scorer modules.

Historical Drawdown Sources:
- 2x bounds: 2020 COVID (SSO -68% vs SPY -34%), 2022 rate shock (SSO -40%)
- 3x bounds: 2020 COVID (TQQQ -75%), 2022 rate shock (TQQQ -80%)
"""

from typing import List, Tuple
from src.agent.models import Strategy


# Approved leveraged ETFs - liquid, well-established instruments only
LEVERAGED_ETF_WHITELIST = {
    # 2x Leveraged (Moderate Risk)
    "2x": [
        "SSO",   # 2x S&P 500
        "QLD",   # 2x Nasdaq 100
        "UGL",   # 2x Gold
        "URE",   # 2x Real Estate
        "ROM",   # 2x Technology
        "UYG",   # 2x Financials
        "UST",   # 2x 7-10Y Treasuries
        "UBT",   # 2x 20Y+ Treasuries
    ],
    # 3x Leveraged (High Risk)
    "3x": [
        "UPRO",  # 3x S&P 500
        "TQQQ",  # 3x Nasdaq 100
        "SPXL",  # 3x S&P 500 (alternate)
        "SOXL",  # 3x Semiconductors
        "FAS",   # 3x Financials
        "TECL",  # 3x Technology
        "TMF",   # 3x 20Y+ Treasuries
        "SPXS",  # 3x Inverse S&P (short)
        "SQQQ",  # 3x Inverse Nasdaq (short)
        "TZA",   # 3x Inverse Russell 2000 (short)
    ]
}

# Flatten for quick lookup
APPROVED_2X_ETFS = set(LEVERAGED_ETF_WHITELIST["2x"])
APPROVED_3X_ETFS = set(LEVERAGED_ETF_WHITELIST["3x"])
ALL_LEVERAGED_ETFS = APPROVED_2X_ETFS | APPROVED_3X_ETFS


# Historical worst-case drawdowns (source: 2022 rate shock, 2020 COVID)
DRAWDOWN_BOUNDS_2X = {
    "min": 18,  # Conservative minimum for 2x (based on 2020 SSO -34% → rounded to -18% for tolerance)
    "max": 40,  # SSO 2022 rate shock maximum observed (-40%)
}

DRAWDOWN_BOUNDS_3X = {
    "min": 40,  # Conservative minimum (2022 TQQQ -80%, using 50% threshold)
    "max": 65,  # Realistic pessimistic (2022 TQQQ -80%, 2020 -75% → 65% conservative)
}

# Annual decay costs in sideways markets
DECAY_COST_2X = (0.5, 1.0)  # Annual percentage range
DECAY_COST_3X = (2.0, 5.0)  # Annual percentage range


def detect_leverage(strategy: Strategy) -> Tuple[List[str], List[str], int]:
    """
    Detect leveraged assets in a strategy and determine max leverage level.

    Args:
        strategy: Strategy to analyze

    Returns:
        Tuple of (leveraged_2x_assets, leveraged_3x_assets, max_leverage_level)

    Examples:
        >>> strategy = Strategy(assets=["SPY", "TQQQ"], ...)
        >>> detect_leverage(strategy)
        ([], ["TQQQ"], 3)

        >>> strategy = Strategy(assets=["SSO", "AGG"], ...)
        >>> detect_leverage(strategy)
        (["SSO"], [], 2)

        >>> strategy = Strategy(assets=["SPY", "QQQ"], ...)
        >>> detect_leverage(strategy)
        ([], [], 1)
    """
    leveraged_2x = [asset for asset in strategy.assets if asset in APPROVED_2X_ETFS]
    leveraged_3x = [asset for asset in strategy.assets if asset in APPROVED_3X_ETFS]
    max_leverage = 3 if leveraged_3x else (2 if leveraged_2x else 1)

    return leveraged_2x, leveraged_3x, max_leverage


def get_drawdown_bounds(max_leverage: int) -> Tuple[int, int]:
    """
    Get realistic drawdown bounds for leverage level.

    Args:
        max_leverage: Leverage level (1, 2, or 3)

    Returns:
        Tuple of (min_realistic_dd, max_realistic_dd)

    Examples:
        >>> get_drawdown_bounds(3)
        (40, 65)

        >>> get_drawdown_bounds(2)
        (18, 40)
    """
    if max_leverage == 3:
        bounds = DRAWDOWN_BOUNDS_3X
    elif max_leverage == 2:
        bounds = DRAWDOWN_BOUNDS_2X
    else:
        # No specific bounds for unleveraged (not used in validation)
        return (0, 100)

    return bounds["min"], bounds["max"]


def get_decay_cost_range(max_leverage: int) -> Tuple[float, float]:
    """
    Get expected decay cost range for leverage level.

    Args:
        max_leverage: Leverage level (1, 2, or 3)

    Returns:
        Tuple of (min_decay_pct, max_decay_pct)

    Examples:
        >>> get_decay_cost_range(3)
        (2.0, 5.0)

        >>> get_decay_cost_range(2)
        (0.5, 1.0)
    """
    if max_leverage == 3:
        return DECAY_COST_3X
    elif max_leverage == 2:
        return DECAY_COST_2X
    else:
        return (0.0, 0.0)  # No decay for unleveraged
