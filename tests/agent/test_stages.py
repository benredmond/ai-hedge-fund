"""
Tests for workflow stage classes (CandidateGenerator, WinnerSelector, CharterGenerator).

These tests validate the core logic of each stage class, focusing on:
- Input validation and error handling
- Business logic correctness (e.g., ranking formulas)
- Output structure and requirements

Note: AI generation is not mocked - tests use real LLM calls.
"""

import pytest
from unittest.mock import AsyncMock, patch
from src.agent.stages import CandidateGenerator, WinnerSelector, CharterGenerator
from src.agent.models import (
    Strategy,
    BacktestResult,
    EdgeScorecard,
    SelectionReasoning,
    Charter,
    RebalanceFrequency
)


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_market_context():
    """Minimal market context for testing."""
    return {
        "metadata": {
            "anchor_date": "2024-01-15",
            "generated_at": "2024-01-15T12:00:00Z",
            "version": "v1.0.0"
        },
        "regime_snapshot": {
            "trend": {"regime": "bull"},
            "volatility": {"regime": "normal", "vix_latest": 15.5}
        },
        "regime_tags": ["bull_market", "normal_volatility"]
    }


@pytest.fixture
def sample_candidates():
    """5 sample candidates for testing."""
    return [
        Strategy(
            name=f"Strategy {i+1}",
            assets=[f"TICKER{i}", f"TICKER{i+1}"],
            weights={f"TICKER{i}": 0.6, f"TICKER{i+1}": 0.4},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={}
        )
        for i in range(5)
    ]


@pytest.fixture
def sample_scorecards():
    """5 sample edge scorecards with different scores (all >= 3 per dimension)."""
    return [
        EdgeScorecard(
            thesis_quality=4,
            edge_economics=3,
            risk_framework=4,
            regime_awareness=4,
            strategic_coherence=4
        ),  # total_score = 3.8
        EdgeScorecard(
            thesis_quality=5,
            edge_economics=5,
            risk_framework=5,
            regime_awareness=5,
            strategic_coherence=5
        ),  # total_score = 5.0 (highest)
        EdgeScorecard(
            thesis_quality=3,
            edge_economics=3,
            risk_framework=3,
            regime_awareness=3,
            strategic_coherence=3
        ),  # total_score = 3.0 (minimum)
        EdgeScorecard(
            thesis_quality=4,
            edge_economics=4,
            risk_framework=4,
            regime_awareness=4,
            strategic_coherence=3
        ),  # total_score = 3.8
        EdgeScorecard(
            thesis_quality=3,
            edge_economics=4,
            risk_framework=4,
            regime_awareness=3,
            strategic_coherence=4
        ),  # total_score = 3.6
    ]


@pytest.fixture
def sample_backtests():
    """5 sample backtest results with varying performance."""
    return [
        BacktestResult(sharpe_ratio=1.2, max_drawdown=-0.15, total_return=0.08, volatility_annualized=0.12),
        BacktestResult(sharpe_ratio=2.1, max_drawdown=-0.10, total_return=0.15, volatility_annualized=0.10),
        BacktestResult(sharpe_ratio=0.8, max_drawdown=-0.20, total_return=0.05, volatility_annualized=0.15),
        BacktestResult(sharpe_ratio=1.5, max_drawdown=-0.12, total_return=0.10, volatility_annualized=0.11),
        BacktestResult(sharpe_ratio=1.0, max_drawdown=-0.18, total_return=0.06, volatility_annualized=0.14),
    ]


# ============================================================================
# CandidateGenerator Tests
# ============================================================================

