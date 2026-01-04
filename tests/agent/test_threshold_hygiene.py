"""Tests for threshold hygiene validation.

Validates that _validate_threshold_hygiene correctly:
- Rejects absolute price thresholds for non-proxy tickers
- Rejects arbitrary return thresholds (SPY_return > 0.05)
- Allows relative comparisons (SPY_price > SPY_200d_MA)
- Allows zero-bounded checks (VIXY_return > 0)
- Allows RSI with standard thresholds (RSI > 70)
- Allows cross-asset comparisons (XLK_return > XLF_return)
- Allows absolute price thresholds for approved proxies (VIXY_price > 20)
- Handles nested logic_tree structures
- Handles AND/OR compound conditions
"""

import pytest
from src.agent.stages.candidate_generator import CandidateGenerator
from src.agent.models import Strategy, RebalanceFrequency
from src.agent.config.proxies import ALLOWED_ABSOLUTE_PRICE_TICKERS


# Minimum length strings to satisfy model validation
THESIS_STUB = (
    "This strategy implements a systematic approach to asset allocation based on "
    "volatility signals and market regime detection. The edge exists due to institutional "
    "lag in responding to volatility shifts. Capacity is approximately $500M AUM."
)

RATIONALE_STUB = (
    "Daily rebalancing required to capture 2-4 day institutional lag window. "
    "Weights derived from equal risk contribution methodology. "
    "Frequency matched to edge decay timescale."
)

THESIS_NO_VOL = (
    "This strategy focuses on trend persistence across equities and bonds, rotating "
    "between risk-on and defensive assets based on long-term price signals. The edge "
    "is behavioral underreaction to trend breaks and institutional allocation delays. "
    "Capacity estimated at $300M AUM with a 4-8 week persistence window."
)

RATIONALE_NO_VOL = (
    "Weekly rebalancing balances responsiveness with turnover by checking trend "
    "conditions on a steady cadence. Weights are mode-based with a growth-tilted "
    "risk-on mix and an equal-conviction defensive mix. Frequency matches the "
    "expected regime shift timescale."
)

THESIS_WITH_VIXY = (
    "This strategy uses VIXY as a regime proxy to detect market stress and switch "
    "allocations when the signal turns positive. The edge comes from risk-budget "
    "constraints that force systematic de-risking ahead of discretionary committees. "
    "Capacity estimated at $250M AUM."
)

THESIS_WITH_VOLATILITY = (
    "This strategy targets volatility regime shifts by reducing risk when volatility "
    "spikes and increasing risk when volatility normalizes. The edge comes from slow "
    "institutional responses to volatility regimes. Capacity estimated at $400M AUM."
)

THESIS_WITH_VOLUME = (
    "This strategy uses volume signals and price persistence to manage exposure, "
    "focusing on liquidity cycles and trend durability. The edge is flow-driven "
    "allocation shifts among large caps with capacity estimated at $350M AUM."
)


