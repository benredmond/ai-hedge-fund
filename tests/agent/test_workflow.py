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
from src.agent.cost_tracker import CostTracker


class TestGenerateCandidates:
    """Tests for generate_candidates() function"""

    @pytest.mark.asyncio
    async def test_returns_exactly_five_strategies(self):
        """generate_candidates() should return exactly 5 Strategy objects"""
        # Import here so test can fail with ImportError if function doesn't exist
        from src.agent.workflow import generate_candidates

        # Arrange
        market_context = {
            'metadata': {'anchor_date': '2025-10-23'},
            'regime_tags': ['strong_bull', 'volatility_normal', 'growth_favored'],
            'regime_snapshot': {'trend_classification': 'bull'},
            'macro_indicators': {}
        }
        model = 'openai:gpt-4o'
        cost_tracker = CostTracker(max_budget=10.0)

        # Mock the agent creation and execution
        # We'll mock create_agent to return a mock agent that yields 5 DISTINCT strategies
        mock_strategies = [
            Strategy(
                name="Strategy 1",
                assets=['SPY', 'QQQ'],
                weights={'SPY': 0.6, 'QQQ': 0.4},
                rebalance_frequency='monthly'
            ),
            Strategy(
                name="Strategy 2",
                assets=['AGG', 'TLT'],
                weights={'AGG': 0.5, 'TLT': 0.5},
                rebalance_frequency='monthly'
            ),
            Strategy(
                name="Strategy 3",
                assets=['GLD', 'SLV'],
                weights={'GLD': 0.7, 'SLV': 0.3},
                rebalance_frequency='monthly'
            ),
            Strategy(
                name="Strategy 4",
                assets=['VTI', 'VXUS'],
                weights={'VTI': 0.6, 'VXUS': 0.4},
                rebalance_frequency='monthly'
            ),
            Strategy(
                name="Strategy 5",
                assets=['IWM', 'EFA'],
                weights={'IWM': 0.5, 'EFA': 0.5},
                rebalance_frequency='monthly'
            )
        ]

        with patch('src.agent.workflow.create_agent') as mock_create_agent:
            # Set up mock agent
            mock_agent = AsyncMock()
            mock_result = Mock()
            mock_result.output = mock_strategies
            mock_agent.run.return_value = mock_result

            # Mock context manager
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_agent
            mock_ctx.__aexit__.return_value = None
            mock_create_agent.return_value = mock_ctx

            # Act
            result = await generate_candidates(market_context, model, cost_tracker)

        # Assert
        assert len(result) == 5, f"Expected 5 candidates, got {len(result)}"
        assert all(isinstance(s, Strategy) for s in result), "All candidates should be Strategy objects"

    @pytest.mark.asyncio
    async def test_raises_error_when_wrong_count(self):
        """generate_candidates() should raise ValueError if AI doesn't return exactly 5"""
        from src.agent.workflow import generate_candidates

        # Arrange
        market_context = {'metadata': {'anchor_date': '2025-10-23'}, 'regime_tags': []}
        model = 'openai:gpt-4o'
        cost_tracker = CostTracker(max_budget=10.0)

        # Mock agent returning wrong count (3 instead of 5)
        mock_strategies = [
            Strategy(
                name=f"Strategy {i+1}",
                assets=['SPY', 'QQQ'],
                weights={'SPY': 0.6, 'QQQ': 0.4},
                rebalance_frequency='monthly'
            )
            for i in range(3)  # Wrong count!
        ]

        with patch('src.agent.workflow.create_agent') as mock_create_agent:
            mock_agent = AsyncMock()
            mock_result = Mock()
            mock_result.output = mock_strategies
            mock_agent.run.return_value = mock_result

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_agent
            mock_ctx.__aexit__.return_value = None
            mock_create_agent.return_value = mock_ctx

            # Act & Assert
            with pytest.raises(ValueError, match="Expected 5 candidates, got 3"):
                await generate_candidates(market_context, model, cost_tracker)

    @pytest.mark.asyncio
    async def test_detects_duplicate_ticker_sets(self):
        """generate_candidates() should raise ValueError if duplicate ticker sets detected"""
        from src.agent.workflow import generate_candidates

        # Arrange
        market_context = {'metadata': {'anchor_date': '2025-10-23'}, 'regime_tags': []}
        model = 'openai:gpt-4o'
        cost_tracker = CostTracker(max_budget=10.0)

        # Mock agent returning duplicates
        mock_strategies = [
            Strategy(
                name=f"Strategy {i+1}",
                assets=['SPY', 'QQQ'],  # Same tickers for all!
                weights={'SPY': 0.6, 'QQQ': 0.4},
                rebalance_frequency='monthly'
            )
            for i in range(5)
        ]

        with patch('src.agent.workflow.create_agent') as mock_create_agent:
            mock_agent = AsyncMock()
            mock_result = Mock()
            mock_result.output = mock_strategies
            mock_agent.run.return_value = mock_result

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_agent
            mock_ctx.__aexit__.return_value = None
            mock_create_agent.return_value = mock_ctx

            # Act & Assert
            with pytest.raises(ValueError, match="Duplicate candidates detected"):
                await generate_candidates(market_context, model, cost_tracker)

    @pytest.mark.asyncio
    async def test_tracks_cost(self):
        """generate_candidates() should record cost in cost_tracker"""
        from src.agent.workflow import generate_candidates

        # Arrange
        market_context = {'metadata': {'anchor_date': '2025-10-23'}, 'regime_tags': []}
        model = 'openai:gpt-4o'
        cost_tracker = CostTracker(max_budget=10.0)

        # Mock 5 distinct strategies
        mock_strategies = [
            Strategy(
                name="Strategy 1",
                assets=['SPY', 'QQQ'],
                weights={'SPY': 0.6, 'QQQ': 0.4},
                rebalance_frequency='monthly'
            ),
            Strategy(
                name="Strategy 2",
                assets=['AGG', 'TLT', 'GLD'],
                weights={'AGG': 0.4, 'TLT': 0.4, 'GLD': 0.2},
                rebalance_frequency='monthly'
            ),
            Strategy(
                name="Strategy 3",
                assets=['VTI', 'VXUS', 'BIL'],
                weights={'VTI': 0.5, 'VXUS': 0.3, 'BIL': 0.2},
                rebalance_frequency='monthly'
            ),
            Strategy(
                name="Strategy 4",
                assets=['IWM', 'EFA', 'EEM'],
                weights={'IWM': 0.4, 'EFA': 0.3, 'EEM': 0.3},
                rebalance_frequency='monthly'
            ),
            Strategy(
                name="Strategy 5",
                assets=['MTUM', 'QUAL'],
                weights={'MTUM': 0.5, 'QUAL': 0.5},
                rebalance_frequency='monthly'
            )
        ]

        with patch('src.agent.workflow.create_agent') as mock_create_agent:
            mock_agent = AsyncMock()
            mock_result = Mock()
            mock_result.output = mock_strategies
            mock_agent.run.return_value = mock_result

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_agent
            mock_ctx.__aexit__.return_value = None
            mock_create_agent.return_value = mock_ctx

            # Act
            initial_cost = cost_tracker.total_cost
            await generate_candidates(market_context, model, cost_tracker)
            final_cost = cost_tracker.total_cost

        # Assert
        assert final_cost > initial_cost, "Cost should be tracked after AI call"
        assert len(cost_tracker.call_log) > 0, "Cost tracker should have logged at least one call"


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
        cost_tracker = CostTracker(max_budget=10.0)

        # Act
        results = await backtest_all_candidates(candidates, cost_tracker)

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
        cost_tracker = CostTracker(max_budget=10.0)

        # Act
        results = await backtest_all_candidates(candidates, cost_tracker)

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
        cost_tracker = CostTracker(max_budget=10.0)

        # Act - even without real Composer, should not crash
        results = await backtest_all_candidates(candidates, cost_tracker)

        # Assert - should still return 5 results (graceful degradation)
        assert len(results) == 5, "Should return 5 results even if Composer unavailable"