class TestCandidateGenerator:
    """Test candidate generation stage."""

    @pytest.mark.asyncio
    async def test_raises_error_when_wrong_count(self, sample_market_context):
        """
        Validate that generate() raises ValueError if AI returns != 5 candidates.

        This is a critical safety check to ensure the workflow always
        gets exactly 5 candidates as required.
        """
        generator = CandidateGenerator()

        # Mock the agent for phased prompting
        with patch('src.agent.stages.candidate_generator.create_agent') as mock_create:
            # Phase 1 mock (research): returns dict
            mock_research_agent = AsyncMock()
            mock_research_result = AsyncMock()
            mock_research_result.output = {
                "macro_regime": {"classification": "expansion"},
                "market_regime": {"trend": "bull"}
            }
            mock_research_agent.run.return_value = mock_research_result
            mock_research_context = AsyncMock()
            mock_research_context.__aenter__.return_value = mock_research_agent

            # Phase 2 mock (generate): returns list of strategies (wrong count)
            mock_generate_agent = AsyncMock()
            mock_generate_result = AsyncMock()
            mock_generate_result.output = [
                Strategy(
                    name="Only Strategy",
                    assets=["SPY"],
                    weights={"SPY": 1.0},
                    rebalance_frequency=RebalanceFrequency.MONTHLY,
                    logic_tree={}
                )
            ]  # Only 1 strategy instead of 5
            mock_generate_agent.run.return_value = mock_generate_result
            mock_generate_context = AsyncMock()
            mock_generate_context.__aenter__.return_value = mock_generate_agent

            # Return different contexts for each call
            mock_create.side_effect = [mock_research_context, mock_generate_context]

            with pytest.raises(ValueError, match="Expected 5 candidates, got 1"):
                await generator.generate(sample_market_context, model="openai:gpt-4o")

    @pytest.mark.asyncio
    async def test_detects_duplicate_ticker_sets(self, sample_market_context):
        """
        Validate that generate() raises ValueError if duplicates detected.

        Duplicates are defined as candidates with identical ticker sets
        (same assets, order-independent).
        """
        generator = CandidateGenerator()

        # Mock the agent for phased prompting
        with patch('src.agent.stages.candidate_generator.create_agent') as mock_create:
            # Phase 1 mock (research): returns dict
            mock_research_agent = AsyncMock()
            mock_research_result = AsyncMock()
            mock_research_result.output = {
                "macro_regime": {"classification": "expansion"},
                "market_regime": {"trend": "bull"}
            }
            mock_research_agent.run.return_value = mock_research_result
            mock_research_context = AsyncMock()
            mock_research_context.__aenter__.return_value = mock_research_agent

            # Phase 2 mock (generate): returns list with duplicates
            mock_generate_agent = AsyncMock()
            mock_generate_result = AsyncMock()

            # Create 5 candidates, but 2 have same ticker set
            duplicate_candidates = []
            for i in range(5):
                # Candidates 0 and 3 will have same tickers
                tickers = ["SPY", "QQQ"] if i in [0, 3] else [f"TICKER{i}", f"ASSET{i}"]
                weights = {tickers[0]: 0.5, tickers[1]: 0.5}
                duplicate_candidates.append(
                    Strategy(
                        name=f"Strategy {i}",
                        assets=tickers,
                        weights=weights,
                        rebalance_frequency=RebalanceFrequency.MONTHLY,
                        logic_tree={}
                    )
                )

            mock_generate_result.output = duplicate_candidates
            mock_generate_agent.run.return_value = mock_generate_result
            mock_generate_context = AsyncMock()
            mock_generate_context.__aenter__.return_value = mock_generate_agent

            # Return different contexts for each call
            mock_create.side_effect = [mock_research_context, mock_generate_context]

            with pytest.raises(ValueError, match="Duplicate candidates detected"):
                await generator.generate(sample_market_context, model="openai:gpt-4o")


# ============================================================================
# WinnerSelector Tests
# ============================================================================