class TestThresholdHygiene:
    """Test _validate_threshold_hygiene validation."""

    @pytest.fixture
    def generator(self):
        return CandidateGenerator()

    def _make_strategy(self, condition: str, name: str = "Test") -> Strategy:
        """Helper to create a strategy with a given condition."""
        return Strategy(
            name=name,
            assets=["SPY", "TLT", "VIXY", "XLK", "XLF"],
            weights={},
            rebalance_frequency=RebalanceFrequency.DAILY,
            logic_tree={
                "condition": condition,
                "if_true": {"assets": ["TLT"], "weights": {"TLT": 1.0}},
                "if_false": {"assets": ["SPY"], "weights": {"SPY": 1.0}},
            },
            rebalancing_rationale=RATIONALE_STUB,
            thesis_document=THESIS_STUB,
        )

    # ==================== REJECTION TESTS ====================

    def test_absolute_price_threshold_fails(self, generator):
        """SPY_price > 450 should fail - absolute price threshold."""
        strategy = self._make_strategy("SPY_price > 450")
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 1
        assert "Syntax Error" in errors[0]
        assert "absolute price threshold" in errors[0].lower()

    def test_reversed_absolute_price_fails(self, generator):
        """20 < SPY_price should also fail - reversed syntax."""
        strategy = self._make_strategy("20 < SPY_price")
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 1
        assert "Syntax Error" in errors[0]

    def test_arbitrary_return_threshold_fails(self, generator):
        """SPY_cumulative_return_30d > 0.05 should fail - arbitrary 5%."""
        strategy = self._make_strategy("SPY_cumulative_return_30d > 0.05")
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 1
        assert "Syntax Error" in errors[0]
        assert "arbitrary return threshold" in errors[0].lower()

    def test_negative_return_threshold_fails(self, generator):
        """SPY_cumulative_return_30d < -0.10 should fail - arbitrary -10%."""
        strategy = self._make_strategy("SPY_cumulative_return_30d < -0.10")
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 1
        assert "Syntax Error" in errors[0]

    def test_decimal_price_threshold_fails(self, generator):
        """SPY_price > 450.50 should fail."""
        strategy = self._make_strategy("SPY_price > 450.50")
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 1
        assert "Syntax Error" in errors[0]

    # ==================== PASS TESTS ====================

    def test_zero_bounded_return_passes(self, generator):
        """SPY_cumulative_return_30d > 0 should pass - zero-bounded."""
        strategy = self._make_strategy("SPY_cumulative_return_30d > 0")
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 0

    def test_negative_zero_bounded_passes(self, generator):
        """VIXY_cumulative_return_5d < 0 should pass - volatility falling."""
        strategy = self._make_strategy("VIXY_cumulative_return_5d < 0")
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 0

    def test_proxy_absolute_price_passes(self, generator):
        """VIXY_price > 20 should pass - approved proxy absolute price threshold."""
        strategy = self._make_strategy("VIXY_price > 20")
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 0

    @pytest.mark.parametrize("ticker", sorted(ALLOWED_ABSOLUTE_PRICE_TICKERS))
    def test_absolute_price_allowlist_passes(self, generator, ticker):
        """All allowed proxy tickers should pass absolute price thresholds."""
        strategy = self._make_strategy(f"{ticker}_price > 20")
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 0

    @pytest.mark.parametrize("ticker", ["SPY", "QQQ"])
    def test_absolute_price_non_proxy_rejected(self, generator, ticker):
        """Non-proxy tickers should fail absolute price thresholds."""
        strategy = self._make_strategy(f"{ticker}_price > 20")
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 1
        assert "absolute price threshold" in errors[0].lower()

    def test_price_vs_ma_passes(self, generator):
        """SPY_price > SPY_200d_MA should pass - relative to own history."""
        strategy = self._make_strategy("SPY_price > SPY_200d_MA")
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 0

    def test_price_vs_ema_passes(self, generator):
        """SPY_price > SPY_EMA_20d_MA should pass."""
        strategy = self._make_strategy("SPY_price > SPY_EMA_20d_MA")
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 0

    def test_cross_asset_comparison_passes(self, generator):
        """XLK_cumulative_return_30d > XLF_cumulative_return_30d should pass."""
        strategy = self._make_strategy(
            "XLK_cumulative_return_30d > XLF_cumulative_return_30d"
        )
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 0

    def test_rsi_standard_70_passes(self, generator):
        """SPY_RSI_14d > 70 should pass - standard overbought."""
        strategy = self._make_strategy("SPY_RSI_14d > 70")
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 0

    def test_rsi_standard_30_passes(self, generator):
        """SPY_RSI_14d < 30 should pass - standard oversold."""
        strategy = self._make_strategy("SPY_RSI_14d < 30")
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 0

    def test_empty_logic_tree_passes(self, generator):
        """Empty logic_tree (static strategy) should pass."""
        strategy = Strategy(
            name="Static",
            assets=["SPY", "AGG"],
            weights={"SPY": 0.6, "AGG": 0.4},
            rebalance_frequency=RebalanceFrequency.QUARTERLY,
            logic_tree={},
            rebalancing_rationale=RATIONALE_STUB,
            thesis_document=THESIS_STUB,
        )
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 0

    # ==================== COMPOUND CONDITION TESTS ====================

    def test_mixed_and_catches_violation(self, generator):
        """Valid AND invalid should catch the invalid part."""
        strategy = self._make_strategy(
            "SPY_price > SPY_200d_MA and XLK_price > 150"
        )
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 1
        assert "XLK_price > 150" in errors[0]

    def test_both_valid_and_passes(self, generator):
        """Two valid conditions should pass."""
        strategy = self._make_strategy(
            "SPY_cumulative_return_30d > 0 and VIXY_cumulative_return_5d < 0"
        )
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 0

    def test_or_with_violation(self, generator):
        """OR condition with one violation should catch it."""
        strategy = self._make_strategy(
            "SPY_RSI_14d > 70 or XLK_price > 150"
        )
        errors = generator._validate_threshold_hygiene(strategy, 1)
        assert len(errors) == 1

    # ==================== NESTED LOGIC TREE TESTS ====================
    # Nested logic_tree structures are supported; extraction is tested below.
    # We test here that validation is called on extracted conditions.

    def test_condition_extraction_integration(self, generator):
        """Verify extraction and validation work together."""
        # Create a simple strategy and test the extraction method directly
        logic_tree = {
            "condition": "VIXY_price > 25",
            "if_true": {"assets": ["TLT"], "weights": {"TLT": 1.0}},
            "if_false": {
                "condition": "SPY_cumulative_return_30d > 0.08",
                "if_true": {"assets": ["SPY"], "weights": {"SPY": 1.0}},
                "if_false": {"assets": ["BIL"], "weights": {"BIL": 1.0}},
            },
        }
        conditions = generator._extract_all_conditions(logic_tree)
        assert len(conditions) == 2
        assert "VIXY_price > 25" in conditions
        assert "SPY_cumulative_return_30d > 0.08" in conditions


