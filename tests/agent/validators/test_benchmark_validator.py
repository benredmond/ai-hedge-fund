"""Tests for BenchmarkValidator."""

import pytest

from src.agent.models import Strategy, EdgeType, StrategyArchetype, RebalanceFrequency
from src.agent.validators.benchmark import BenchmarkValidator


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


class TestBenchmarkValidator:
    """Test suite for benchmark comparison validation."""

    def test_strategy_with_benchmark_and_alpha_passes(self):
        """Strategy with benchmark mention and alpha quantification passes."""
        thesis = (
            "This momentum strategy captures trends vs SPY by rotating into top 3 sectors. "
            "Expected alpha: +150 bps over SPY through factor timing and cash buffer. "
            "The strategy exploits momentum persistence in sector leadership, typically lasting 3-6 months."
        )
        strategy = create_test_strategy(name="Momentum Strategy", thesis=thesis)

        validator = BenchmarkValidator()
        errors = validator.validate(strategy)

        assert len(errors) == 0

    def test_strategy_without_benchmark_flagged(self):
        """Strategy without benchmark comparison gets suggestion."""
        thesis = (
            "This strategy uses momentum signals to rotate between sectors. "
            "It captures trends and avoids drawdowns using technical indicators. "
            "The approach focuses on risk-adjusted returns through dynamic allocation."
        )
        strategy = create_test_strategy(name="Generic Strategy", thesis=thesis)

        validator = BenchmarkValidator()
        errors = validator.validate(strategy)

        assert len(errors) == 1
        assert "Priority 3 (SUGGESTION)" in errors[0]
        assert "benchmark" in errors[0].lower()

    def test_strategy_with_benchmark_no_alpha_suggested(self):
        """Strategy with benchmark but no alpha quantification gets suggestion."""
        thesis = (
            "This strategy compares to SPY by selecting best sectors based on momentum. "
            "It should perform well in trending markets by maintaining exposure to leadership. "
            "The systematic approach reduces emotional decision-making biases."
        )
        strategy = create_test_strategy(name="Sector Strategy", thesis=thesis)

        validator = BenchmarkValidator()
        errors = validator.validate(strategy)

        assert len(errors) == 1
        assert "Priority 3 (SUGGESTION)" in errors[0]
        assert "quantify" in errors[0].lower() or "alpha" in errors[0].lower()

    @pytest.mark.parametrize(
        "benchmark",
        ["SPY", "QQQ", "AGG", "XLF", "60/40", "risk parity"],
    )
    def test_various_benchmarks_recognized(self, benchmark):
        """Test that various benchmarks are recognized."""
        thesis = f"This strategy aims to outperform {benchmark} by 200 bps annually through systematic factor exposure and dynamic risk management techniques."
        strategy = create_test_strategy(name="Test Strategy", thesis=thesis)

        validator = BenchmarkValidator()
        errors = validator.validate(strategy)

        # Should recognize benchmark and see "outperform" + "bps" as alpha quantification
        assert len(errors) == 0

    def test_priority_3_suggestion_format(self):
        """Verify error messages use correct Priority 3 format."""
        thesis = "Generic thesis without benchmarks for testing validation error message format and priority level assignment in the validation framework."
        strategy = create_test_strategy(name="Test Strategy", thesis=thesis)

        validator = BenchmarkValidator()
        errors = validator.validate(strategy)

        assert len(errors) >= 1
        assert errors[0].startswith("Priority 3 (SUGGESTION):")
        assert "Test Strategy" in errors[0]