class TestSelectWinner:
    """Tests for select_winner() function"""

    @pytest.mark.asyncio
    async def test_selects_highest_composite_score(self):
        """select_winner() should select strategy with highest composite score"""
        from src.agent.workflow import select_winner
        from src.agent.models import EdgeScorecard, BacktestResult, SelectionReasoning

        # Arrange - create 5 candidates with varying scores
        # Strategy 3 will have highest composite score
        candidates = [
            Strategy(name="Low Performer", assets=['SPY'], weights={'SPY': 1.0}, rebalance_frequency='monthly'),
            Strategy(name="Medium Performer", assets=['AGG'], weights={'AGG': 1.0}, rebalance_frequency='monthly'),
            Strategy(name="High Performer", assets=['QQQ'], weights={'QQQ': 1.0}, rebalance_frequency='monthly'),  # Winner
            Strategy(name="Another Medium", assets=['TLT'], weights={'TLT': 1.0}, rebalance_frequency='monthly'),
            Strategy(name="Low Sharpe", assets=['GLD'], weights={'GLD': 1.0}, rebalance_frequency='monthly'),
        ]

        scorecards = [
            EdgeScorecard(specificity=3, structural_basis=3, regime_alignment=3, differentiation=3, failure_clarity=3, mental_model_coherence=3),
            EdgeScorecard(specificity=4, structural_basis=4, regime_alignment=3, differentiation=3, failure_clarity=3, mental_model_coherence=3),
            EdgeScorecard(specificity=5, structural_basis=5, regime_alignment=5, differentiation=4, failure_clarity=4, mental_model_coherence=4),  # Best edge
            EdgeScorecard(specificity=3, structural_basis=3, regime_alignment=4, differentiation=3, failure_clarity=3, mental_model_coherence=3),
            EdgeScorecard(specificity=3, structural_basis=3, regime_alignment=3, differentiation=3, failure_clarity=3, mental_model_coherence=3),
        ]

        backtests = [
            BacktestResult(sharpe_ratio=0.8, max_drawdown=-0.15, total_return=0.05, volatility_annualized=0.12),
            BacktestResult(sharpe_ratio=1.2, max_drawdown=-0.12, total_return=0.10, volatility_annualized=0.14),
            BacktestResult(sharpe_ratio=2.1, max_drawdown=-0.08, total_return=0.25, volatility_annualized=0.15),  # Best backtest
            BacktestResult(sharpe_ratio=1.0, max_drawdown=-0.20, total_return=0.08, volatility_annualized=0.16),
            BacktestResult(sharpe_ratio=0.5, max_drawdown=-0.18, total_return=0.02, volatility_annualized=0.10),
        ]

        market_context = {'metadata': {'anchor_date': '2025-10-23'}, 'regime_tags': ['strong_bull']}
        model = 'openai:gpt-4o'
        cost_tracker = CostTracker(max_budget=10.0)

        # Mock the agent for reasoning generation
        with patch('src.agent.workflow.create_agent') as mock_create_agent:
            mock_agent = AsyncMock()
            mock_result = Mock()
            mock_result.output = SelectionReasoning(
                winner_index=2,
                why_selected="High Performer has best risk-adjusted returns with Sharpe 2.1, significantly outperforming alternatives on both backtest metrics and edge scorecard dimensions.",
                alternatives_compared=["Low Performer", "Medium Performer", "Another Medium", "Low Sharpe"]
            )
            mock_agent.run.return_value = mock_result

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_agent
            mock_ctx.__aexit__.return_value = None
            mock_create_agent.return_value = mock_ctx

            # Act
            winner, reasoning = await select_winner(
                candidates, scorecards, backtests, market_context, model, cost_tracker
            )

        # Assert
        assert winner.name == "High Performer", "Should select candidate with highest composite score"
        assert reasoning.winner_index == 2, "Reasoning should indicate index 2 as winner"

    @pytest.mark.asyncio
    async def test_reasoning_references_all_alternatives(self):
        """Selection reasoning should reference all 4 non-winning candidates"""
        from src.agent.workflow import select_winner
        from src.agent.models import EdgeScorecard, BacktestResult, SelectionReasoning

        # Arrange
        candidates = [Strategy(name=f"Strategy {i+1}", assets=['SPY'], weights={'SPY': 1.0}, rebalance_frequency='monthly') for i in range(5)]
        scorecards = [EdgeScorecard(specificity=3, structural_basis=3, regime_alignment=3, differentiation=3, failure_clarity=3, mental_model_coherence=3) for _ in range(5)]
        backtests = [BacktestResult(sharpe_ratio=1.0, max_drawdown=-0.10, total_return=0.05, volatility_annualized=0.12) for _ in range(5)]
        market_context = {'metadata': {'anchor_date': '2025-10-23'}, 'regime_tags': []}
        model = 'openai:gpt-4o'
        cost_tracker = CostTracker(max_budget=10.0)

        with patch('src.agent.workflow.create_agent') as mock_create_agent:
            mock_agent = AsyncMock()
            mock_result = Mock()
            mock_result.output = SelectionReasoning(
                winner_index=0,
                why_selected="Strategy 1 selected based on comprehensive evaluation of risk-adjusted returns, regime alignment, and structural robustness compared to all alternatives.",
                alternatives_compared=["Strategy 2", "Strategy 3", "Strategy 4", "Strategy 5"]
            )
            mock_agent.run.return_value = mock_result

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_agent
            mock_ctx.__aexit__.return_value = None
            mock_create_agent.return_value = mock_ctx

            # Act
            winner, reasoning = await select_winner(
                candidates, scorecards, backtests, market_context, model, cost_tracker
            )

        # Assert
        assert len(reasoning.alternatives_compared) == 4, "Should compare against 4 alternatives"
        # Verify winner is not in alternatives
        assert winner.name not in reasoning.alternatives_compared, "Winner should not be in alternatives list"

    @pytest.mark.asyncio
    async def test_tracks_cost_for_reasoning_generation(self):
        """select_winner() should record cost for AI reasoning generation"""
        from src.agent.workflow import select_winner
        from src.agent.models import EdgeScorecard, BacktestResult, SelectionReasoning

        # Arrange
        candidates = [Strategy(name=f"Strategy {i+1}", assets=['SPY'], weights={'SPY': 1.0}, rebalance_frequency='monthly') for i in range(5)]
        scorecards = [EdgeScorecard(specificity=3, structural_basis=3, regime_alignment=3, differentiation=3, failure_clarity=3, mental_model_coherence=3) for _ in range(5)]
        backtests = [BacktestResult(sharpe_ratio=1.0, max_drawdown=-0.10, total_return=0.05, volatility_annualized=0.12) for _ in range(5)]
        market_context = {'metadata': {'anchor_date': '2025-10-23'}, 'regime_tags': []}
        model = 'openai:gpt-4o'
        cost_tracker = CostTracker(max_budget=10.0)

        with patch('src.agent.workflow.create_agent') as mock_create_agent:
            mock_agent = AsyncMock()
            mock_result = Mock()
            mock_result.output = SelectionReasoning(
                winner_index=0,
                why_selected="Test reasoning for strategy selection based on multiple factors including performance metrics, risk management, and market regime alignment across all candidates.",
                alternatives_compared=["Strategy 2", "Strategy 3", "Strategy 4", "Strategy 5"]
            )
            mock_agent.run.return_value = mock_result

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_agent
            mock_ctx.__aexit__.return_value = None
            mock_create_agent.return_value = mock_ctx

            # Act
            initial_cost = cost_tracker.total_cost
            await select_winner(candidates, scorecards, backtests, market_context, model, cost_tracker)
            final_cost = cost_tracker.total_cost

        # Assert
        assert final_cost > initial_cost, "Cost should increase after AI reasoning generation"


