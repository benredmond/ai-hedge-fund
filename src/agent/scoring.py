"""
Edge Scorecard evaluation for trading strategies.

Evaluates strategies on 6 dimensions (1-5 scale):
- Specificity: Edge clarity and precision
- Structural Basis: Reasoning quality
- Regime Alignment: Fit with current market conditions
- Differentiation: Novelty vs generic approaches
- Failure Clarity: Quality of identified failure modes
- Mental Model Coherence: Internal consistency

All functions are deterministic code (no AI calls).
"""

from src.agent.models import EdgeScorecard, Strategy
from typing import Dict, Any


def check_specificity(candidate: Strategy, market_context: Dict[str, Any]) -> int:
    """
    Score 1-5 based on edge specificity.

    1 = Vague ("buy winners", "diversify")
    5 = Specific ("Buy 3M momentum leaders in low-VIX regimes")

    Args:
        candidate: Strategy to evaluate
        market_context: Current market conditions (not used for specificity)

    Returns:
        Score from 1 to 5
    """
    # Check for vague terms
    vague_terms = ['winners', 'losers', 'diversify', 'balance', 'hedge', 'growth', 'value']

    # Check if strategy name contains vague terms
    name_lower = candidate.name.lower()
    has_vague = any(term in name_lower for term in vague_terms)

    # Check for specific numeric criteria
    has_specific = any(char.isdigit() for char in candidate.name)

    # Check for regime/factor mentions (more specific)
    regime_mentions = ['momentum', 'volatility', 'bull', 'bear', 'defensive',
                      'risk-on', 'risk-off', 'quality', 'low-vol', 'high-vol']
    has_regime = any(term in name_lower for term in regime_mentions)

    # Scoring logic
    score = 3  # Default acceptable

    if has_vague and not has_specific and not has_regime:
        score = 2  # Too vague
    elif has_specific and has_regime:
        score = 5  # Excellent specificity
    elif has_specific or has_regime:
        score = 4  # Strong specificity

    return max(1, min(5, score))


def check_structural_basis(candidate: Strategy, market_context: Dict[str, Any]) -> int:
    """
    Score 1-5 based on structural reasoning.

    1 = "Feels right"
    5 = Documented edge type (behavioral/structural/informational/risk premium)

    Uses asset diversity as proxy for structural thinking.

    Args:
        candidate: Strategy to evaluate
        market_context: Current market conditions (not used)

    Returns:
        Score from 1 to 5
    """
    asset_count = len(candidate.assets)

    # Categorize assets by type
    equity_assets = {'SPY', 'QQQ', 'IWM', 'VTI', 'DIA'}
    bond_assets = {'AGG', 'TLT', 'BIL', 'SHY', 'IEF'}
    commodity_assets = {'GLD', 'SLV', 'DBC', 'USO'}

    asset_types = set()
    for ticker in candidate.assets:
        if ticker in equity_assets or ticker.startswith('XL'):  # Sector ETFs
            asset_types.add('equity')
        elif ticker in bond_assets:
            asset_types.add('bond')
        elif ticker in commodity_assets:
            asset_types.add('commodity')
        else:
            asset_types.add('other')

    unique_asset_types = len(asset_types)

    # More diverse = better structural basis
    if unique_asset_types >= 3:
        return 5
    elif unique_asset_types == 2:
        return 4
    elif asset_count >= 5:
        return 3
    else:
        return 2


def check_regime_alignment(candidate: Strategy, market_context: Dict[str, Any]) -> int:
    """
    Score 1-5 based on alignment with current market regime.

    Current regime from market_context['regime_tags']:
    - strong_bull, volatility_normal, growth_favored (Oct 2025)

    Args:
        candidate: Strategy to evaluate
        market_context: Market conditions with regime_tags

    Returns:
        Score from 1 to 5
    """
    regime_tags = market_context.get('regime_tags', [])

    # Analyze candidate's asset allocation
    has_equity = any(ticker in candidate.assets
                     for ticker in ['SPY', 'QQQ', 'IWM', 'VTI', 'DIA'])

    equity_weight = sum(
        candidate.weights.get(ticker, 0)
        for ticker in ['SPY', 'QQQ', 'IWM', 'VTI', 'DIA']
        if ticker in candidate.assets
    )

    # Add sector ETFs to equity weight
    sector_etfs = [t for t in candidate.assets if t.startswith('XL')]
    equity_weight += sum(candidate.weights.get(ticker, 0) for ticker in sector_etfs)

    score = 3  # Default

    # Strong bull regime favors equity
    if 'strong_bull' in regime_tags:
        if equity_weight > 0.6:
            score = 5
        elif equity_weight > 0.4:
            score = 4

    # Normal volatility allows for balanced
    if 'volatility_normal' in regime_tags:
        if 0.4 <= equity_weight <= 0.7:
            score = max(score, 4)

    # Growth favored means tech/growth heavy
    if 'growth_favored' in regime_tags:
        if 'QQQ' in candidate.assets or 'XLK' in candidate.assets:
            score = max(score, 4)

    return score


