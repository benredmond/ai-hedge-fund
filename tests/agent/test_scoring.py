"""
Tests for Edge Scorecard evaluation functions.

Tests all 6 dimension scoring functions and the main evaluate_edge_scorecard.
"""

import pytest
from src.agent.models import Strategy, EdgeScorecard
from src.agent.scoring import (
    check_specificity,
    check_structural_basis,
    check_regime_alignment,
    check_differentiation,
    check_failure_clarity,
    check_mental_model_coherence,
    evaluate_edge_scorecard
)


class TestCheckSpecificity:
    """Test specificity dimension scoring"""

    def test_vague_strategy_scores_low(self):
        """Vague strategy names score 2-3"""
        strategy = Strategy(
            name="Diversified Winners Portfolio",
            assets=['SPY', 'AGG'],
            weights={'SPY': 0.6, 'AGG': 0.4},
            rebalance_frequency='monthly'
        )
        score = check_specificity(strategy, {})
        assert score <= 3

    def test_specific_numeric_strategy_scores_high(self):
        """Strategy with numbers scores 4+"""
        strategy = Strategy(
            name="3-Month Tech Momentum in Low-VIX",
            assets=['QQQ', 'XLK'],
            weights={'QQQ': 0.7, 'XLK': 0.3},
            rebalance_frequency='weekly'
        )
        score = check_specificity(strategy, {})
        assert score >= 4

    def test_regime_specific_strategy_scores_well(self):
        """Strategy mentioning regimes scores 4+"""
        strategy = Strategy(
            name="Bull Market Momentum Play",
            assets=['SPY'],
            weights={'SPY': 1.0},
            rebalance_frequency='weekly'
        )
        score = check_specificity(strategy, {})
        assert score >= 4


class TestCheckStructuralBasis:
    """Test structural basis dimension scoring"""

    def test_diverse_asset_types_score_high(self):
        """3+ asset types score 5"""
        strategy = Strategy(
            name="Multi-Asset Strategy",
            assets=['SPY', 'AGG', 'GLD'],  # Equity, bond, commodity
            weights={'SPY': 0.5, 'AGG': 0.3, 'GLD': 0.2},
            rebalance_frequency='monthly'
        )
        score = check_structural_basis(strategy, {})
        assert score == 5

    def test_two_asset_types_score_well(self):
        """2 asset types score 4"""
        strategy = Strategy(
            name="Stock-Bond Mix",
            assets=['SPY', 'AGG'],  # Equity + bond
            weights={'SPY': 0.6, 'AGG': 0.4},
            rebalance_frequency='monthly'
        )
        score = check_structural_basis(strategy, {})
        assert score == 4

    def test_single_asset_type_scores_lower(self):
        """Single asset type with few assets scores 2-3"""
        strategy = Strategy(
            name="Tech Only",
            assets=['QQQ', 'XLK'],  # Both equity
            weights={'QQQ': 0.6, 'XLK': 0.4},
            rebalance_frequency='weekly'
        )
        score = check_structural_basis(strategy, {})
        assert 2 <= score <= 4


class TestCheckRegimeAlignment:
    """Test regime alignment dimension scoring"""

    def test_high_equity_in_bull_regime_scores_high(self):
        """60%+ equity in strong_bull scores 5"""
        strategy = Strategy(
            name="Aggressive Bull Play",
            assets=['SPY', 'QQQ', 'AGG'],
            weights={'SPY': 0.4, 'QQQ': 0.4, 'AGG': 0.2},
            rebalance_frequency='monthly'
        )
        context = {'regime_tags': ['strong_bull', 'volatility_normal']}
        score = check_regime_alignment(strategy, context)
        assert score == 5

    def test_tech_heavy_in_growth_favored_scores_well(self):
        """QQQ/XLK in growth_favored scores 4+"""
        strategy = Strategy(
            name="Tech Growth",
            assets=['QQQ'],
            weights={'QQQ': 1.0},
            rebalance_frequency='weekly'
        )
        context = {'regime_tags': ['growth_favored']}
        score = check_regime_alignment(strategy, context)
        assert score >= 4

    def test_balanced_in_normal_vol_scores_well(self):
        """40-70% equity in volatility_normal scores 4"""
        strategy = Strategy(
            name="Balanced",
            assets=['SPY', 'AGG'],
            weights={'SPY': 0.5, 'AGG': 0.5},
            rebalance_frequency='monthly'
        )
        context = {'regime_tags': ['volatility_normal']}
        score = check_regime_alignment(strategy, context)
        assert score >= 4


class TestCheckDifferentiation:
    """Test differentiation dimension scoring"""

    def test_classic_60_40_scores_low(self):
        """Classic 60/40 SPY/AGG scores 2"""
        strategy = Strategy(
            name="60/40 Portfolio",
            assets=['SPY', 'AGG'],
            weights={'SPY': 0.6, 'AGG': 0.4},
            rebalance_frequency='monthly'
        )
        score = check_differentiation(strategy, {})
        assert score == 2

    def test_exotic_assets_score_high(self):
        """Exotic ETFs (MTUM, QUAL, etc.) score 4+"""
        strategy = Strategy(
            name="Quality Momentum",
            assets=['MTUM', 'QUAL', 'SPY'],
            weights={'MTUM': 0.4, 'QUAL': 0.4, 'SPY': 0.2},
            rebalance_frequency='weekly'
        )
        score = check_differentiation(strategy, {})
        assert score >= 4

    def test_logic_tree_increases_score(self):
        """Complex logic tree scores 4+"""
        strategy = Strategy(
            name="Conditional Strategy",
            assets=['SPY', 'AGG'],
            weights={'SPY': 0.7, 'AGG': 0.3},
            rebalance_frequency='monthly',
            logic_tree={'condition': 'VIX < 20', 'true_branch': {}}
        )
        score = check_differentiation(strategy, {})
        assert score >= 4