class TestWinnerSelector:
    """Test winner selection stage."""

    @pytest.mark.asyncio
    async def test_selects_highest_composite_score(
        self,
        sample_candidates,
        sample_scorecards,
        sample_backtests,
        sample_market_context
    ):
        """
        Validate that select() chooses candidate with highest composite score.

        Composite formula:
            score = 0.4 × Sharpe + 0.3 × EdgeScore + 0.2 × RegimeFit + 0.1 × (1 - abs(Drawdown))

        Given the test data:
        - Candidate 1 has best Sharpe (2.1) and best EdgeScore (4.7)
        - Should win despite not having best drawdown
        """
        selector = WinnerSelector()

        # Mock the reasoning generation (AI call)
        with patch('src.agent.stages.winner_selector.create_agent') as mock_create:
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            mock_result.output = SelectionReasoning(
                why_selected="Mock reasoning for testing purposes that meets the minimum length requirement of 100 characters for this field.",
                winner_index=1,  # Candidate 1 has highest composite score
                tradeoffs_accepted="Accepting higher volatility for better returns under current conditions.",
                alternatives_rejected=[c.name for i, c in enumerate(sample_candidates) if i != 1],
                conviction_level=0.85
            )
            mock_agent.run.return_value = mock_result
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_agent
            mock_create.return_value = mock_context

            winner, reasoning = await selector.select(
                sample_candidates,
                sample_scorecards,
                sample_backtests,
                sample_market_context,
                model="openai:gpt-4o"
            )

            # Calculate expected winner manually
            # Candidate 1: Sharpe=2.1, Edge=4.7, Regime=5, Drawdown=-0.10
            sharpe_norm = (2.1 + 1) / 4  # = 0.775
            edge_norm = 4.7 / 5  # = 0.94
            regime_norm = 5 / 5  # = 1.0
            drawdown_norm = 1 - 0.10  # = 0.90
            expected_score = 0.4 * 0.775 + 0.3 * 0.94 + 0.2 * 1.0 + 0.1 * 0.90
            # = 0.31 + 0.282 + 0.2 + 0.09 = 0.882

            # Candidate 1 should have highest composite score
            assert winner == sample_candidates[1], "Should select candidate with highest composite score"
            assert reasoning.winner_index == 1, "Reasoning should have correct winner_index"

    @pytest.mark.asyncio
    async def test_reasoning_has_correct_alternatives(
        self,
        sample_candidates,
        sample_scorecards,
        sample_backtests,
        sample_market_context
    ):
        """
        Validate that SelectionReasoning includes all 4 non-winner candidates.
        """
        selector = WinnerSelector()

        # Mock the reasoning generation
        with patch('src.agent.stages.winner_selector.create_agent') as mock_create:
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            mock_result.output = SelectionReasoning(
                why_selected="Mock reasoning for testing purposes that meets the minimum length requirement of 100 characters for this field.",
                winner_index=0,
                tradeoffs_accepted="Accepting higher volatility for better returns under current conditions.",
                alternatives_rejected=[c.name for i, c in enumerate(sample_candidates) if i != 0],
                conviction_level=0.85
            )
            mock_agent.run.return_value = mock_result
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_agent
            mock_create.return_value = mock_context

            winner, reasoning = await selector.select(
                sample_candidates,
                sample_scorecards,
                sample_backtests,
                sample_market_context,
                model="openai:gpt-4o"
            )

            # Should have 4 alternatives (all except winner)
            assert len(reasoning.alternatives_rejected) == 4, "Should have 4 alternatives"

            # Winner's name should not be in alternatives
            assert winner.name not in reasoning.alternatives_rejected, "Winner should not be in alternatives"

            # All other names should be in alternatives
            other_names = [c.name for c in sample_candidates if c.name != winner.name]
            assert set(reasoning.alternatives_rejected) == set(other_names), "Alternatives should match non-winners"

    @pytest.mark.asyncio
    async def test_composite_score_normalization(
        self,
        sample_candidates,
        sample_market_context
    ):
        """
        Validate that normalization formula handles edge cases correctly.

        Tests:
        - Sharpe ratio normalization: (-1 to 3) → (0 to 1)
        - Edge score normalization: (1 to 5) → (0.2 to 1.0)
        - Regime alignment: (1 to 5) → (0.2 to 1.0)
        - Drawdown: negative values normalized correctly
        """
        selector = WinnerSelector()

        # Create extreme test cases (minimum 3 per dimension due to validation)
        extreme_scorecards = [
            EdgeScorecard(thesis_quality=3, edge_economics=3, risk_framework=3,
                         regime_awareness=3, strategic_coherence=3),  # Minimum: 3.0
            EdgeScorecard(thesis_quality=5, edge_economics=5, risk_framework=5,
                         regime_awareness=5, strategic_coherence=5),  # Maximum: 5.0
            EdgeScorecard(thesis_quality=3, edge_economics=3, risk_framework=3,
                         regime_awareness=3, strategic_coherence=3),
            EdgeScorecard(thesis_quality=3, edge_economics=3, risk_framework=3,
                         regime_awareness=3, strategic_coherence=3),
            EdgeScorecard(thesis_quality=3, edge_economics=3, risk_framework=3,
                         regime_awareness=3, strategic_coherence=3),
        ]

        extreme_backtests = [
            BacktestResult(sharpe_ratio=-1.0, max_drawdown=-0.50, total_return=-0.30, volatility_annualized=0.25),  # Worst
            BacktestResult(sharpe_ratio=3.0, max_drawdown=-0.05, total_return=0.40, volatility_annualized=0.08),   # Best
            BacktestResult(sharpe_ratio=1.0, max_drawdown=-0.15, total_return=0.10, volatility_annualized=0.12),
            BacktestResult(sharpe_ratio=1.0, max_drawdown=-0.15, total_return=0.10, volatility_annualized=0.12),
            BacktestResult(sharpe_ratio=1.0, max_drawdown=-0.15, total_return=0.10, volatility_annualized=0.12),
        ]

        # Mock reasoning generation
        with patch('src.agent.stages.winner_selector.create_agent') as mock_create:
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            mock_result.output = SelectionReasoning(
                why_selected="Mock reasoning for testing purposes that meets the minimum length requirement of 100 characters for this field.",
                winner_index=1,  # Candidate 1 has best extreme metrics
                tradeoffs_accepted="Accepting higher volatility for better returns under current conditions.",
                alternatives_rejected=[c.name for i, c in enumerate(sample_candidates) if i != 1],
                conviction_level=0.85
            )
            mock_agent.run.return_value = mock_result
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_agent
            mock_create.return_value = mock_context

            winner, reasoning = await selector.select(
                sample_candidates,
                extreme_scorecards,
                extreme_backtests,
                sample_market_context,
                model="openai:gpt-4o"
            )

            # Candidate 1 (best Sharpe and Edge) should win
            assert reasoning.winner_index == 1, "Candidate with best metrics should win"


