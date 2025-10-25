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


class TestBacktestAllCandidates:
    """Tests for backtest_all_candidates() function"""

    @pytest.mark.asyncio
    async def test_returns_five_backtest_results(self):
        """backtest_all_candidates() should return exactly 5 BacktestResult objects"""
        from src.agent.workflow import backtest_all_candidates
        from src.agent.models import BacktestResult

        # Arrange
        candidates = [
            Strategy(
                name=f"Strategy {i+1}",
                assets=['SPY', 'QQQ'],
                weights={'SPY': 0.6, 'QQQ': 0.4},
                rebalance_frequency='monthly'
            )
            for i in range(5)
        ]

        # Act
        results = await backtest_all_candidates(candidates)

        # Assert
        assert len(results) == 5, f"Expected 5 backtest results, got {len(results)}"
        assert all(isinstance(r, BacktestResult) for r in results), "All results should be BacktestResult objects"

    @pytest.mark.asyncio
    async def test_backtest_results_have_valid_metrics(self):
        """Backtest results should have valid Sharpe, drawdown, return, and volatility"""
        from src.agent.workflow import backtest_all_candidates

        # Arrange
        candidates = [
            Strategy(
                name=f"Strategy {i+1}",
                assets=['SPY', 'AGG'],
                weights={'SPY': 0.6, 'AGG': 0.4},
                rebalance_frequency='monthly'
            )
            for i in range(5)
        ]

        # Act
        results = await backtest_all_candidates(candidates)

        # Assert
        for result in results:
            assert hasattr(result, 'sharpe_ratio'), "Result should have sharpe_ratio"
            assert hasattr(result, 'max_drawdown'), "Result should have max_drawdown"
            assert hasattr(result, 'total_return'), "Result should have total_return"
            assert hasattr(result, 'volatility_annualized'), "Result should have volatility_annualized"
            # Check drawdown is negative or zero
            assert result.max_drawdown <= 0, "Max drawdown should be negative or zero"

    @pytest.mark.asyncio
    async def test_graceful_degradation_when_composer_unavailable(self):
        """Should return neutral backtest results if Composer fails"""
        from src.agent.workflow import backtest_all_candidates

        # Arrange
        candidates = [
            Strategy(
                name=f"Strategy {i+1}",
                assets=['SPY'],
                weights={'SPY': 1.0},
                rebalance_frequency='monthly'
            )
            for i in range(5)
        ]

        # Act - even without real Composer, should not crash
        results = await backtest_all_candidates(candidates)

        # Assert - should still return 5 results (graceful degradation)
        assert len(results) == 5, "Should return 5 results even if Composer unavailable"


class TestCreateStrategyWorkflow:
    """Tests for create_strategy_workflow() - full end-to-end orchestration"""

    @pytest.mark.asyncio
    async def test_full_workflow_execution(self):
        """create_strategy_workflow() should execute all 5 stages and return complete WorkflowResult"""
        from src.agent.workflow import create_strategy_workflow
        from src.agent.models import WorkflowResult, Strategy, Charter, EdgeScorecard, BacktestResult, SelectionReasoning

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
             patch('src.agent.stages.WinnerSelector.select') as mock_select, \
             patch('src.agent.stages.CharterGenerator.generate') as mock_charter_gen, \
             patch('src.agent.workflow.backtest_all_candidates') as mock_backtest:

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

            # Mock backtest results
            mock_backtest.return_value = [
                BacktestResult(sharpe_ratio=1.5, max_drawdown=-0.15, total_return=0.10, volatility_annualized=0.12),
                BacktestResult(sharpe_ratio=1.7, max_drawdown=-0.17, total_return=0.13, volatility_annualized=0.13),
                BacktestResult(sharpe_ratio=1.9, max_drawdown=-0.19, total_return=0.16, volatility_annualized=0.14),
                BacktestResult(sharpe_ratio=2.1, max_drawdown=-0.21, total_return=0.19, volatility_annualized=0.15),
                BacktestResult(sharpe_ratio=2.3, max_drawdown=-0.23, total_return=0.22, volatility_annualized=0.16),
            ]

            # Mock winner selection
            mock_select.return_value = (
                mock_candidates[0],
                SelectionReasoning(
                    winner_index=0,
                    why_selected="3-Month Tech Momentum in Low-VIX selected for superior risk-adjusted returns with Sharpe ratio of 1.5, significantly outperforming alternatives on both backtest metrics and edge scorecard dimensions including regime alignment.",
                    alternatives_compared=["Quality Defensive 60-40 Portfolio", "4-Asset Global Growth Allocation", "Value Factor 3-Asset Rotation", "Gold-Tilted 3-Asset Inflation Play"]
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
        assert len(result.backtests) == 5, "Should have 5 backtest results"
        assert result.strategy in result.all_candidates, "Winner should be from candidates"
        assert isinstance(result.charter, Charter), "Should have Charter"
        assert isinstance(result.selection_reasoning, SelectionReasoning), "Should have SelectionReasoning"

    @pytest.mark.asyncio
    async def test_validates_all_edge_scores_above_threshold(self):
        """Workflow should raise ValidationError if any candidate scores <3 on Edge Scorecard"""
        from src.agent.workflow import create_strategy_workflow
        from pydantic_core import ValidationError

        # Arrange - create market context
        market_context = {
            'metadata': {'anchor_date': '2025-10-23'},
            'regime_tags': [],
            'regime_snapshot': {'trend_classification': 'neutral'},
            'macro_indicators': {}
        }

        model = 'openai:gpt-4o'

        # Mock candidates that will fail Edge Scorecard (vague strategy with poor scores)
        with patch('src.agent.stages.CandidateGenerator.generate') as mock_generate:
            # Create 5 distinct strategies that will score poorly on Edge Scorecard
            mock_generate.return_value = [
                Strategy(name="Diversified Winners Portfolio", assets=['SPY'], weights={'SPY': 1.0}, rebalance_frequency='monthly'),
                Strategy(name="Balance Strategy", assets=['AGG'], weights={'AGG': 1.0}, rebalance_frequency='monthly'),
                Strategy(name="Hedge Portfolio", assets=['GLD'], weights={'GLD': 1.0}, rebalance_frequency='monthly'),
                Strategy(name="Winners Selection", assets=['QQQ'], weights={'QQQ': 1.0}, rebalance_frequency='monthly'),
                Strategy(name="Losers Avoidance", assets=['TLT'], weights={'TLT': 1.0}, rebalance_frequency='monthly'),
            ]

            # Act & Assert - should raise ValidationError due to low Edge Scorecard scores
            with pytest.raises(ValidationError, match="minimum threshold is 3"):
                await create_strategy_workflow(
                    market_context=market_context,
                    model=model
                )