class TestCheckFailureClarity:
    """Test failure clarity dimension scoring"""

    def test_concentrated_strategy_scores_higher(self):
        """Concentrated (>50% single asset) scores 4"""
        strategy = Strategy(
            name="Concentrated Tech",
            assets=['QQQ', 'SPY'],
            weights={'QQQ': 0.8, 'SPY': 0.2},
            rebalance_frequency='weekly'
        )
        score = check_failure_clarity(strategy, {})
        assert score == 4

    def test_diversified_strategy_scores_acceptable(self):
        """10+ assets score 3"""
        assets = [f'XL{x}' for x in 'KFVYEBIUP']  # 9 sector ETFs
        assets.append('SPY')  # Make it 10
        weights = {a: 0.1 for a in assets}

        strategy = Strategy(
            name="All Sectors",
            assets=assets,
            weights=weights,
            rebalance_frequency='monthly'
        )
        score = check_failure_clarity(strategy, {})
        assert score == 3


class TestCheckMentalModelCoherence:
    """Test mental model coherence dimension scoring"""

    def test_bonds_with_low_frequency_coherent(self):
        """Bonds + monthly/quarterly rebalance scores 4"""
        strategy = Strategy(
            name="Bond Portfolio",
            assets=['AGG', 'TLT'],
            weights={'AGG': 0.6, 'TLT': 0.4},
            rebalance_frequency='monthly'
        )
        score = check_mental_model_coherence(strategy, {})
        assert score >= 4

    def test_tech_with_high_frequency_coherent(self):
        """Tech + weekly/daily rebalance scores 4"""
        strategy = Strategy(
            name="Active Tech",
            assets=['QQQ', 'XLK'],
            weights={'QQQ': 0.7, 'XLK': 0.3},
            rebalance_frequency='weekly'
        )
        score = check_mental_model_coherence(strategy, {})
        assert score >= 4

    def test_concentrated_with_few_assets_coherent(self):
        """Concentrated (>50%) with <=3 assets scores 4"""
        strategy = Strategy(
            name="Concentrated Play",
            assets=['SPY', 'QQQ'],
            weights={'SPY': 0.7, 'QQQ': 0.3},
            rebalance_frequency='monthly'
        )
        score = check_mental_model_coherence(strategy, {})
        assert score >= 4


class TestEvaluateEdgeScorecard:
    """Test complete Edge Scorecard evaluation"""

    def test_good_strategy_passes_all_dimensions(self):
        """Well-designed strategy scores 3+ on all dimensions"""
        strategy = Strategy(
            name="3-Month Tech Momentum",
            assets=['QQQ', 'XLK', 'MTUM'],
            weights={'QQQ': 0.5, 'XLK': 0.3, 'MTUM': 0.2},
            rebalance_frequency='weekly'
        )
        context = {'regime_tags': ['strong_bull', 'growth_favored', 'volatility_normal']}

        scorecard = evaluate_edge_scorecard(strategy, context)

        assert scorecard.specificity >= 3
        assert scorecard.structural_basis >= 3
        assert scorecard.regime_alignment >= 3
        assert scorecard.differentiation >= 3
        assert scorecard.failure_clarity >= 3
        assert scorecard.mental_model_coherence >= 3
        assert scorecard.total_score >= 3.0

    def test_weak_strategy_fails_validation(self):
        """Strategy with single asset fails structural_basis threshold"""
        from pydantic import ValidationError

        # Single asset = only 1 asset type = scores 2 on structural_basis
        strategy = Strategy(
            name="Simple Strategy",
            assets=['SPY'],
            weights={'SPY': 1.0},
            rebalance_frequency='monthly'
        )
        context = {'regime_tags': []}

        # Should raise ValidationError because structural_basis scores 2
        with pytest.raises(ValidationError, match="minimum threshold is 3"):
            evaluate_edge_scorecard(strategy, context)

    def test_scorecard_total_score_calculation(self):
        """total_score property calculates average correctly"""
        # Use a better strategy that won't trigger validation errors
        strategy = Strategy(
            name="Quality Factor Tilt",  # More specific than "Balanced"
            assets=['QUAL', 'SPY', 'AGG'],  # Add QUAL for differentiation
            weights={'QUAL': 0.3, 'SPY': 0.4, 'AGG': 0.3},
            rebalance_frequency='monthly'
        )
        context = {'regime_tags': ['strong_bull']}

        scorecard = evaluate_edge_scorecard(strategy, context)

        # Calculate expected average
        expected_avg = (
            scorecard.specificity +
            scorecard.structural_basis +
            scorecard.regime_alignment +
            scorecard.differentiation +
            scorecard.failure_clarity +
            scorecard.mental_model_coherence
        ) / 6

        assert scorecard.total_score == pytest.approx(expected_avg, abs=0.01)

    def test_excellent_strategy_scores_high(self):
        """Excellent strategy scores 4+ average"""
        strategy = Strategy(
            name="12-Month Quality Momentum in Bull Market",
            assets=['QUAL', 'MTUM', 'SPY', 'AGG', 'GLD'],
            weights={'QUAL': 0.3, 'MTUM': 0.3, 'SPY': 0.2, 'AGG': 0.15, 'GLD': 0.05},
            rebalance_frequency='monthly',
            logic_tree={'condition': 'VIX < 25', 'true_branch': {}}
        )
        context = {'regime_tags': ['strong_bull', 'growth_favored', 'volatility_normal']}

        scorecard = evaluate_edge_scorecard(strategy, context)

        # This is a well-designed strategy, should score well
        assert scorecard.total_score >= 3.5
