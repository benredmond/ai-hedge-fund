"""Tests for CostValidator."""

import pytest

from src.agent.models import Strategy, EdgeType, StrategyArchetype, RebalanceFrequency
from src.agent.validators.cost import CostValidator


def create_test_strategy(
    name: str = "Test Strategy",
    thesis: str = None,
    rebalance_freq: RebalanceFrequency = RebalanceFrequency.QUARTERLY,
) -> Strategy:
    """Create a valid Strategy for testing with minimum viable fields."""
    if thesis is None:
        thesis = (
            "This is a test strategy thesis document that meets the minimum 200 character requirement. "
            "It describes a generic investment approach for testing validation logic without specific details."
        )

    while len(thesis) < 200:
        thesis += " Padding."

    return Strategy(
        name=name,
        thesis_document=thesis,
        rebalancing_rationale=(
            "Rebalancing implements the edge by maintaining target exposure levels. "
            "The rebalancing frequency aligns with the edge timescale, avoiding overtrading costs "
            "while capturing the strategic opportunity effectively."
        ),
        edge_type=EdgeType.BEHAVIORAL,
        archetype=StrategyArchetype.MOMENTUM,
        assets=["EQUITIES::SPY//USD"],
        weights={"EQUITIES::SPY//USD": 1.0},
        logic_tree={},
        rebalance_frequency=rebalance_freq,
    )


class TestCostValidator:
    """Test suite for execution cost validation."""

    def test_daily_rebalancing_without_costs_flagged(self):
        """Daily rebalancing without cost discussion gets suggestion."""
        thesis = (
            "This strategy rotates daily into top momentum stocks to capture short-term trends. "
            "It uses technical indicators for entry and exit signals with systematic rules. "
            "The approach focuses on consistent execution without emotional interference."
        )
        strategy = create_test_strategy(
            name="Daily Momentum",
            thesis=thesis,
            rebalance_freq=RebalanceFrequency.DAILY,
        )

        validator = CostValidator()
        errors = validator.validate(strategy)

        assert len(errors) == 1
        assert "Priority 3 (SUGGESTION)" in errors[0]
        assert "daily" in errors[0].lower()
        assert "execution cost" in errors[0].lower() or "friction" in errors[0].lower()

    def test_weekly_rebalancing_without_costs_flagged(self):
        """Weekly rebalancing without cost discussion gets suggestion."""
        thesis = (
            "This strategy rotates weekly between top 3 sectors based on RSI signals. "
            "It maintains exposure to trending sectors while avoiding overtraded markets. "
            "The systematic approach reduces behavioral biases in sector selection."
        )
        strategy = create_test_strategy(
            name="Weekly Sector Rotation",
            thesis=thesis,
            rebalance_freq=RebalanceFrequency.WEEKLY,
        )

        validator = CostValidator()
        errors = validator.validate(strategy)

        assert len(errors) == 1
        assert "Priority 3 (SUGGESTION)" in errors[0]
        assert "weekly" in errors[0].lower()

    def test_monthly_rebalancing_cost_optional(self):
        """Monthly rebalancing doesn't require cost discussion."""
        thesis = (
            "This strategy rebalances monthly to capture medium-term trends in sector performance. "
            "It uses fundamental and technical signals to identify leadership changes. "
            "The approach balances responsiveness with transaction cost efficiency."
        )
        strategy = create_test_strategy(
            name="Monthly Rebalance",
            thesis=thesis,
            rebalance_freq=RebalanceFrequency.MONTHLY,
        )

        validator = CostValidator()
        errors = validator.validate(strategy)

        # Monthly is not high-frequency, no cost requirement
        assert len(errors) == 0

    def test_quarterly_rebalancing_cost_optional(self):
        """Quarterly rebalancing doesn't require cost discussion."""
        thesis = (
            "This strategy rebalances quarterly based on fundamental valuation signals. "
            "It captures long-term value opportunities with minimal trading activity. "
            "The patient approach allows fundamentals to materialize over time."
        )
        strategy = create_test_strategy(
            name="Quarterly Rebalance",
            thesis=thesis,
            rebalance_freq=RebalanceFrequency.QUARTERLY,
        )

        validator = CostValidator()
        errors = validator.validate(strategy)

        # Quarterly is not high-frequency, no cost requirement
        assert len(errors) == 0

    def test_daily_with_cost_discussion_passes(self):
        """Daily rebalancing WITH cost discussion passes."""
        thesis = (
            "This strategy rotates daily with estimated 200% annual turnover. "
            "Execution costs: 3 bps average spread + 2 bps impact = 5 bps per trade. "
            "Annual friction budget: 200% × 5 bps = 1.0% friction. "
            "Expected gross alpha: 6%, net alpha: 5% after costs."
        )
        strategy = create_test_strategy(
            name="Daily with Costs",
            thesis=thesis,
            rebalance_freq=RebalanceFrequency.DAILY,
        )

        validator = CostValidator()
        errors = validator.validate(strategy)

        # Should pass - has cost discussion (turnover, bps, friction)
        assert len(errors) == 0

    def test_priority_3_suggestion_format(self):
        """Verify error messages use correct Priority 3 format."""
        thesis = "Daily momentum strategy without cost discussion for testing validation error message format."
        strategy = create_test_strategy(
            name="Test Strategy",
            thesis=thesis,
            rebalance_freq=RebalanceFrequency.DAILY,
        )

        validator = CostValidator()
        errors = validator.validate(strategy)

        assert len(errors) >= 1
        assert errors[0].startswith("Priority 3 (SUGGESTION):")
        assert "Test Strategy" in errors[0]
        assert "daily" in errors[0].lower()