# ============================================================================
# CharterGenerator Tests
# ============================================================================

class TestCharterGenerator:
    """Test charter generation stage."""

    @pytest.mark.asyncio
    async def test_charter_has_all_required_sections(
        self,
        sample_candidates,
        sample_backtests,
        sample_scorecards,
        sample_market_context
    ):
        """
        Validate that generated charter has all 5 required sections.

        Required sections:
        1. market_thesis
        2. strategy_selection
        3. expected_behavior
        4. failure_modes (list)
        5. outlook_90d
        """
        generator = CharterGenerator()

        # Create mock reasoning (must have >= 100 char explanation)
        reasoning = SelectionReasoning(
            why_selected="Selected for best risk-adjusted returns in the current market regime, with superior Sharpe ratio and drawdown control compared to alternatives.",
            winner_index=0,
            tradeoffs_accepted="Accepting slightly higher volatility for better long-term returns.",
            alternatives_rejected=["Strategy 2", "Strategy 3", "Strategy 4", "Strategy 5"],
            conviction_level=0.85
        )

        # Mock the charter generation (AI call)
        with patch('src.agent.stages.charter_generator.create_agent') as mock_create:
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            mock_result.output = Charter(
                market_thesis="This is a bull market with normal volatility...",
                strategy_selection="We selected this strategy because of superior Sharpe ratio...",
                expected_behavior="We expect positive returns in bull market conditions...",
                failure_modes=[
                    "Sudden volatility spike could trigger losses",
                    "Market regime shift to bear market"
                ],
                outlook_90d="Over the next 90 days, we expect this strategy to perform well..."
            )
            mock_agent.run.return_value = mock_result
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_agent
            mock_create.return_value = mock_context

            charter = await generator.generate(
                sample_candidates[0],
                reasoning,
                sample_candidates,
                sample_scorecards,
                sample_backtests,
                sample_market_context,
                model="openai:gpt-4o"
            )

            # Validate all sections present
            assert charter.market_thesis, "Charter missing market_thesis"
            assert len(charter.market_thesis) > 20, "market_thesis too short"

            assert charter.strategy_selection, "Charter missing strategy_selection"
            assert len(charter.strategy_selection) > 20, "strategy_selection too short"

            assert charter.expected_behavior, "Charter missing expected_behavior"
            assert len(charter.expected_behavior) > 20, "expected_behavior too short"

            assert charter.failure_modes, "Charter missing failure_modes"
            assert len(charter.failure_modes) >= 2, "Should have at least 2 failure modes"
            for mode in charter.failure_modes:
                assert len(mode) > 10, "Failure mode too short"

            assert charter.outlook_90d, "Charter missing outlook_90d"
            assert len(charter.outlook_90d) > 20, "outlook_90d too short"

    @pytest.mark.asyncio
    async def test_charter_prompt_includes_context(
        self,
        sample_candidates,
        sample_backtests,
        sample_scorecards,
        sample_market_context
    ):
        """
        Validate that the prompt sent to AI includes all necessary context.

        Should include:
        - Winner strategy details
        - Backtest results
        - Selection reasoning
        - Alternative candidates
        - Market context
        """
        generator = CharterGenerator()

        reasoning = SelectionReasoning(
            why_selected="Selected for best risk-adjusted returns in the current market regime, with superior Sharpe ratio and drawdown control compared to alternatives.",
            winner_index=1,
            tradeoffs_accepted="Accepting slightly higher volatility for better long-term returns.",
            alternatives_rejected=["Strategy 1", "Strategy 3", "Strategy 4", "Strategy 5"],
            conviction_level=0.85
        )

        # Mock and capture the prompt
        captured_prompt = None

        with patch('src.agent.stages.charter_generator.create_agent') as mock_create:
            mock_agent = AsyncMock()

            async def capture_prompt(prompt):
                nonlocal captured_prompt
                captured_prompt = prompt
                mock_result = AsyncMock()
                mock_result.output = Charter(
                    market_thesis="Test thesis that meets minimum requirements",
                    strategy_selection="Test selection explanation that meets minimum",
                    expected_behavior="Test behavior description that meets minimum",
                    failure_modes=["Sudden market reversal could cause losses",
                                   "Volatility spike could trigger drawdown"],
                    outlook_90d="Test outlook prediction that meets minimum"
                )
                return mock_result

            mock_agent.run.side_effect = capture_prompt
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_agent
            mock_create.return_value = mock_context

            await generator.generate(
                sample_candidates[1],
                reasoning,
                sample_candidates,
                sample_scorecards,
                sample_backtests,
                sample_market_context,
                model="openai:gpt-4o"
            )

            # Validate prompt includes key elements
            assert captured_prompt is not None, "Prompt should have been captured"
            assert sample_candidates[1].name in captured_prompt, "Prompt should include winner name"
            assert "sharpe_ratio" in captured_prompt, "Prompt should include backtest metrics"
            assert reasoning.why_selected in captured_prompt, "Prompt should include selection reasoning"
            assert sample_market_context["metadata"]["anchor_date"] in captured_prompt, "Prompt should include market context date"
            assert "regime_tags" in captured_prompt, "Prompt should reference regime"
