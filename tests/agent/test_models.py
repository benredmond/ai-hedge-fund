"""
Tests for Pydantic models (Strategy and Charter).
Following TDD: Write tests first, then implement models.
"""

import pytest
from pydantic import ValidationError


class TestStrategyModel:
    """Test Strategy model validation"""

    def test_valid_strategy_accepted(self):
        """Valid strategy with all required fields passes validation"""
        from src.agent.models import Strategy

        strategy = Strategy(
            name="60/40 Portfolio",
            assets=["SPY", "AGG"],
            weights={"SPY": 0.6, "AGG": 0.4},
            rebalance_frequency="monthly",
            logic_tree={}
        )

        assert strategy.name == "60/40 Portfolio"
        assert len(strategy.assets) == 2
        assert sum(strategy.weights.values()) == pytest.approx(1.0)

    def test_empty_assets_rejected(self):
        """Strategy with empty assets list fails validation"""
        from src.agent.models import Strategy

        with pytest.raises(ValidationError, match="at least 1 item"):
            Strategy(
                name="Empty Strategy",
                assets=[],
                weights={},
                rebalance_frequency="monthly",
                logic_tree={}
            )

    def test_weights_must_sum_to_one(self):
        """Strategy weights must sum to 1.0 within tolerance"""
        from src.agent.models import Strategy

        # Too low
        with pytest.raises(ValidationError, match="sum to"):
            Strategy(
                name="Incomplete",
                assets=["SPY"],
                weights={"SPY": 0.5},
                rebalance_frequency="monthly",
                logic_tree={}
            )

        # Too high
        with pytest.raises(ValidationError, match="sum to"):
            Strategy(
                name="Overweight",
                assets=["SPY"],
                weights={"SPY": 1.5},
                rebalance_frequency="monthly",
                logic_tree={}
            )

    def test_weights_tolerance_accepted(self):
        """Weights within 0.99-1.01 are accepted with normalization"""
        from src.agent.models import Strategy

        # Slightly under 1.0 (acceptable)
        strategy = Strategy(
            name="Slightly Under",
            assets=["SPY", "AGG"],
            weights={"SPY": 0.595, "AGG": 0.40},  # Sums to 0.995
            rebalance_frequency="monthly",
            logic_tree={}
        )
        assert sum(strategy.weights.values()) == pytest.approx(1.0, abs=0.01)

    def test_weights_missing_asset(self):
        """Weights must include all assets"""
        from src.agent.models import Strategy

        with pytest.raises(ValidationError, match="cover all assets"):
            Strategy(
                name="Missing Weight",
                assets=["SPY", "QQQ", "AGG"],
                weights={"SPY": 0.6, "QQQ": 0.4},  # AGG missing
                rebalance_frequency="monthly",
                logic_tree={}
            )

    def test_weights_extra_asset(self):
        """Weights cannot include assets not in assets list"""
        from src.agent.models import Strategy

        with pytest.raises(ValidationError, match="cover all assets"):
            Strategy(
                name="Extra Weight",
                assets=["SPY"],
                weights={"SPY": 0.7, "QQQ": 0.3},  # QQQ not in assets
                rebalance_frequency="monthly",
                logic_tree={}
            )

    def test_rebalance_frequency_enum(self):
        """Rebalance frequency must be valid enum value"""
        from src.agent.models import Strategy

        # Valid values
        for freq in ["daily", "weekly", "monthly"]:
            strategy = Strategy(
                name="Test",
                assets=["SPY"],
                weights={"SPY": 1.0},
                rebalance_frequency=freq,
                logic_tree={}
            )
            assert strategy.rebalance_frequency == freq

        # Invalid value
        with pytest.raises(ValidationError):
            Strategy(
                name="Test",
                assets=["SPY"],
                weights={"SPY": 1.0},
                rebalance_frequency="every_tuesday",
                logic_tree={}
            )


