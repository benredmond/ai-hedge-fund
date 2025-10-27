"""
Tests for Edge Scorecard evaluation using EdgeScorer agent.
"""

import pytest
from src.agent.models import Strategy, EdgeScorecard
from src.agent.stages.edge_scorer import EdgeScorer


@pytest.mark.integration
class TestEdgeScorer:
    """Test EdgeScorer agent for AI-based strategy evaluation"""

    @pytest.mark.asyncio
    async def test_scores_good_strategy_with_agent(self):
        """EdgeScorer agent successfully scores a well-designed strategy"""
        scorer = EdgeScorer()

        strategy = Strategy(
            name="3-Month Tech Momentum",
            assets=['QQQ', 'XLK', 'MTUM'],
            weights={'QQQ': 0.5, 'XLK': 0.3, 'MTUM': 0.2},
            rebalance_frequency='weekly'
        )
        context = {
            'regime_tags': ['strong_bull', 'growth_favored', 'volatility_normal'],
            'regime_snapshot': {
                'trend_classification': 'bull',
                'volatility_regime': 'normal',
                'market_breadth_pct': 75.0
            }
        }

        scorecard = await scorer.score(strategy, context)

        # Verify structure
        assert isinstance(scorecard, EdgeScorecard)
        assert scorecard.specificity >= 3
        assert scorecard.structural_basis >= 3
        assert scorecard.regime_alignment >= 3
        assert scorecard.differentiation >= 3
        assert scorecard.failure_clarity >= 3
        assert scorecard.mental_model_coherence >= 3
        assert scorecard.total_score >= 3.0

    @pytest.mark.asyncio
    async def test_scores_generic_60_40_correctly(self):
        """EdgeScorer agent identifies generic 60/40 portfolio"""
        scorer = EdgeScorer()

        strategy = Strategy(
            name="60/40 Portfolio",
            assets=['SPY', 'AGG'],
            weights={'SPY': 0.6, 'AGG': 0.4},
            rebalance_frequency='monthly'
        )
        context = {
            'regime_tags': ['strong_bull'],
            'regime_snapshot': {
                'trend_classification': 'bull',
                'volatility_regime': 'normal',
                'market_breadth_pct': 70.0
            }
        }

        scorecard = await scorer.score(strategy, context)

        # Generic strategy should pass but not score high
        assert scorecard.total_score >= 3.0
        assert scorecard.total_score < 4.5  # Shouldn't be excellent
        # Differentiation should be low for generic 60/40
        assert scorecard.differentiation <= 3

    @pytest.mark.asyncio
    async def test_handles_complex_strategy(self):
        """EdgeScorer agent handles strategy with logic tree"""
        scorer = EdgeScorer()

        strategy = Strategy(
            name="VIX-Based Adaptive Strategy",
            assets=['QQQ', 'AGG', 'GLD'],
            weights={'QQQ': 0.5, 'AGG': 0.3, 'GLD': 0.2},
            rebalance_frequency='weekly',
            logic_tree={'condition': 'VIX < 20', 'true_branch': {}}
        )
        context = {
            'regime_tags': ['growth_favored', 'volatility_normal'],
            'regime_snapshot': {
                'trend_classification': 'bull',
                'volatility_regime': 'normal',
                'market_breadth_pct': 65.0
            }
        }

        scorecard = await scorer.score(strategy, context)

        # Strategy with logic tree should pass all thresholds
        # AI agents may score conservatively, so we verify minimum standards
        assert scorecard.total_score >= 3.0
        assert all([
            scorecard.specificity >= 3,
            scorecard.structural_basis >= 3,
            scorecard.regime_alignment >= 3,
            scorecard.differentiation >= 3,
            scorecard.failure_clarity >= 3,
            scorecard.mental_model_coherence >= 3
        ])