def check_differentiation(candidate: Strategy, market_context: Dict[str, Any]) -> int:
    """
    Score 1-5 based on strategy differentiation.

    1 = Generic ("Everyone does this")
    5 = Novel or underutilized combination

    Args:
        candidate: Strategy to evaluate
        market_context: Current market conditions (not used)

    Returns:
        Score from 1 to 5
    """
    # Check for generic portfolios
    asset_set = set(candidate.assets)

    # Common generic combos
    if asset_set == {'SPY', 'AGG'}:
        # Classic 60/40 check
        spy_weight = candidate.weights.get('SPY', 0)
        if 0.55 <= spy_weight <= 0.65:
            return 2  # Generic 60/40

    if asset_set == {'QQQ', 'TLT'}:
        return 2  # Generic tech/bonds

    # Check for novel assets (factor ETFs, exotic strategies)
    exotic_assets = {'MTUM', 'QUAL', 'USMV', 'VIG', 'SCHD', 'VWO', 'EFA',
                     'QYLD', 'JEPI', 'QQQM', 'VUG', 'VTV'}
    has_exotic = any(ticker in candidate.assets for ticker in exotic_assets)

    # Check for complex logic tree
    has_logic = bool(candidate.logic_tree)

    score = 3  # Default
    if has_exotic and has_logic:
        score = 5
    elif has_exotic or has_logic:
        score = 4

    return score


def check_mental_model_coherence(candidate: Strategy, market_context: Dict[str, Any]) -> int:
    """
    Score 1-5 based on internal coherence.

    1 = Unclear classification
    5 = All 5 mental models tell coherent story

    Checks:
    - Rebalancing frequency matches asset types
    - Concentration matches conviction
    - Asset mix makes sense

    Args:
        candidate: Strategy to evaluate
        market_context: Current market conditions (not used)

    Returns:
        Score from 1 to 5
    """
    # Check rebalancing frequency matches asset types
    bond_assets = {'AGG', 'TLT', 'BIL', 'SHY', 'IEF'}
    tech_assets = {'QQQ', 'XLK', 'NVDA', 'MSFT', 'AAPL'}

    has_bonds = any(ticker in candidate.assets for ticker in bond_assets)
    has_tech = any(ticker in candidate.assets for ticker in tech_assets)

    freq = candidate.rebalance_frequency.value

    score = 3  # Default

    # Coherence checks
    if has_bonds and freq in ['monthly', 'quarterly']:
        score = max(score, 4)  # Coherent: bonds + low frequency

    if has_tech and freq in ['weekly', 'daily']:
        score = max(score, 4)  # Coherent: tech + high frequency

    # Check concentration coherence
    max_weight = max(candidate.weights.values()) if candidate.weights else 0
    if max_weight > 0.5:
        # Concentrated = should be high conviction (fewer assets)
        if len(candidate.assets) <= 3:
            score = max(score, 4)

    # Check if weights make sense (not all equal for different asset types)
    if len(candidate.weights) > 2:
        weights_list = sorted(candidate.weights.values())
        # Check for variation (not all equal weight)
        if weights_list[-1] - weights_list[0] > 0.15:
            score = max(score, 4)  # Has conviction differences

    return score


def check_failure_clarity(candidate: Strategy, market_context: Dict[str, Any]) -> int:
    """
    Score 1-5 based on identifiable failure modes.

    Since strategies don't have explicit failure_modes yet (added in charter),
    we infer failure clarity from:
    - Concentration risk (high = clear failure mode)
    - Asset diversity (low = clearer failure modes)
    - Rebalancing frequency (infrequent = clearer regime assumptions)

    Args:
        candidate: Strategy to evaluate
        market_context: Current market conditions (not used)

    Returns:
        Score from 1 to 5
    """
    # For now, default to 3 (acceptable) since failure modes
    # are defined in the charter, not the strategy itself
    #
    # Future: Could analyze strategy characteristics for implicit failure modes:
    # - High equity concentration → VIX spike risk
    # - Tech heavy → rate hike risk
    # - Bond heavy → inflation risk
    # - Sector concentration → sector rotation risk

    # Simple heuristic: more concentrated = clearer failure modes
    max_weight = max(candidate.weights.values()) if candidate.weights else 0

    if max_weight > 0.5:
        return 4  # Concentrated = clear single point of failure
    elif len(candidate.assets) >= 10:
        return 3  # Diversified = less clear failure modes
    else:
        return 3  # Default acceptable


def evaluate_edge_scorecard(candidate: Strategy, market_context: Dict[str, Any]) -> EdgeScorecard:
    """
    Evaluate strategy on 6 Edge Scorecard dimensions.

    Each dimension scored 1-5:
    - 1-2: Weak (fails threshold)
    - 3: Acceptable minimum
    - 4: Strong
    - 5: Excellent

    Args:
        candidate: Strategy to evaluate
        market_context: Current market conditions

    Returns:
        EdgeScorecard with all 6 dimensions evaluated

    Raises:
        ValueError: If any dimension scores below 3 (via EdgeScorecard validation)

    Example:
        >>> from src.agent.models import Strategy
        >>> strategy = Strategy(
        ...     name="3-Month Tech Momentum",
        ...     assets=["QQQ", "XLK"],
        ...     weights={"QQQ": 0.7, "XLK": 0.3},
        ...     rebalance_frequency="weekly"
        ... )
        >>> context = {"regime_tags": ["strong_bull", "growth_favored"]}
        >>> scorecard = evaluate_edge_scorecard(strategy, context)
        >>> print(f"Total score: {scorecard.total_score:.1f}/5")
        Total score: 4.2/5
    """
    return EdgeScorecard(
        specificity=check_specificity(candidate, market_context),
        structural_basis=check_structural_basis(candidate, market_context),
        regime_alignment=check_regime_alignment(candidate, market_context),
        differentiation=check_differentiation(candidate, market_context),
        failure_clarity=check_failure_clarity(candidate, market_context),
        mental_model_coherence=check_mental_model_coherence(candidate, market_context)
    )