class TestCharterModel:
    """Test Charter model validation"""

    def test_valid_charter_accepted(self):
        """Valid charter with all required fields passes validation"""
        from src.agent.models import Charter

        charter = Charter(
            market_thesis="Bull market driven by AI adoption",
            strategy_selection="Selected 60/40 for risk-adjusted returns",
            expected_behavior="Outperform in rising markets, lag in bear markets",
            failure_modes=["Bond yields spike above 6%", "AI bubble bursts"],
            outlook_90d="Expect 5-10% returns over next 90 days"
        )

        assert "AI adoption" in charter.market_thesis
        assert len(charter.failure_modes) >= 2

    def test_empty_failure_modes_rejected(self):
        """Charter must have at least one failure mode"""
        from src.agent.models import Charter

        with pytest.raises(ValidationError, match="at least 1"):
            Charter(
                market_thesis="Test thesis",
                strategy_selection="Test selection",
                expected_behavior="Test behavior",
                failure_modes=[],  # Empty list not allowed
                outlook_90d="Test outlook"
            )

    def test_required_fields_present(self):
        """Charter requires all fields to be non-empty strings"""
        from src.agent.models import Charter

        # Missing market_thesis
        with pytest.raises(ValidationError):
            Charter(
                market_thesis="",  # Empty string
                strategy_selection="Selection",
                expected_behavior="Behavior",
                failure_modes=["Failure"],
                outlook_90d="Outlook"
            )

    def test_failure_modes_minimum_length(self):
        """Each failure mode must be meaningful (min 10 chars)"""
        from src.agent.models import Charter

        # Too short failure mode
        with pytest.raises(ValidationError, match="at least 10 characters"):
            Charter(
                market_thesis="This is a valid thesis with enough characters",
                strategy_selection="This is a valid selection rationale",
                expected_behavior="This is valid expected behavior description",
                failure_modes=["Bad"],  # Too short
                outlook_90d="This is a valid 90-day outlook"
            )

        # Just long enough
        charter = Charter(
            market_thesis="This is a valid thesis with enough characters",
            strategy_selection="This is a valid selection rationale",
            expected_behavior="This is valid expected behavior description",
            failure_modes=["Market crash occurs"],  # 19 chars, valid
            outlook_90d="This is a valid 90-day outlook"
        )
        assert len(charter.failure_modes) == 1


class TestEdgeScorecardModel:
    """Test EdgeScorecard model validation"""

    def test_valid_scorecard_accepted(self):
        """Valid scorecard with all dimensions 3-5 passes validation"""
        from src.agent.models import EdgeScorecard

        scorecard = EdgeScorecard(
            thesis_quality=4,
            edge_economics=3,
            risk_framework=3,
            regime_awareness=5,
            strategic_coherence=4
        )

        assert scorecard.thesis_quality == 4
        assert scorecard.total_score == pytest.approx(3.8, abs=0.01)

    def test_dimension_below_threshold_rejected(self):
        """Any dimension below 3 fails validation"""
        from src.agent.models import EdgeScorecard

        with pytest.raises(ValidationError, match="minimum threshold is 3"):
            EdgeScorecard(
                thesis_quality=2,  # Below threshold
                edge_economics=3,
                risk_framework=4,
                regime_awareness=3,
                strategic_coherence=3
            )

    def test_dimension_above_max_rejected(self):
        """Dimensions cannot exceed 5"""
        from src.agent.models import EdgeScorecard

        with pytest.raises(ValidationError):
            EdgeScorecard(
                thesis_quality=6,  # Above maximum
                edge_economics=4,
                risk_framework=4,
                regime_awareness=3,
                strategic_coherence=3
            )

    def test_total_score_calculation(self):
        """total_score property calculates average correctly"""
        from src.agent.models import EdgeScorecard

        scorecard = EdgeScorecard(
            thesis_quality=3,
            edge_economics=3,
            risk_framework=3,
            regime_awareness=3,
            strategic_coherence=3
        )
        assert scorecard.total_score == 3.0

        scorecard2 = EdgeScorecard(
            thesis_quality=5,
            edge_economics=5,
            risk_framework=5,
            regime_awareness=5,
            strategic_coherence=5
        )
        assert scorecard2.total_score == 5.0