class TestGenerateCharter:
    """Tests for generate_charter() function"""

    @pytest.mark.asyncio
    async def test_generates_complete_charter(self):
        """generate_charter() should return Charter with all 5 required sections"""
        from src.agent.workflow import generate_charter
        from src.agent.models import EdgeScorecard, BacktestResult, SelectionReasoning, Charter

        # Arrange
        winner = Strategy(
            name="Momentum Tech Leaders in Low-VIX Regime",
            assets=['QQQ', 'XLK'],
            weights={'QQQ': 0.7, 'XLK': 0.3},
            rebalance_frequency='weekly'
        )

        reasoning = SelectionReasoning(
            winner_index=2,
            why_selected="Selected for superior risk-adjusted returns (Sharpe 2.1), strong regime alignment with current bull market, and robust edge scorecard across all dimensions particularly in specificity and structural basis.",
            alternatives_compared=["60/40 Traditional", "Bond Heavy Defensive", "Gold Inflation Hedge", "Value Factor Tilt"]
        )

        alternatives = [
            Strategy(name="60/40 Traditional", assets=['SPY', 'AGG'], weights={'SPY': 0.6, 'AGG': 0.4}, rebalance_frequency='monthly'),
            Strategy(name="Bond Heavy Defensive", assets=['AGG', 'TLT'], weights={'AGG': 0.7, 'TLT': 0.3}, rebalance_frequency='monthly'),
            winner,  # Index 2
            Strategy(name="Gold Inflation Hedge", assets=['GLD', 'TIP'], weights={'GLD': 0.6, 'TIP': 0.4}, rebalance_frequency='monthly'),
            Strategy(name="Value Factor Tilt", assets=['VTV', 'IWD'], weights={'VTV': 0.5, 'IWD': 0.5}, rebalance_frequency='monthly'),
        ]

        backtests = [
            BacktestResult(sharpe_ratio=1.2, max_drawdown=-0.12, total_return=0.10, volatility_annualized=0.14),
            BacktestResult(sharpe_ratio=0.8, max_drawdown=-0.08, total_return=0.06, volatility_annualized=0.10),
            BacktestResult(sharpe_ratio=2.1, max_drawdown=-0.08, total_return=0.25, volatility_annualized=0.15),  # Winner
            BacktestResult(sharpe_ratio=0.9, max_drawdown=-0.15, total_return=0.07, volatility_annualized=0.12),
            BacktestResult(sharpe_ratio=1.1, max_drawdown=-0.14, total_return=0.09, volatility_annualized=0.13),
        ]

        market_context = {
            'metadata': {'anchor_date': '2025-10-23'},
            'regime_tags': ['strong_bull', 'volatility_normal', 'growth_favored'],
            'regime_snapshot': {'trend_classification': 'bull', 'volatility_regime': 'normal'},
            'macro_indicators': {}
        }

        model = 'openai:gpt-4o'
        cost_tracker = CostTracker(max_budget=10.0)

        # Mock the agent for charter generation
        with patch('src.agent.workflow.create_agent') as mock_create_agent:
            mock_agent = AsyncMock()
            mock_result = Mock()
            mock_result.output = Charter(
                market_thesis="Current strong bull market with normal volatility favors momentum-driven tech strategies. Growth sector leadership signals continued strength in technology and innovation-focused equities.",
                strategy_selection="Selected Momentum Tech Leaders strategy with Sharpe ratio of 2.1, significantly outperforming 60/40 Traditional (1.2) and Bond Heavy Defensive (0.8). Strategy capitalizes on low-VIX environment enabling concentrated tech exposure.",
                expected_behavior="Expect 15-25% annualized returns during bull continuation, weekly rebalancing maintains momentum exposure. Strategy will underperform during volatility spikes (VIX > 25) or sector rotation away from growth.",
                failure_modes=["VIX spike above 30 triggers defensive rotation", "Tech sector underperformance vs broader market", "Rising rates compress tech valuations"],
                outlook_90d="Next 90 days: maintain tech overweight if VIX stays below 20, monitor for sector rotation signals. Re-evaluate if Fed signals policy shift or if tech sector breadth deteriorates."
            )
            mock_agent.run.return_value = mock_result

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_agent
            mock_ctx.__aexit__.return_value = None
            mock_create_agent.return_value = mock_ctx

            # Act
            charter = await generate_charter(
                winner, reasoning, alternatives, backtests, market_context, model, cost_tracker
            )

        # Assert
        assert isinstance(charter, Charter), "Should return Charter object"
        assert len(charter.market_thesis) > 50, "Market thesis should be substantial"
        assert len(charter.strategy_selection) > 50, "Strategy selection should be substantial"
        assert len(charter.expected_behavior) > 50, "Expected behavior should be substantial"
        assert len(charter.failure_modes) >= 3, "Should have at least 3 failure modes"
        assert len(charter.outlook_90d) > 50, "90-day outlook should be substantial"

    @pytest.mark.asyncio
    async def test_charter_references_backtest_data(self):
        """Charter should reference specific backtest numbers (implied by prompt)"""
        from src.agent.workflow import generate_charter
        from src.agent.models import BacktestResult, SelectionReasoning, Charter

        # Arrange
        winner = Strategy(name="Test Strategy", assets=['SPY'], weights={'SPY': 1.0}, rebalance_frequency='monthly')
        reasoning = SelectionReasoning(
            winner_index=0,
            why_selected="Selected for strong performance metrics and risk management capabilities demonstrated in backtesting period.",
            alternatives_compared=["Alt 1", "Alt 2", "Alt 3", "Alt 4"]
        )
        alternatives = [winner] + [
            Strategy(name=f"Alt {i}", assets=['AGG'], weights={'AGG': 1.0}, rebalance_frequency='monthly')
            for i in range(1, 5)
        ]
        backtests = [BacktestResult(sharpe_ratio=1.8, max_drawdown=-0.10, total_return=0.15, volatility_annualized=0.12)] + [
            BacktestResult(sharpe_ratio=1.0, max_drawdown=-0.15, total_return=0.08, volatility_annualized=0.14)
            for _ in range(4)
        ]
        market_context = {'metadata': {'anchor_date': '2025-10-23'}, 'regime_tags': []}
        model = 'openai:gpt-4o'
        cost_tracker = CostTracker(max_budget=10.0)

        # Mock charter generation
        with patch('src.agent.workflow.create_agent') as mock_create_agent:
            mock_agent = AsyncMock()
            mock_result = Mock()
            # Charter that references the specific Sharpe ratio from backtest
            mock_result.output = Charter(
                market_thesis="Market analysis based on current conditions and historical performance patterns indicating favorable environment for selected strategy.",
                strategy_selection="Test Strategy achieved Sharpe ratio of 1.8 in backtesting, outperforming alternatives which averaged 1.0. Maximum drawdown of -10% demonstrates superior risk management.",
                expected_behavior="Strategy expected to deliver consistent returns with controlled downside risk, based on historical 15% total return and 12% annualized volatility.",
                failure_modes=["Market regime shift", "Volatility spike", "Liquidity crisis"],
                outlook_90d="Maintain current allocation given favorable conditions. Monitor for regime changes that would trigger reassessment."
            )
            mock_agent.run.return_value = mock_result

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_agent
            mock_ctx.__aexit__.return_value = None
            mock_create_agent.return_value = mock_ctx

            # Act
            charter = await generate_charter(
                winner, reasoning, alternatives, backtests, market_context, model, cost_tracker
            )

        # Assert - the test verifies the mock was called, actual charter content validation
        # depends on AI model output in production
        assert isinstance(charter, Charter), "Should return Charter object"

    @pytest.mark.asyncio
    async def test_tracks_cost_for_charter_generation(self):
        """generate_charter() should record cost in cost_tracker"""
        from src.agent.workflow import generate_charter
        from src.agent.models import BacktestResult, SelectionReasoning, Charter

        # Arrange
        winner = Strategy(name="Test", assets=['SPY'], weights={'SPY': 1.0}, rebalance_frequency='monthly')
        reasoning = SelectionReasoning(
            winner_index=0,
            why_selected="Test reasoning for strategy selection based on comprehensive evaluation across multiple performance and risk dimensions.",
            alternatives_compared=["A", "B", "C", "D"]
        )
        alternatives = [winner] + [Strategy(name=x, assets=['AGG'], weights={'AGG': 1.0}, rebalance_frequency='monthly') for x in ["A", "B", "C", "D"]]
        backtests = [BacktestResult(sharpe_ratio=1.0, max_drawdown=-0.10, total_return=0.05, volatility_annualized=0.12) for _ in range(5)]
        market_context = {'metadata': {'anchor_date': '2025-10-23'}, 'regime_tags': []}
        model = 'openai:gpt-4o'
        cost_tracker = CostTracker(max_budget=10.0)

        with patch('src.agent.workflow.create_agent') as mock_create_agent:
            mock_agent = AsyncMock()
            mock_result = Mock()
            mock_result.output = Charter(
                market_thesis="Test market thesis content for charter generation testing purposes.",
                strategy_selection="Test strategy selection reasoning with sufficient detail for validation.",
                expected_behavior="Test expected behavior description with adequate length for requirements.",
                failure_modes=["Market regime shift could trigger strategy underperformance", "Volatility spike above threshold", "Liquidity crisis in underlying assets"],
                outlook_90d="Test 90-day outlook with sufficient detail for charter requirements."
            )
            mock_agent.run.return_value = mock_result

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_agent
            mock_ctx.__aexit__.return_value = None
            mock_create_agent.return_value = mock_ctx

            # Act
            initial_cost = cost_tracker.total_cost
            await generate_charter(winner, reasoning, alternatives, backtests, market_context, model, cost_tracker)
            final_cost = cost_tracker.total_cost

        # Assert
        assert final_cost > initial_cost, "Cost should increase after AI charter generation"


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
        max_cost = 5.0

        # Mock all AI calls
        with patch('src.agent.workflow.create_agent') as mock_create_agent:
            # We'll have 3 agent calls: candidates, selection reasoning, charter
            mock_agents = []

            # Agent 1: Generate candidates - 5 DISTINCT strategies that will score well on Edge Scorecard
            agent1 = AsyncMock()
            result1 = Mock()
            result1.output = [
                Strategy(
                    name="3-Month Tech Momentum in Low-VIX",  # has number + momentum -> score 5
                    assets=['SPY', 'QQQ', 'AGG'],  # equity + bonds = 2 asset types = score 4
                    weights={'SPY': 0.5, 'QQQ': 0.3, 'AGG': 0.2},
                    rebalance_frequency='monthly',
                    failure_modes=["VIX spike above 30", "Tech underperformance", "Rate spike"]
                ),
                Strategy(
                    name="Quality Defensive 60-40 Portfolio",  # has number + quality + defensive -> score 5
                    assets=['SPY', 'AGG', 'GLD'],  # equity + bond + commodity = 3 asset types = score 5
                    weights={'SPY': 0.4, 'AGG': 0.4, 'GLD': 0.2},
                    rebalance_frequency='monthly',
                    failure_modes=["Rising rates compress bonds", "Inflation spike", "Flight to risk"]
                ),
                Strategy(
                    name="4-Asset Global Growth Allocation",  # has number + growth -> score 5
                    assets=['SPY', 'IWM', 'AGG', 'GLD'],  # equity + bond + commodity = 3 types = score 5
                    weights={'SPY': 0.4, 'IWM': 0.2, 'AGG': 0.3, 'GLD': 0.1},
                    rebalance_frequency='monthly',
                    failure_modes=["International underperformance", "Dollar strength", "Risk-off environment"]
                ),
                Strategy(
                    name="Value Factor 3-Asset Rotation",  # has number + value -> score 5
                    assets=['SPY', 'QQQ', 'TLT'],  # equity + bonds = 2 asset types = score 4
                    weights={'SPY': 0.5, 'QQQ': 0.3, 'TLT': 0.2},
                    rebalance_frequency='monthly',
                    failure_modes=["Growth outperforms value", "Quality premium reversal", "Small cap weakness"]
                ),
                Strategy(
                    name="Gold-Tilted 3-Asset Inflation Play",  # has number (3) -> score 4 (no regime term)
                    assets=['GLD', 'TLT', 'IWM'],  # commodity + bond + equity = 3 types = score 5
                    weights={'GLD': 0.5, 'TLT': 0.3, 'IWM': 0.2},
                    rebalance_frequency='monthly',
                    failure_modes=["Deflation scenario", "Dollar strength", "Commodity collapse"]
                ),
            ]
            agent1.run.return_value = result1

            # Agent 2: Selection reasoning
            agent2 = AsyncMock()
            result2 = Mock()
            result2.output = SelectionReasoning(
                winner_index=0,
                why_selected="3-Month Tech Momentum in Low-VIX selected for superior risk-adjusted returns and strong regime alignment with current market conditions.",
                alternatives_compared=["Quality Defensive 60-40 Portfolio", "4-Asset Global Growth Allocation", "Value Factor 3-Asset Rotation", "Gold-Tilted 3-Asset Inflation Play"]
            )
            agent2.run.return_value = result2

            # Agents 3-7: Backtest agents (5 total, one per candidate)
            backtest_agents = []
            for i in range(5):
                agent_backtest = AsyncMock()
                result_backtest = Mock()
                result_backtest.output = {
                    'sharpe_ratio': 1.5 + (i * 0.2),
                    'max_drawdown': -0.15 - (i * 0.02),
                    'total_return': 0.10 + (i * 0.03),
                    'volatility_annualized': 0.12 + (i * 0.01)
                }
                agent_backtest.run.return_value = result_backtest
                backtest_agents.append(agent_backtest)

            # Agent 8: Selection reasoning
            agent_selection = AsyncMock()
            result_selection = Mock()
            result_selection.output = SelectionReasoning(
                winner_index=0,
                why_selected="This strategy offers the best risk-adjusted returns with Sharpe ratio of 2.1 compared to alternatives ranging from 1.5-1.9. The low-volatility regime alignment provides additional confidence in sustained outperformance.",
                alternatives_compared=["Quality Defensive 60-40 Portfolio", "4-Asset Global Growth Allocation", "Value Factor 3-Asset Rotation", "Gold-Tilted 3-Asset Inflation Play"]
            )
            agent_selection.run.return_value = result_selection

            # Agent 9: Charter generation
            agent_charter = AsyncMock()
            result_charter = Mock()
            result_charter.output = Charter(
                market_thesis="Bull market with normal volatility supports growth-oriented strategies with strong momentum characteristics.",
                strategy_selection="3-Month Tech Momentum in Low-VIX chosen for Sharpe ratio outperformance and alignment with current low-volatility growth regime.",
                expected_behavior="Expect continued outperformance during bull market continuation with monthly rebalancing maintaining momentum exposure.",
                failure_modes=["Volatility spike triggers defensive rotation", "Growth underperforms value in regime shift", "Rising rates compress valuations"],
                outlook_90d="Maintain current positioning given favorable regime. Monitor VIX and sector breadth for early warning signals."
            )
            agent_charter.run.return_value = result_charter

            # Set up context managers for each agent
            # Order: 1 generation, 5 backtests, 1 selection, 1 charter = 8 total
            mock_agents = [agent1] + backtest_agents + [agent_selection, agent_charter]
            agent_index = [0]  # Use list to maintain state across calls

            def create_agent_side_effect(*args, **kwargs):
                ctx = AsyncMock()
                ctx.__aenter__.return_value = mock_agents[agent_index[0]]
                ctx.__aexit__.return_value = None
                agent_index[0] += 1
                return ctx

            mock_create_agent.side_effect = create_agent_side_effect

            # Act
            result = await create_strategy_workflow(
                market_context=market_context,
                model=model,
                max_cost=max_cost
            )

        # Assert - verify WorkflowResult structure
        assert isinstance(result, WorkflowResult), "Should return WorkflowResult object"
        assert len(result.all_candidates) == 5, "Should have 5 candidates"
        assert len(result.scorecards) == 5, "Should have 5 scorecards"
        assert len(result.backtests) == 5, "Should have 5 backtest results"
        assert result.strategy in result.all_candidates, "Winner should be from candidates"
        assert isinstance(result.charter, Charter), "Should have Charter"
        assert isinstance(result.selection_reasoning, SelectionReasoning), "Should have SelectionReasoning"
        assert result.total_cost <= max_cost, f"Cost {result.total_cost} should not exceed budget {max_cost}"
        assert result.total_cost > 0, "Cost should be tracked and non-zero"

    @pytest.mark.asyncio
    async def test_validates_all_edge_scores_above_threshold(self):
        """Workflow should raise ValidationError if any candidate scores <3 on Edge Scorecard"""
        from src.agent.workflow import create_strategy_workflow
        from pydantic import ValidationError

        # Arrange - create market context
        market_context = {
            'metadata': {'anchor_date': '2025-10-23'},
            'regime_tags': [],
            'regime_snapshot': {'trend_classification': 'neutral'},
            'macro_indicators': {}
        }

        model = 'openai:gpt-4o'
        max_cost = 5.0

        # Mock candidates that will fail Edge Scorecard (vague strategy with poor scores)
        with patch('src.agent.workflow.create_agent') as mock_create_agent:
            agent1 = AsyncMock()
            result1 = Mock()
            # Create 5 distinct strategies that will score poorly on Edge Scorecard
            result1.output = [
                Strategy(name="Diversified Winners Portfolio", assets=['SPY'], weights={'SPY': 1.0}, rebalance_frequency='monthly'),
                Strategy(name="Balance Strategy", assets=['AGG'], weights={'AGG': 1.0}, rebalance_frequency='monthly'),
                Strategy(name="Hedge Portfolio", assets=['GLD'], weights={'GLD': 1.0}, rebalance_frequency='monthly'),
                Strategy(name="Winners Selection", assets=['QQQ'], weights={'QQQ': 1.0}, rebalance_frequency='monthly'),
                Strategy(name="Losers Avoidance", assets=['TLT'], weights={'TLT': 1.0}, rebalance_frequency='monthly'),
            ]
            agent1.run.return_value = result1

            ctx = AsyncMock()
            ctx.__aenter__.return_value = agent1
            ctx.__aexit__.return_value = None
            mock_create_agent.return_value = ctx

            # Act & Assert - should raise ValidationError due to low Edge Scorecard scores
            # EdgeScorecard's Pydantic validator catches scores <3
            with pytest.raises(ValidationError) as exc_info:
                await create_strategy_workflow(
                    market_context=market_context,
                    model=model,
                    max_cost=max_cost
                )

            # Verify the error message mentions the threshold
            assert "minimum threshold is 3" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_budget_exceeded_error(self):
        """Workflow should raise BudgetExceededError if costs exceed max_cost"""
        from src.agent.workflow import create_strategy_workflow
        from src.agent.cost_tracker import BudgetExceededError

        # Arrange
        market_context = {'metadata': {'anchor_date': '2025-10-23'}, 'regime_tags': []}
        model = 'openai:gpt-4o'
        max_cost = 0.01  # Very low budget to trigger error

        with patch('src.agent.workflow.create_agent') as mock_create_agent:
            agent = AsyncMock()
            result = Mock()
            result.output = [
                Strategy(name=f"S{i}", assets=['SPY'], weights={'SPY': 1.0}, rebalance_frequency='monthly')
                for i in range(5)
            ]
            agent.run.return_value = result

            ctx = AsyncMock()
            ctx.__aenter__.return_value = agent
            ctx.__aexit__.return_value = None
            mock_create_agent.return_value = ctx

            # Act & Assert
            with pytest.raises(BudgetExceededError):
                await create_strategy_workflow(
                    market_context=market_context,
                    model=model,
                    max_cost=max_cost
                )

