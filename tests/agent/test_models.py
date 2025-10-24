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
        for freq in ["daily", "weekly", "monthly", "quarterly"]:
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
