"""Simple tests for leverage validation."""

import pytest
from src.agent.models import Strategy, RebalanceFrequency, EdgeType, StrategyArchetype
from src.agent.stages.candidate_generator import CandidateGenerator


class TestLeverageValidation:

    def test_2x_without_justification_fails(self):
        """2x ETF without justification should trigger retry."""
        generator = CandidateGenerator()

        strategy = Strategy(
            name="2x No Justification",
            assets=["SSO", "AGG"],
            weights={"SSO": 0.70, "AGG": 0.30},
            rebalance_frequency=RebalanceFrequency.WEEKLY,
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.MOMENTUM,
            thesis_document="Momentum strategy using broad market. SSO provides enhanced returns." * 20,
            rebalancing_rationale="Weekly rebalancing." * 10
        )

        errors = generator._validate_leverage_justification(strategy)
        assert len(errors) > 0
        assert any("Priority 2" in err for err in errors)  # Should be retry, not reject
        assert any("convexity" in err.lower() or "leverage" in err.lower() for err in errors)

    def test_3x_without_stress_test_rejected(self):
        """3x ETF without stress test should be hard rejected."""
        generator = CandidateGenerator()

        strategy = Strategy(
            name="3x No Stress Test",
            assets=["TQQQ"],
            weights={"TQQQ": 1.0},
            rebalance_frequency=RebalanceFrequency.DAILY,
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.MOMENTUM,
            thesis_document=(
                "Tech momentum with 3x. Convexity: faster capture. "
                "Decay: 3% annually. Drawdown: -50% to -60%. "
                "Benchmark: TQQQ vs QQQ for momentum."
                # Missing stress test and exit criteria
            ) * 10,
            rebalancing_rationale="Daily momentum." * 10
        )

        errors = generator._validate_leverage_justification(strategy)
        assert len(errors) > 0
        assert any("Priority 1" in err and "HARD REJECT" in err for err in errors)
        assert any("stress" in err.lower() or "2022" in err or "2020" in err for err in errors)

    def test_unleveraged_passes(self):
        """Unleveraged strategy should pass leverage validation."""
        generator = CandidateGenerator()

        strategy = Strategy(
            name="Unleveraged Conservative",
            assets=["SPY", "AGG", "QQQ"],
            weights={"SPY": 0.50, "AGG": 0.30, "QQQ": 0.20},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            edge_type=EdgeType.STRUCTURAL,
            archetype=StrategyArchetype.CARRY,
            thesis_document="Diversified unleveraged portfolio." * 20,
            rebalancing_rationale="Monthly rebalancing." * 10
        )

        errors = generator._validate_leverage_justification(strategy)
        assert len(errors) == 0  # No leverage, should pass

    def test_3x_with_complete_justification_passes(self):
        """3x ETF with all 6 elements should pass validation."""
        generator = CandidateGenerator()

        strategy = Strategy(
            name="3x AI Infrastructure Momentum (Comprehensive)",
            assets=["TQQQ", "QQQ", "BIL"],
            weights={"TQQQ": 0.50, "QQQ": 0.30, "BIL": 0.20},
            rebalance_frequency=RebalanceFrequency.WEEKLY,
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.MOMENTUM,
            thesis_document="""AI infrastructure momentum persists 2-4 weeks (supply chain order lag) before mean-reversion. TQQQ captures momentum spike 3x faster than QQQ before 30+ day decay threshold. This convexity advantage amplifies short-term edge window. TQQQ decays 3-5% annually in sideways markets (daily rebalancing friction). Edge target: 20-28% alpha vs QQQ, justifying decay cost 6-9x. 2022 rate shock: TQQQ -80% vs QQQ -35%. Expected max drawdown: -50% to -65%. Realistic pessimistic scenario accounts for non-linear amplification. Benchmark: TQQQ vs QQQ targeting +18-24% alpha after decay costs. Why not QQQ? Unleveraged misses 2-4w momentum amplification window. 2020 COVID: TQQQ -75% in 30 days. Exit at VIX>30 limits exposure to ~-35%. 2022 analog: Exit when 3m momentum negative avoids June-Oct decline. Exit criteria: Rotate to BIL if VIX>30 for 5+ days OR NASDAQ 3m momentum<0 OR AI CapEx growth <15% YoY OR position down -30% from peak.""",
            rebalancing_rationale="""Weekly rebalancing captures 2-4 week momentum edge while limiting decay exposure. VIX-based conditional allocation rotates to cash when volatility spikes. Weights: TQQQ 50% (high conviction), QQQ 30% (unleveraged anchor), BIL 20% (cash buffer)."""
        )

        errors = generator._validate_leverage_justification(strategy)
        # Should pass all 6 elements
        assert len(errors) == 0, f"Expected no errors but got: {errors}"

    def test_2x_with_complete_justification_passes(self):
        """2x ETF with all 4 core elements should pass validation."""
        generator = CandidateGenerator()

        strategy = Strategy(
            name="2x Sector Momentum Rotation",
            assets=["SSO", "QLD", "AGG"],
            weights={"SSO": 0.40, "QLD": 0.35, "AGG": 0.25},
            rebalance_frequency=RebalanceFrequency.WEEKLY,
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.MOMENTUM,
            thesis_document="""Sector momentum persists 2-4 weeks (institutional rebalancing lag). SSO/QLD (2x S&P/Nasdaq) capture momentum spikes faster than SPY/QQQ through leverage amplification. Edge window (2-4 weeks) shorter than 2x decay dominance (30+ days sideways). SSO/QLD decay ~0.8-1.0% annually in sideways markets (daily rebalancing friction). Edge target: +12-16% alpha vs SPY/QQQ, justifying decay 12-20x. 2020 COVID: SSO -68% vs SPY -34% (2x amplification). Expected max drawdown: -28% to -38% (2x baseline -15-20% realistic pessimistic scenario). Benchmark: SSO vs SPY targeting +8-10% alpha after decay. Why not SPY? Unleveraged captures only 6-8% with lower drawdown; 2x justified for momentum edge enhancement before mean reversion.""",
            rebalancing_rationale="""Weekly rebalancing aligns with 2-4 week momentum persistence. Weights: SSO 40% + QLD 35% (2x tilt), AGG 25% (defensive buffer). Allocation reduces portfolio leverage to ~1.5x effective."""
        )

        errors = generator._validate_leverage_justification(strategy)
        # Should pass all 4 core elements (2x doesn't require stress test/exit)
        assert len(errors) == 0, f"Expected no errors but got: {errors}"

    def test_unrealistic_drawdown_rejected(self):
        """3x claiming unrealistic drawdown should be hard rejected."""
        generator = CandidateGenerator()

        strategy = Strategy(
            name="3x Fantasy Drawdown",
            assets=["TQQQ"],
            weights={"TQQQ": 1.0},
            rebalance_frequency=RebalanceFrequency.DAILY,
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.MOMENTUM,
            thesis_document="""Tech momentum with TQQQ provides amplified returns through convexity advantage. TQQQ decays 3% annually in sideways markets, justified by 20% alpha target. Max 25% drawdown expected. Benchmark: TQQQ vs QQQ for momentum amplification. 2022 stress: TQQQ declined during rate shock. Exit if VIX > 30 or momentum turns negative.""",
            rebalancing_rationale="Daily rebalancing captures short-term momentum signals and aligns with high-frequency edge timing. Weights allocated based on momentum strength indicators with TQQQ providing 3x exposure to Nasdaq technology leadership during bullish momentum regimes."
        )

        errors = generator._validate_leverage_justification(strategy)
        assert len(errors) > 0
        assert any("Priority 1" in err and "UNREALISTIC" in err for err in errors)
        # Should flag that 20-30% is unrealistic for 3x (should be 40-65%)

    def test_non_approved_leveraged_etf_rejected(self):
        """Non-whitelisted leveraged ETF should trigger retry."""
        generator = CandidateGenerator()

        strategy = Strategy(
            name="Exotic 3x Strategy",
            assets=["FNGU", "SPY"],  # FNGU is 3x FANG but not on whitelist
            weights={"FNGU": 0.60, "SPY": 0.40},
            rebalance_frequency=RebalanceFrequency.WEEKLY,
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.MOMENTUM,
            thesis_document="FANG momentum strategy." * 20,
            rebalancing_rationale="Weekly rebalancing." * 10
        )

        # Note: FNGU won't be detected as leveraged unless it has indicators like "3X"
        # But if we add "3X" to the name for testing:
        strategy_with_indicator = Strategy(
            name="Exotic 3X Strategy",
            assets=["EXOTIC3X", "SPY"],
            weights={"EXOTIC3X": 0.60, "SPY": 0.40},
            rebalance_frequency=RebalanceFrequency.WEEKLY,
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.MOMENTUM,
            thesis_document="3X amplified strategy." * 20,
            rebalancing_rationale="Weekly rebalancing." * 10
        )

        errors = generator._validate_leverage_justification(strategy_with_indicator)
        assert len(errors) > 0
        assert any("Priority 2" in err and "non-approved" in err for err in errors)

    def test_boundary_drawdown_3x_exactly_at_minimum(self):
        """3x with exactly 40% drawdown should pass (at minimum threshold)."""
        generator = CandidateGenerator()

        strategy = Strategy(
            name="3x Boundary Drawdown Test",
            assets=["TQQQ", "BIL"],
            weights={"TQQQ": 0.60, "BIL": 0.40},
            rebalance_frequency=RebalanceFrequency.WEEKLY,
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.MOMENTUM,
            thesis_document="""Tech momentum with TQQQ. Convexity: faster momentum capture amplifies edge window. Decay: 3-4% annually in sideways markets. Max drawdown: 40% expected in worst case scenario. Benchmark: TQQQ vs QQQ for 2-4 week momentum amplification. 2022 stress test: TQQQ -80% vs QQQ -35%. Exit if VIX > 30 for 5+ days or momentum turns negative.""",
            rebalancing_rationale="Weekly rebalancing for momentum edge." * 10
        )

        errors = generator._validate_leverage_justification(strategy)
        # Should pass - 40% is exactly at minimum threshold for 3x
        assert len(errors) == 0, f"Expected no errors for 40% drawdown (at minimum), got: {errors}"

    def test_boundary_drawdown_3x_below_minimum(self):
        """3x with 39% drawdown should fail (below minimum threshold)."""
        generator = CandidateGenerator()

        strategy = Strategy(
            name="3x Below Boundary Drawdown",
            assets=["TQQQ"],
            weights={"TQQQ": 1.0},
            rebalance_frequency=RebalanceFrequency.DAILY,
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.MOMENTUM,
            thesis_document="""Tech momentum with TQQQ provides amplified exposure to Nasdaq technology leadership during bullish momentum regimes driven by AI infrastructure buildout and enterprise adoption cycles. Convexity advantage: 3x amplification captures faster returns through leverage multiplier effect. Decay cost: 3% annually from daily rebalancing friction in sideways markets. Worst case 39% drawdown expected based on historical volatility patterns and back-testing analysis. Benchmark comparison: TQQQ vs QQQ for momentum amplification with target alpha of 20-25% over unleveraged baseline position.""",
            rebalancing_rationale="Daily momentum tracking with high-frequency rebalancing to capture short-term edge windows while managing volatility exposure through dynamic position sizing and risk controls." * 2
        )

        errors = generator._validate_leverage_justification(strategy)
        # Should fail because 39% drawdown is below the 40% minimum for 3x
        # Note: Still missing stress test and exit criteria, but drawdown check should fail first
        assert len(errors) > 0
        assert any("39%" in err and "UNREALISTIC" in err for err in errors), f"Expected unrealistic drawdown error, got: {errors}"

    def test_boundary_drawdown_2x_at_minimum(self):
        """2x with exactly 18% drawdown should pass (at minimum threshold)."""
        generator = CandidateGenerator()

        strategy = Strategy(
            name="2x Boundary Drawdown",
            assets=["SSO", "AGG"],
            weights={"SSO": 0.50, "AGG": 0.50},
            rebalance_frequency=RebalanceFrequency.WEEKLY,
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.MOMENTUM,
            thesis_document="""S&P 500 momentum strategy with SSO (2x leveraged S&P) amplification for faster edge capture through leverage convexity advantage. Decay cost: 0.8% annually from daily rebalancing friction. Max drawdown: 18% expected in worst case scenario based on historical analysis. Benchmark: SSO vs SPY for momentum enhancement and alpha generation.""",
            rebalancing_rationale="Weekly rebalancing schedule with equal-weight allocation between SSO (50%) and AGG (50%) provides balanced exposure to equity momentum while maintaining defensive bond buffer for volatility management." * 2
        )

        errors = generator._validate_leverage_justification(strategy)
        # Should pass - 18% is exactly at minimum threshold for 2x
        assert len(errors) == 0, f"Expected no errors for 18% drawdown (at minimum), got: {errors}"

    def test_mixed_2x_and_3x_uses_stricter_validation(self):
        """Strategy with both 2x and 3x should use 3x validation rules (all 6 elements)."""
        generator = CandidateGenerator()

        # Missing stress test and exit - should fail with 3x rules
        strategy = Strategy(
            name="Mixed 2x + 3x Strategy",
            assets=["SSO", "TQQQ", "AGG"],
            weights={"SSO": 0.30, "TQQQ": 0.40, "AGG": 0.30},
            rebalance_frequency=RebalanceFrequency.WEEKLY,
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.MOMENTUM,
            thesis_document="""Mixed leverage momentum. Convexity: faster capture through amplification. Decay: 2-4% blended annually. Drawdown: 45-55% realistic range. Benchmark: vs SPY/QQQ blended.""" * 5,
            rebalancing_rationale="Weekly momentum rotation." * 10
        )

        errors = generator._validate_leverage_justification(strategy)
        # Should require ALL 6 elements (3x rules)
        assert len(errors) > 0
        assert any("stress" in err.lower() or "2022" in err or "2020" in err for err in errors)

    def test_regex_variant_decay_annually_suffix(self):
        """'decay 3% annually' should match decay number pattern."""
        generator = CandidateGenerator()

        strategy = Strategy(
            name="Decay Suffix Variant",
            assets=["TQQQ"],
            weights={"TQQQ": 1.0},
            rebalance_frequency=RebalanceFrequency.DAILY,
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.MOMENTUM,
            thesis_document="""Tech momentum with TQQQ. Convexity: faster capture through amplification. Daily rebalancing friction causes decay 3% annually in sideways markets. Drawdown: 50-60% realistic. Benchmark: TQQQ vs QQQ for momentum. 2022 stress: TQQQ -80% decline. Exit if VIX > 30 or momentum < 0.""",
            rebalancing_rationale="Daily trading strategy with high-frequency rebalancing to capture short-term momentum signals and manage intraday volatility exposure through systematic position adjustments based on technical indicators and market regime classification." * 2
        )

        errors = generator._validate_leverage_justification(strategy)
        # "decay 3% annually" should be recognized
        assert not any("decay cost" in err.lower() for err in errors), "Should recognize 'decay 3% annually' pattern"

    def test_regex_variant_yearly_decay(self):
        """'3% yearly decay' should match decay number pattern."""
        generator = CandidateGenerator()

        strategy = Strategy(
            name="Yearly Decay Variant",
            assets=["UPRO"],
            weights={"UPRO": 1.0},
            rebalance_frequency=RebalanceFrequency.DAILY,
            edge_type=EdgeType.STRUCTURAL,
            archetype=StrategyArchetype.DIRECTIONAL,
            thesis_document="""S&P bull market amplification. Convexity advantage from 3x leverage enhances directional edge. Expects 3% yearly decay from daily rebalancing. Drawdown: 55-65% worst case. Benchmark: UPRO vs SPY targeting +15% alpha. 2022: UPRO -65% vs SPY -20% stress test. Exit criteria: if SPY < 200d MA or VIX > 35.""",
            rebalancing_rationale="Daily exposure management." * 10
        )

        errors = generator._validate_leverage_justification(strategy)
        # "3% yearly decay" should be recognized
        assert not any("decay cost" in err.lower() for err in errors), "Should recognize '3% yearly decay' pattern"

    def test_multiple_missing_elements_generates_multiple_errors(self):
        """Missing convexity + decay + stress test should generate 3 separate errors."""
        generator = CandidateGenerator()

        strategy = Strategy(
            name="Multiple Missing Elements",
            assets=["TQQQ"],
            weights={"TQQQ": 1.0},
            rebalance_frequency=RebalanceFrequency.DAILY,
            edge_type=EdgeType.BEHAVIORAL,
            archetype=StrategyArchetype.MOMENTUM,
            thesis_document="""Tech momentum strategy. Drawdown: 50-60%. Benchmark: TQQQ vs QQQ. Exit if VIX > 30.""" * 10,
            rebalancing_rationale="Daily rebalancing." * 10
        )

        errors = generator._validate_leverage_justification(strategy)
        # Should have errors for: convexity, decay, stress test
        assert len(errors) >= 3
        assert any("convexity" in err.lower() for err in errors)
        assert any("decay" in err.lower() for err in errors)
        assert any("stress" in err.lower() for err in errors)