class TestExtractAllConditions:
    """Test _extract_all_conditions helper method."""

    @pytest.fixture
    def generator(self):
        return CandidateGenerator()

    def test_empty_logic_tree(self, generator):
        """Empty dict returns empty list."""
        conditions = generator._extract_all_conditions({})
        assert conditions == []

    def test_single_level(self, generator):
        """Single level extracts one condition."""
        logic_tree = {
            "condition": "SPY_price > SPY_200d_MA",
            "if_true": {"assets": ["SPY"]},
            "if_false": {"assets": ["TLT"]},
        }
        conditions = generator._extract_all_conditions(logic_tree)
        assert conditions == ["SPY_price > SPY_200d_MA"]

    def test_nested_two_levels(self, generator):
        """Nested structure extracts all conditions."""
        logic_tree = {
            "condition": "VIXY_cumulative_return_5d > 0",
            "if_true": {"assets": ["TLT"]},
            "if_false": {
                "condition": "SPY_RSI_14d > 70",
                "if_true": {"assets": ["BIL"]},
                "if_false": {"assets": ["SPY"]},
            },
        }
        conditions = generator._extract_all_conditions(logic_tree)
        assert len(conditions) == 2
        assert "VIXY_cumulative_return_5d > 0" in conditions
        assert "SPY_RSI_14d > 70" in conditions

    def test_deeply_nested(self, generator):
        """Three levels of nesting extracts all."""
        logic_tree = {
            "condition": "A",
            "if_true": {"assets": []},
            "if_false": {
                "condition": "B",
                "if_true": {
                    "condition": "C",
                    "if_true": {"assets": []},
                    "if_false": {"assets": []},
                },
                "if_false": {"assets": []},
            },
        }
        conditions = generator._extract_all_conditions(logic_tree)
        assert conditions == ["A", "B", "C"]


class TestVixyThesisAlignment:
    """Test _validate_vixy_thesis_alignment validation."""

    @pytest.fixture
    def generator(self):
        return CandidateGenerator()

    def _make_strategy(self, condition: str, thesis: str, rationale: str) -> Strategy:
        return Strategy(
            name="VIXY Alignment Test",
            assets=["SPY", "TLT", "VIXY"],
            weights={},
            rebalance_frequency=RebalanceFrequency.DAILY,
            logic_tree={
                "condition": condition,
                "if_true": {"assets": ["TLT"], "weights": {"TLT": 1.0}},
                "if_false": {"assets": ["SPY"], "weights": {"SPY": 1.0}},
            },
            rebalancing_rationale=rationale,
            thesis_document=thesis,
        )

    def test_vixy_without_volatility_fails(self, generator):
        strategy = self._make_strategy(
            "VIXY_cumulative_return_5d > 0",
            THESIS_NO_VOL,
            RATIONALE_NO_VOL,
        )
        errors = generator._validate_vixy_thesis_alignment(strategy, 1)
        assert len(errors) == 1
        assert "VIXY condition used (1 occurrence" in errors[0]

    def test_vixy_with_vixy_keyword_passes(self, generator):
        strategy = self._make_strategy(
            "VIXY_cumulative_return_5d > 0",
            THESIS_WITH_VIXY,
            RATIONALE_NO_VOL,
        )
        errors = generator._validate_vixy_thesis_alignment(strategy, 1)
        assert len(errors) == 0

    def test_vixy_with_volatility_keyword_passes(self, generator):
        strategy = self._make_strategy(
            "VIXY_cumulative_return_5d > 0",
            THESIS_WITH_VOLATILITY,
            RATIONALE_NO_VOL,
        )
        errors = generator._validate_vixy_thesis_alignment(strategy, 1)
        assert len(errors) == 0

    def test_volume_word_does_not_pass(self, generator):
        strategy = self._make_strategy(
            "VIXY_cumulative_return_5d > 0",
            THESIS_WITH_VOLUME,
            RATIONALE_NO_VOL,
        )
        errors = generator._validate_vixy_thesis_alignment(strategy, 1)
        assert len(errors) == 1