class TestSelectionReasoningModel:
    """Test SelectionReasoning model validation"""

    def test_valid_reasoning_accepted(self):
        """Valid selection reasoning passes validation"""
        from src.agent.models import SelectionReasoning

        reasoning = SelectionReasoning(
            winner_index=2,
            why_selected="This strategy was selected because it has the highest Sharpe ratio (2.1) combined with excellent regime alignment and low drawdown risk.",
            tradeoffs_accepted="Accepting higher short-term volatility for superior risk-adjusted returns over the full evaluation period",
            alternatives_rejected=["Strategy A", "Strategy B", "Strategy C", "Strategy D"],
            conviction_level=0.85
        )

        assert reasoning.winner_index == 2
        assert len(reasoning.alternatives_rejected) == 4

    def test_winner_index_out_of_range_rejected(self):
        """Winner index must be 0-4"""
        from src.agent.models import SelectionReasoning

        with pytest.raises(ValidationError):
            SelectionReasoning(
                winner_index=5,  # Out of range
                why_selected="This strategy was selected for its superior risk-adjusted returns and alignment with current market regime.",
                tradeoffs_accepted="Minimal tradeoffs given strong alignment across all dimensions",
                alternatives_rejected=["A", "B", "C", "D"],
                conviction_level=0.9
            )

    def test_why_selected_too_short_rejected(self):
        """why_selected must be at least 100 chars"""
        from src.agent.models import SelectionReasoning

        with pytest.raises(ValidationError):
            SelectionReasoning(
                winner_index=0,
                why_selected="Good strategy.",  # Too short
                tradeoffs_accepted="Accepting standard market beta exposure for simplicity",
                alternatives_rejected=["A", "B", "C", "D"],
                conviction_level=0.7
            )

    def test_alternatives_wrong_count_rejected(self):
        """Must have exactly 4 alternatives"""
        from src.agent.models import SelectionReasoning

        # Too few
        with pytest.raises(ValidationError):
            SelectionReasoning(
                winner_index=0,
                why_selected="This strategy was selected because it has the highest Sharpe ratio combined with excellent regime alignment.",
                tradeoffs_accepted="Standard tradeoffs between return and risk apply here",
                alternatives_rejected=["A", "B"],  # Only 2
                conviction_level=0.8
            )

        # Too many
        with pytest.raises(ValidationError):
            SelectionReasoning(
                winner_index=0,
                why_selected="This strategy was selected because it has the highest Sharpe ratio combined with excellent regime alignment.",
                tradeoffs_accepted="Standard tradeoffs between return and risk apply here",
                alternatives_rejected=["A", "B", "C", "D", "E"],  # 5 is too many
                conviction_level=0.8
            )


class TestWorkflowResultModel:
    """Test WorkflowResult model validation"""

    def test_valid_workflow_result_accepted(self):
        """Valid workflow result with all fields passes validation"""
        from src.agent.models import WorkflowResult, Strategy, Charter, EdgeScorecard, SelectionReasoning

        # Create 5 candidates
        candidates = [
            Strategy(
                name=f"Strategy {i+1}",
                assets=["SPY", "AGG"],
                weights={"SPY": 0.6, "AGG": 0.4},
                rebalance_frequency="monthly"
            )
            for i in range(5)
        ]

        # Create scorecards
        scorecards = [
            EdgeScorecard(
                thesis_quality=3,
                edge_economics=4,
                risk_framework=3,
                regime_awareness=3,
                strategic_coherence=4
            )
            for _ in range(5)
        ]

        # Create charter
        charter = Charter(
            market_thesis="Strong bull market with AI adoption driving growth",
            strategy_selection="Selected for best risk-adjusted returns",
            expected_behavior="Outperform in rising markets, moderate downside protection",
            failure_modes=["VIX spikes above 30", "Fed pivots hawkish"],
            outlook_90d="Expect continued uptrend with potential 5-10% gains"
        )

        # Create reasoning
        reasoning = SelectionReasoning(
            winner_index=0,
            why_selected="This strategy achieved the best composite score combining Edge Scorecard dimensions across thesis quality, edge economics, risk framework, regime awareness, and strategic coherence metrics for optimal regime fit.",
            tradeoffs_accepted="Accepting moderate sector concentration for stronger momentum exposure",
            alternatives_rejected=["Strategy 2", "Strategy 3", "Strategy 4", "Strategy 5"],
            conviction_level=0.82
        )

        # Create workflow result
        result = WorkflowResult(
            strategy=candidates[0],
            charter=charter,
            all_candidates=candidates,
            scorecards=scorecards,
            selection_reasoning=reasoning
        )

        assert len(result.all_candidates) == 5

    def test_exactly_five_candidates_enforced(self):
        """Must have exactly 5 candidates"""
        from src.agent.models import WorkflowResult, Strategy, Charter, EdgeScorecard, SelectionReasoning

        # Create 3 candidates (wrong count)
        candidates = [
            Strategy(
                name=f"Strategy {i+1}",
                assets=["SPY"],
                weights={"SPY": 1.0},
                rebalance_frequency="monthly"
            )
            for i in range(3)
        ]

        charter = Charter(
            market_thesis="Test thesis",
            strategy_selection="Test selection",
            expected_behavior="Test behavior",
            failure_modes=["Test failure mode"],
            outlook_90d="Test outlook"
        )

        reasoning = SelectionReasoning(
            winner_index=0,
            why_selected="This is test reasoning with enough characters to pass validation requirements for the minimum length of 100 characters.",
            tradeoffs_accepted="Minimal tradeoffs for this test case scenario validation",
            alternatives_rejected=["A", "B", "C", "D"],
            conviction_level=0.75
        )

        with pytest.raises(ValidationError, match="at least 5 items"):
            WorkflowResult(
                strategy=candidates[0],
                charter=charter,
                all_candidates=candidates,  # Only 3
                scorecards=[],
                selection_reasoning=reasoning
            )

