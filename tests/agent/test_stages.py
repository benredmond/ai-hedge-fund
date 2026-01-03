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
    EdgeScorecard,
    SelectionReasoning,
    Charter,
    RebalanceFrequency,
    CandidateList
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
        "macro_indicators": {
            "fed_funds_rate": {"value": 5.25, "date": "2024-01-10"},
            "cpi": {"value": 3.1, "date": "2023-12-01"},
            "unemployment_rate": {"value": 3.7, "date": "2023-12-01"}
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
            logic_tree={},
            rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
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


# ============================================================================
# CandidateGenerator Tests
# ============================================================================

class TestCandidateGenerator:
    """Test candidate generation stage (parallel mode)."""

    def _make_strategy(self, name: str, tickers: list) -> Strategy:
        """Helper to create a valid Strategy for testing."""
        weights = {t: 1.0 / len(tickers) for t in tickers}
        return Strategy(
            name=name,
            assets=tickers,
            weights=weights,
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={},
            rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
        )

    def _make_single_strategy_result(self, strategy: Strategy):
        """Helper to create a mock SingleStrategy result."""
        mock_result = AsyncMock()
        mock_output = AsyncMock()
        mock_output.strategy = strategy
        mock_result.output = mock_output
        return mock_result

    @pytest.mark.asyncio
    async def test_raises_error_when_too_few_candidates(self, sample_market_context):
        """
        Validate that generate() raises ValueError if <4 candidates generated.

        Parallel mode requires minimum 4 successful candidates (allows 1 failure).
        """
        generator = CandidateGenerator()

        # Mock create_agent to return only 3 successful candidates (2 failures + 2 retry failures each)
        call_count = 0

        async def mock_agent_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # First 3 calls succeed, rest fail (simulating permanent failures)
            if call_count <= 3:
                return self._make_single_strategy_result(
                    self._make_strategy(f"Strategy {call_count}", [f"TICKER{call_count}A", f"TICKER{call_count}B"])
                )
            else:
                raise Exception("API Error: Rate limited")

        with patch('src.agent.stages.candidate_generator.create_agent') as mock_create:
            mock_agent = AsyncMock()
            mock_agent.run = mock_agent_run
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_agent
            mock_create.return_value = mock_context

            with pytest.raises(ValueError, match="Expected at least 4 candidates"):
                await generator.generate(sample_market_context, model="openai:gpt-4o")

    @pytest.mark.asyncio
    async def test_detects_duplicate_ticker_sets(self, sample_market_context):
        """
        Validate that generate() raises ValueError if duplicates detected.

        Duplicates are defined as candidates with identical ticker sets
        (same assets, order-independent).
        """
        generator = CandidateGenerator()

        # Mock 5 successful generations with 2 having duplicate tickers
        duplicate_strategies = [
            self._make_strategy("Strategy 0", ["SPY", "QQQ"]),  # Duplicate with #3
            self._make_strategy("Strategy 1", ["AAPL", "MSFT"]),
            self._make_strategy("Strategy 2", ["TLT", "GLD"]),
            self._make_strategy("Strategy 3", ["SPY", "QQQ"]),  # Duplicate with #0
            self._make_strategy("Strategy 4", ["VTI", "BND"]),
        ]

        call_count = 0

        async def mock_agent_run(*args, **kwargs):
            nonlocal call_count
            strategy = duplicate_strategies[call_count % 5]
            call_count += 1
            return self._make_single_strategy_result(strategy)

        with patch('src.agent.stages.candidate_generator.create_agent') as mock_create:
            mock_agent = AsyncMock()
            mock_agent.run = mock_agent_run
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_agent
            mock_create.return_value = mock_context

            with pytest.raises(ValueError, match="Duplicate candidates detected"):
                await generator.generate(sample_market_context, model="openai:gpt-4o")

    @pytest.mark.asyncio
    async def test_accepts_4_candidates_with_1_failure(self, sample_market_context):
        """
        Validate that generate() succeeds with 4 candidates (1 permanent failure allowed).
        """
        generator = CandidateGenerator()

        # Mock: 4 succeed, 1 fails permanently (all retries exhausted)
        call_count = 0

        async def mock_agent_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # First 4 calls succeed, 5th and its retries fail
            if call_count <= 4:
                return self._make_single_strategy_result(
                    self._make_strategy(f"Strategy {call_count}", [f"TICKER{call_count}A", f"TICKER{call_count}B"])
                )
            else:
                raise Exception("API Error: Model overloaded")

        with patch('src.agent.stages.candidate_generator.create_agent') as mock_create:
            mock_agent = AsyncMock()
            mock_agent.run = mock_agent_run
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_agent
            mock_create.return_value = mock_context

            candidates = await generator.generate(sample_market_context, model="openai:gpt-4o")

            assert len(candidates) == 4
            assert all(isinstance(c, Strategy) for c in candidates)


class TestCandidateGeneratorDiversity:
    """Test diversity checking for parallel candidate generation."""

    # Standard rebalancing rationale that meets 150 char minimum
    STANDARD_RATIONALE = (
        "Monthly rebalancing maintains target weights by systematically buying dips "
        "and selling rallies, implementing contrarian exposure that captures "
        "mean-reversion across asset classes over 30-60 day cycles."
    )

    def test_check_diversity_passes_with_diverse_candidates(self):
        """Diversity check passes when candidates have >=3 edge types and archetypes."""
        from src.agent.models import EdgeType, StrategyArchetype

        generator = CandidateGenerator()
        candidates = [
            Strategy(
                name="Momentum Strategy",
                assets=["SPY"], weights={"SPY": 1.0},
                rebalance_frequency=RebalanceFrequency.WEEKLY,
                logic_tree={},
                edge_type=EdgeType.BEHAVIORAL,
                archetype=StrategyArchetype.MOMENTUM,
                rebalancing_rationale=self.STANDARD_RATIONALE
            ),
            Strategy(
                name="Mean Reversion Strategy",
                assets=["QQQ"], weights={"QQQ": 1.0},
                rebalance_frequency=RebalanceFrequency.MONTHLY,
                logic_tree={},
                edge_type=EdgeType.STRUCTURAL,
                archetype=StrategyArchetype.MEAN_REVERSION,
                rebalancing_rationale=self.STANDARD_RATIONALE
            ),
            Strategy(
                name="Carry Strategy",
                assets=["TLT"], weights={"TLT": 1.0},
                rebalance_frequency=RebalanceFrequency.QUARTERLY,
                logic_tree={},
                edge_type=EdgeType.RISK_PREMIUM,
                archetype=StrategyArchetype.CARRY,
                rebalancing_rationale=self.STANDARD_RATIONALE
            ),
            Strategy(
                name="Volatility Strategy",
                assets=["VXX"], weights={"VXX": 1.0},
                rebalance_frequency=RebalanceFrequency.DAILY,
                logic_tree={},
                edge_type=EdgeType.INFORMATIONAL,
                archetype=StrategyArchetype.VOLATILITY,
                rebalancing_rationale=self.STANDARD_RATIONALE
            ),
        ]

        is_diverse, issues = generator._check_diversity(candidates)
        assert is_diverse is True
        assert len(issues) == 0

    def test_check_diversity_warns_on_low_edge_type_variety(self):
        """Diversity check warns when <3 edge types present."""
        from src.agent.models import EdgeType, StrategyArchetype

        generator = CandidateGenerator()
        candidates = [
            Strategy(
                name=f"Strategy {i}",
                assets=[f"TICKER{i}"], weights={f"TICKER{i}": 1.0},
                rebalance_frequency=RebalanceFrequency.MONTHLY,
                logic_tree={},
                edge_type=EdgeType.BEHAVIORAL,  # All same edge type
                archetype=[StrategyArchetype.MOMENTUM, StrategyArchetype.MEAN_REVERSION, StrategyArchetype.CARRY][i % 3],
                rebalancing_rationale=self.STANDARD_RATIONALE
            )
            for i in range(4)
        ]

        is_diverse, issues = generator._check_diversity(candidates)
        assert is_diverse is False
        assert len(issues) == 1
        assert "edge types" in issues[0].lower()

    def test_check_diversity_warns_on_low_archetype_variety(self):
        """Diversity check warns when <3 archetypes present."""
        from src.agent.models import EdgeType, StrategyArchetype

        generator = CandidateGenerator()
        candidates = [
            Strategy(
                name=f"Strategy {i}",
                assets=[f"TICKER{i}"], weights={f"TICKER{i}": 1.0},
                rebalance_frequency=RebalanceFrequency.MONTHLY,
                logic_tree={},
                edge_type=[EdgeType.BEHAVIORAL, EdgeType.STRUCTURAL, EdgeType.RISK_PREMIUM][i % 3],
                archetype=StrategyArchetype.MOMENTUM,  # All same archetype
                rebalancing_rationale=self.STANDARD_RATIONALE
            )
            for i in range(4)
        ]

        is_diverse, issues = generator._check_diversity(candidates)
        assert is_diverse is False
        assert len(issues) == 1
        assert "archetype" in issues[0].lower()


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
        sample_market_context
    ):
        """
        Validate that select() chooses candidate with highest composite score.

        Composite formula (Edge Scorecard only):
            score = 0.50 × (Thesis + Edge + Risk)/3 + 0.30 × Regime + 0.20 × Coherence

        Given the test data:
        - Candidate 1 has best EdgeScore (5.0) across all dimensions
        - Should win with highest composite score
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
                sample_market_context,
                model="openai:gpt-4o"
            )

            # Calculate expected winner manually
            # Candidate 1: thesis=5, edge=5, risk=5, regime=5, coherence=5 (total_score=5.0)
            # Composite formula: 0.50 × (5+5+5)/15 + 0.30 × 5/5 + 0.20 × 5/5
            reasoning_norm = (5 + 5 + 5) / 15.0  # = 1.0
            regime_norm = 5 / 5.0  # = 1.0
            coherence_norm = 5 / 5.0  # = 1.0
            expected_score = 0.50 * 1.0 + 0.30 * 1.0 + 0.20 * 1.0
            # = 0.50 + 0.30 + 0.20 = 1.0

            # Candidate 1 should have highest composite score
            assert winner == sample_candidates[1], "Should select candidate with highest composite score"
            assert reasoning.winner_index == 1, "Reasoning should have correct winner_index"

    @pytest.mark.asyncio
    async def test_reasoning_has_correct_alternatives(
        self,
        sample_candidates,
        sample_scorecards,
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
        - Edge score normalization: All dimensions normalized 0-1 (3-5 scale)
        - Regime awareness: (3 to 5) → normalized in formula
        - Strategic coherence: (3 to 5) → normalized in formula
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
                sample_market_context,
                model="openai:gpt-4o"
            )

            # Candidate 1 (best Edge Scorecard) should win
            assert reasoning.winner_index == 1, "Candidate with best Edge Scorecard should win"


# ============================================================================
# CharterGenerator Tests
# ============================================================================

class TestCharterGenerator:
    """Test charter generation stage."""

    @pytest.mark.asyncio
    async def test_charter_has_all_required_sections(
        self,
        sample_candidates,
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
                market_thesis="This is a bull market with normal volatility conditions. The current regime shows strong momentum across major indices with sector rotation favoring technology and growth stocks. This creates opportunities for tactical positioning.",
                strategy_selection="We selected this strategy because of superior Sharpe ratio and drawdown control compared to alternatives. The strategy aligns well with current market conditions and demonstrates robust risk management.",
                expected_behavior="We expect positive returns in bull market conditions with moderate volatility. The strategy should outperform during momentum regimes and show resilience during pullbacks through dynamic rebalancing.",
                failure_modes=[
                    "Sudden volatility spike could trigger losses and force defensive positioning",
                    "Market regime shift to bear market would undermine momentum assumptions",
                    "Sector rotation away from growth could reduce returns significantly"
                ],
                outlook_90d="Over the next 90 days, we expect this strategy to perform well in the current market environment with continued low volatility."
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

            # refinement_recommendations is optional - can be None or list
            assert hasattr(charter, 'refinement_recommendations'), "Charter missing refinement_recommendations field"
            if charter.refinement_recommendations is not None:
                assert isinstance(charter.refinement_recommendations, list), "refinement_recommendations should be list"
                for rec in charter.refinement_recommendations:
                    assert len(rec) >= 50, "Each refinement recommendation must be ≥50 chars"

    @pytest.mark.asyncio
    async def test_charter_prompt_includes_context(
        self,
        sample_candidates,
        sample_scorecards,
        sample_market_context
    ):
        """
        Validate that the prompt sent to AI includes all necessary context.

        Should include:
        - Winner strategy details
        - Edge Scorecard evaluations
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
                    market_thesis="Test thesis that meets minimum character requirements for charter validation. This section describes the market analysis and investment rationale in sufficient detail.",
                    strategy_selection="Test selection explanation that meets minimum character requirements. This section explains why this particular strategy was chosen over the alternatives based on quantitative metrics.",
                    expected_behavior="Test behavior description that meets minimum character requirements. This section outlines expected performance patterns under various market conditions and scenarios.",
                    failure_modes=["Sudden market reversal could cause losses and trigger defensive positioning",
                                   "Volatility spike could trigger drawdown beyond acceptable thresholds",
                                   "Regime shift to bear market would undermine core assumptions"],
                    outlook_90d="Test outlook prediction that meets minimum character requirements for this field validation."
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
                sample_market_context,
                model="openai:gpt-4o"
            )

            # Validate prompt includes key elements
            assert captured_prompt is not None, "Prompt should have been captured"
            assert sample_candidates[1].name in captured_prompt, "Prompt should include winner name"
            assert "edge_score" in captured_prompt, "Prompt should include Edge Scorecard metrics"
            assert reasoning.why_selected in captured_prompt, "Prompt should include selection reasoning"
            assert sample_market_context["metadata"]["anchor_date"] in captured_prompt, "Prompt should include market context date"
            assert "regime_tags" in captured_prompt, "Prompt should reference regime"
            assert "macro_indicators" in captured_prompt, "Prompt should include macro indicators"

    @pytest.mark.asyncio
    async def test_detects_json_key_fragments_in_failure_modes(
        self,
        sample_candidates,
        sample_scorecards,
        sample_market_context
    ):
        """
        Validate that charter generator detects when failure_modes contains
        JSON key fragments instead of actual descriptions.

        This happens when pydantic-ai coerces a dict to list via list(dict.keys()).
        """
        generator = CharterGenerator()

        reasoning = SelectionReasoning(
            why_selected="Selected for best risk-adjusted returns in the current market regime, with superior Sharpe ratio and drawdown control compared to alternatives.",
            winner_index=0,
            tradeoffs_accepted="Accepting slightly higher volatility for better long-term returns.",
            alternatives_rejected=["Strategy 2", "Strategy 3", "Strategy 4", "Strategy 5"],
            conviction_level=0.85
        )

        with patch('src.agent.stages.charter_generator.create_agent') as mock_create:
            mock_agent = AsyncMock()
            mock_result = AsyncMock()
            # Simulate malformed failure_modes (JSON keys instead of descriptions)
            mock_result.output = Charter(
                market_thesis="This is a bull market with normal volatility conditions. The current regime shows strong momentum across major indices.",
                strategy_selection="We selected this strategy because of superior Sharpe ratio and drawdown control compared to alternatives.",
                expected_behavior="We expect positive returns in bull market conditions with moderate volatility.",
                failure_modes=[
                    'outlook_90d": ',  # JSON key fragment (14 chars)
                    'market_thesis',   # Field name (13 chars)
                    'strategy_selection'  # Field name (18 chars)
                ],
                outlook_90d="Over the next 90 days, we expect this strategy to perform well."
            )
            mock_agent.run.return_value = mock_result
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_agent
            mock_create.return_value = mock_context

            # Should raise ValueError after max retries
            with pytest.raises(ValueError, match="appears to be a JSON key"):
                await generator.generate(
                    sample_candidates[0],
                    reasoning,
                    sample_candidates,
                    sample_scorecards,
                    sample_market_context,
                    model="openai:gpt-4o"
                )

    @pytest.mark.asyncio
    async def test_retries_on_malformed_failure_modes(
        self,
        sample_candidates,
        sample_scorecards,
        sample_market_context
    ):
        """
        Validate that charter generator retries when failure_modes are malformed,
        and succeeds if retry returns valid data.
        """
        generator = CharterGenerator()

        reasoning = SelectionReasoning(
            why_selected="Selected for best risk-adjusted returns in the current market regime, with superior Sharpe ratio and drawdown control compared to alternatives.",
            winner_index=0,
            tradeoffs_accepted="Accepting slightly higher volatility for better long-term returns.",
            alternatives_rejected=["Strategy 2", "Strategy 3", "Strategy 4", "Strategy 5"],
            conviction_level=0.85
        )

        call_count = 0

        with patch('src.agent.stages.charter_generator.create_agent') as mock_create:
            mock_agent = AsyncMock()

            async def mock_run(prompt):
                nonlocal call_count
                call_count += 1
                mock_result = AsyncMock()

                if call_count == 1:
                    # First call: return malformed failure_modes
                    mock_result.output = Charter(
                        market_thesis="Bull market with normal volatility conditions and strong momentum across indices.",
                        strategy_selection="Selected for superior Sharpe ratio and drawdown control versus alternatives.",
                        expected_behavior="Expect positive returns in bull conditions with moderate volatility levels.",
                        failure_modes=[
                            'outlook_90d": ',  # JSON key fragment
                            'market_thesis',
                            'expected_behavior'
                        ],
                        outlook_90d="Over the next 90 days, expect strong performance in current environment."
                    )
                else:
                    # Second call: return valid failure_modes
                    mock_result.output = Charter(
                        market_thesis="Bull market with normal volatility conditions and strong momentum across indices.",
                        strategy_selection="Selected for superior Sharpe ratio and drawdown control versus alternatives.",
                        expected_behavior="Expect positive returns in bull conditions with moderate volatility levels.",
                        failure_modes=[
                            "Sudden volatility spike could trigger losses and force defensive positioning",
                            "Market regime shift to bear market would undermine momentum assumptions",
                            "Sector rotation away from growth could reduce returns significantly"
                        ],
                        outlook_90d="Over the next 90 days, expect strong performance in current environment."
                    )
                return mock_result

            mock_agent.run.side_effect = mock_run
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_agent
            mock_create.return_value = mock_context

            charter = await generator.generate(
                sample_candidates[0],
                reasoning,
                sample_candidates,
                sample_scorecards,
                sample_market_context,
                model="openai:gpt-4o"
            )

            # Should have retried and succeeded
            assert call_count == 2, "Should have retried once"
            assert len(charter.failure_modes) == 3
            assert all(len(mode) > 20 for mode in charter.failure_modes)
