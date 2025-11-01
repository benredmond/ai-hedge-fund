"""
Tests for workflow.py - Strategy creation workflow orchestration.

Following TDD approach:
- Write test first (RED)
- Watch it fail
- Implement minimal code (GREEN)
- Verify passes
- Refactor if needed
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.agent.models import Strategy


class TestCreateStrategyWorkflow:
    """Tests for create_strategy_workflow() - full end-to-end orchestration"""

    @pytest.mark.asyncio
    async def test_full_workflow_execution(self):
        """create_strategy_workflow() should execute all 4 stages and return complete WorkflowResult"""
        from src.agent.workflow import create_strategy_workflow
        from src.agent.models import WorkflowResult, Strategy, Charter, EdgeScorecard, SelectionReasoning

        # Arrange
        market_context = {
            'metadata': {'anchor_date': '2025-10-23'},
            'regime_tags': ['strong_bull', 'volatility_normal', 'growth_favored'],
            'regime_snapshot': {
                'trend_classification': 'bull',
                'volatility_regime': 'normal',
                'market_breadth': 0.75,
                'sector_leadership': {'leaders': ['Technology', 'Communication Services', 'Consumer Discretionary']},
                'sector_dispersion': 0.15,
                'factor_regime': {'value_vs_growth': -0.05, 'momentum': 0.12}
            },
            'macro_indicators': {
                'fed_funds_rate': 5.25,
                'unemployment_rate': 3.8,
                'inflation_yoy': 3.2
            }
        }

        model = 'openai:gpt-4o'

        # Mock all stage class methods
        with patch('src.agent.stages.CandidateGenerator.generate') as mock_generate, \
             patch('src.agent.stages.EdgeScorer.score') as mock_edge_score, \
             patch('src.agent.stages.WinnerSelector.select') as mock_select, \
             patch('src.agent.stages.CharterGenerator.generate') as mock_charter_gen:

            # Mock candidate generation
            mock_candidates = [
                Strategy(
                    name="3-Month Tech Momentum in Low-VIX",
                    assets=['SPY', 'QQQ', 'AGG'],
                    weights={'SPY': 0.5, 'QQQ': 0.3, 'AGG': 0.2},
                    rebalance_frequency='monthly',
                    failure_modes=["VIX spike above 30", "Tech underperformance", "Rate spike"]
                ),
                Strategy(
                    name="Quality Defensive 60-40 Portfolio",
                    assets=['SPY', 'AGG', 'GLD'],
                    weights={'SPY': 0.4, 'AGG': 0.4, 'GLD': 0.2},
                    rebalance_frequency='monthly',
                    failure_modes=["Rising rates compress bonds", "Inflation spike", "Flight to risk"]
                ),
                Strategy(
                    name="4-Asset Global Growth Allocation",
                    assets=['SPY', 'IWM', 'AGG', 'GLD'],
                    weights={'SPY': 0.4, 'IWM': 0.2, 'AGG': 0.3, 'GLD': 0.1},
                    rebalance_frequency='monthly',
                    failure_modes=["International underperformance", "Dollar strength", "Risk-off environment"]
                ),
                Strategy(
                    name="Value Factor 3-Asset Rotation",
                    assets=['SPY', 'QQQ', 'TLT'],
                    weights={'SPY': 0.5, 'QQQ': 0.3, 'TLT': 0.2},
                    rebalance_frequency='monthly',
                    failure_modes=["Growth outperforms value", "Quality premium reversal", "Small cap weakness"]
                ),
                Strategy(
                    name="Gold-Tilted 3-Asset Inflation Play",
                    assets=['GLD', 'TLT', 'IWM'],
                    weights={'GLD': 0.5, 'TLT': 0.3, 'IWM': 0.2},
                    rebalance_frequency='monthly',
                    failure_modes=["Deflation scenario", "Dollar strength", "Commodity collapse"]
                ),
            ]
            mock_generate.return_value = mock_candidates

            # Mock edge scoring
            mock_edge_score.return_value = EdgeScorecard(
                thesis_quality=4,
                edge_economics=4,
                risk_framework=3,
                regime_awareness=4,
                strategic_coherence=4
            )

            # Mock winner selection
            mock_select.return_value = (
                mock_candidates[0],
                SelectionReasoning(
                    winner_index=0,
                    why_selected="3-Month Tech Momentum in Low-VIX selected for superior composite score based on Edge Scorecard dimensions including thesis quality, edge economics, risk framework, regime awareness and strategic coherence, significantly outperforming alternatives across all evaluated criteria.",
                    tradeoffs_accepted="Accepting higher volatility for better expected returns under current market regime.",
                    alternatives_rejected=["Quality Defensive 60-40 Portfolio", "4-Asset Global Growth Allocation", "Value Factor 3-Asset Rotation", "Gold-Tilted 3-Asset Inflation Play"],
                    conviction_level=0.85
                )
            )

            # Mock charter generation
            mock_charter_gen.return_value = Charter(
                market_thesis="Bull market with normal volatility supports growth-oriented strategies.",
                strategy_selection="3-Month Tech Momentum in Low-VIX chosen for Sharpe ratio outperformance.",
                expected_behavior="Expect continued outperformance during bull market continuation.",
                failure_modes=["Volatility spike triggers defensive rotation", "Growth underperforms value", "Rising rates compress valuations"],
                outlook_90d="Maintain current positioning given favorable regime."
            )

            # Act
            result = await create_strategy_workflow(
                market_context=market_context,
                model=model
            )

        # Assert - verify WorkflowResult structure
        assert isinstance(result, WorkflowResult), "Should return WorkflowResult object"
        assert len(result.all_candidates) == 5, "Should have 5 candidates"
        assert len(result.scorecards) == 5, "Should have 5 scorecards"
        assert result.strategy in result.all_candidates, "Winner should be from candidates"
        assert isinstance(result.charter, Charter), "Should have Charter"
        assert isinstance(result.selection_reasoning, SelectionReasoning), "Should have SelectionReasoning"

    @pytest.mark.asyncio
    async def test_edge_scorecard_validation_enforced(self):
        """EdgeScorecard model enforces ≥3 minimum per dimension"""
        from src.agent.models import EdgeScorecard
        from pydantic_core import ValidationError

        # EdgeScorecard should reject scores below 3
        with pytest.raises(ValidationError):
            EdgeScorecard(
                thesis_quality=2,  # Below threshold - should fail
                edge_economics=3,
                risk_framework=3,
                regime_awareness=3,
                strategic_coherence=3
            )

        # Valid scorecard with all dimensions ≥3 should pass
        scorecard = EdgeScorecard(
            thesis_quality=3,
            edge_economics=3,
            risk_framework=3,
            regime_awareness=3,
            strategic_coherence=3
        )
        assert scorecard.total_score == 3.0
