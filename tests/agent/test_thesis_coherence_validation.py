"""
Unit tests for thesis coherence validation functions.

Tests three new validation methods in CandidateGenerator:
1. _validate_archetype_logic_tree: Validates archetype requires appropriate logic_tree
2. _validate_thesis_logic_tree_coherence: Validates VIX thresholds match between thesis and logic_tree
3. _validate_weight_derivation_coherence: Validates momentum-weighted claims match actual weights
"""

import pytest
from src.agent.stages.candidate_generator import CandidateGenerator
from src.agent.models import Strategy, RebalanceFrequency, StrategyArchetype


class TestValidateArchetypeLogicTree:
    """Test _validate_archetype_logic_tree validation"""

    def test_momentum_with_rotation_and_empty_logic_tree_fails(self):
        """Momentum archetype with rotation claim and empty logic_tree should FAIL"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Momentum Rotation Strategy",
            assets=["SPY", "QQQ", "IWM"],
            weights={"SPY": 0.33, "QQQ": 0.33, "IWM": 0.34},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={},
            rebalancing_rationale="Monthly rebalancing rotates into top momentum sectors based on 3-month trailing returns, exploiting momentum persistence that typically lasts 6-12 months. This rotation mechanism systematically shifts capital toward sectors with strongest relative strength to capture momentum premium.",
            thesis_document="Strategy rotates toward sectors with strongest momentum signals, shifting allocation dynamically based on relative strength trends. In current market conditions with sector dispersion elevated, momentum rotation captures performance spread between leaders and laggards. The strategy shifts allocation monthly toward top momentum sectors, exploiting the well-documented momentum persistence effect that typically extends 6-12 months across equity sectors.",
            archetype=StrategyArchetype.MOMENTUM
        )

        errors = generator._validate_archetype_logic_tree(strategy, 1)

        assert len(errors) == 1
        assert "Priority 1" in errors[0]
        assert "Implementation-Thesis Mismatch" in errors[0]
        assert "Momentum archetype with rotation claims" in errors[0]
        assert "logic_tree is empty" in errors[0]

    def test_momentum_with_rotation_and_populated_logic_tree_passes(self):
        """Momentum archetype with rotation claim and populated logic_tree should PASS"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Momentum Rotation Strategy",
            assets=["SPY", "QQQ", "IWM"],
            weights={},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={
                "condition": "SPY_momentum > QQQ_momentum",
                "if_true": {"SPY": 0.6, "QQQ": 0.3, "IWM": 0.1},
                "if_false": {"SPY": 0.2, "QQQ": 0.6, "IWM": 0.2}
            },
            rebalancing_rationale="Monthly rebalancing rotates into top momentum sectors based on 3-month trailing returns, exploiting momentum persistence that typically lasts 6-12 months. This rotation mechanism systematically shifts capital toward sectors with strongest relative strength to capture momentum premium.",
            thesis_document="Strategy rotates toward sectors with strongest momentum signals, shifting allocation dynamically based on relative strength trends. In current market conditions with sector dispersion elevated, momentum rotation captures performance spread between leaders and laggards. The strategy shifts allocation monthly toward top momentum sectors, exploiting the well-documented momentum persistence effect that typically extends 6-12 months across equity sectors.",
            archetype=StrategyArchetype.MOMENTUM
        )

        errors = generator._validate_archetype_logic_tree(strategy, 1)

        assert len(errors) == 0

    def test_momentum_without_rotation_and_empty_logic_tree_passes(self):
        """Momentum archetype without rotation claim and empty logic_tree should PASS"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Momentum Buy-and-Hold",
            assets=["MTUM", "QMOM", "IMOM"],
            weights={"MTUM": 0.5, "QMOM": 0.3, "IMOM": 0.2},
            rebalance_frequency=RebalanceFrequency.QUARTERLY,
            logic_tree={},
            rebalancing_rationale="Quarterly rebalancing maintains static exposure to momentum factor ETFs, implementing momentum premium capture through long-term factor tilts. This buy-and-hold approach systematically captures momentum factor returns without active rotation, relying on underlying ETF rebalancing mechanisms.",
            thesis_document="Buy-and-hold momentum factor ETFs to capture persistent momentum premium across market cycles. In current environment with momentum factor showing positive performance, static exposure through specialized ETFs provides systematic momentum capture without tactical timing. The strategy maintains diversified momentum exposure through multiple complementary momentum ETFs covering different market segments.",
            archetype=StrategyArchetype.MOMENTUM
        )

        errors = generator._validate_archetype_logic_tree(strategy, 1)

        assert len(errors) == 0

    def test_volatility_archetype_with_empty_logic_tree_fails(self):
        """Volatility archetype with empty logic_tree should FAIL"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Volatility Strategy",
            assets=["VXX", "SVXY"],
            weights={"VXX": 0.5, "SVXY": 0.5},
            rebalance_frequency=RebalanceFrequency.DAILY,
            logic_tree={},
            rebalancing_rationale="Daily rebalancing maintains fixed 50/50 exposure to volatility products, capturing mean-reversion in VIX term structure. This balanced allocation systematically profits from volatility term structure dynamics and mean-reversion patterns across market regimes.",
            thesis_document="Exploit volatility mean-reversion by maintaining balanced exposure to long and short volatility products. In current market environment with VIX term structure in contango, balanced exposure captures premium from term structure decay while maintaining protection against volatility spikes. The strategy profits from the statistical tendency of volatility to mean-revert from extreme levels over short time horizons.",
            archetype=StrategyArchetype.VOLATILITY
        )

        errors = generator._validate_archetype_logic_tree(strategy, 1)

        assert len(errors) == 1
        assert "Priority 1" in errors[0]
        assert "Implementation-Thesis Mismatch" in errors[0]
        assert "Volatility archetype typically requires conditional logic_tree" in errors[0]

    def test_volatility_archetype_with_populated_logic_tree_passes(self):
        """Volatility archetype with populated logic_tree should PASS"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Volatility Regime Strategy",
            assets=["VXX", "SVXY"],
            weights={},
            rebalance_frequency=RebalanceFrequency.DAILY,
            logic_tree={
                "condition": "VIX > 25",
                "if_true": {"VXX": 0.8, "SVXY": 0.2},
                "if_false": {"VXX": 0.2, "SVXY": 0.8}
            },
            rebalancing_rationale="Daily rebalancing shifts allocation based on VIX regime threshold at 25, exploiting volatility mean-reversion at extreme levels. When VIX exceeds 25 (high volatility regime), strategy tilts toward long volatility positions anticipating mean-reversion. Below 25, tilts toward short volatility to capture term structure premium.",
            thesis_document="Dynamically adjust volatility exposure based on VIX levels to capture mean-reversion premium from extreme volatility regimes. In current market with VIX around 15-20 range, regime-based allocation allows systematic capture of volatility mean-reversion patterns. Historical analysis shows VIX above 25 typically reverts within 30-60 days, providing asymmetric opportunities for regime-aware volatility strategies.",
            archetype=StrategyArchetype.VOLATILITY
        )

        errors = generator._validate_archetype_logic_tree(strategy, 1)

        assert len(errors) == 0

    def test_non_momentum_volatility_archetype_with_empty_logic_tree_passes(self):
        """Non-momentum/volatility archetype with empty logic_tree should PASS"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Buy-and-Hold Portfolio",
            assets=["SPY", "AGG"],
            weights={"SPY": 0.6, "AGG": 0.4},
            rebalance_frequency=RebalanceFrequency.QUARTERLY,
            logic_tree={},
            rebalancing_rationale="Quarterly rebalancing maintains 60/40 target allocation, implementing contrarian rebalancing that systematically buys dips in equities and sells rallies, capturing mean-reversion premium from tactical drift. This disciplined rebalancing provides natural downside protection through forced selling of winners and buying losers.",
            thesis_document="Classic balanced portfolio captures equity risk premium while maintaining downside protection through fixed income allocation. In current environment with positive equity momentum and stable bond yields, 60/40 allocation provides diversified exposure to core asset classes. Historical analysis shows quarterly rebalancing enhances risk-adjusted returns through contrarian drift capture without excessive trading costs.",
            archetype=StrategyArchetype.DIRECTIONAL
        )

        errors = generator._validate_archetype_logic_tree(strategy, 1)

        assert len(errors) == 0


class TestValidateThesisLogicTreeCoherence:
    """Test _validate_thesis_logic_tree_coherence validation"""

    def test_exact_vix_match_passes(self):
        """Thesis 'VIX > 25' with logic_tree condition 'VIX > 25' should PASS (exact match)"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="VIX Strategy",
            assets=["SPY", "BIL"],
            weights={},
            rebalance_frequency=RebalanceFrequency.DAILY,
            logic_tree={
                "condition": "VIX > 25",
                "if_true": {"SPY": 0.0, "BIL": 1.0},
                "if_false": {"SPY": 1.0, "BIL": 0.0}
            },
            rebalancing_rationale="Daily rebalancing shifts to cash when VIX exceeds 25, implementing regime-aware risk management based on volatility threshold. This defensive rotation protects capital during high volatility periods when equity drawdowns typically accelerate. Cash position maintained until VIX normalizes below 25 threshold.",
            thesis_document="When VIX > 25, market enters high volatility regime requiring defensive positioning until volatility normalizes. Historical analysis shows VIX above 25 signals elevated market stress with average subsequent 30-day equity returns significantly negative. The strategy implements tactical risk-off positioning during these periods, rotating to cash equivalents to preserve capital and re-entering equities once volatility subsides.",
        )

        errors = generator._validate_thesis_logic_tree_coherence(strategy, 1)

        assert len(errors) == 0

    def test_within_tolerance_passes(self):
        """Thesis 'VIX > 25' with logic_tree condition 'VIX > 22' should PASS (within 20%)"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="VIX Strategy",
            assets=["SPY", "BIL"],
            weights={},
            rebalance_frequency=RebalanceFrequency.DAILY,
            logic_tree={
                "condition": "VIX > 22",
                "if_true": {"SPY": 0.0, "BIL": 1.0},
                "if_false": {"SPY": 1.0, "BIL": 0.0}
            },
            rebalancing_rationale="Daily rebalancing shifts to cash when VIX exceeds 22, implementing regime-aware risk management based on volatility threshold. This defensive rotation protects capital during high volatility periods when equity drawdowns typically accelerate. Cash position maintained until VIX normalizes below threshold.",
            thesis_document="When VIX > 25, market enters high volatility regime requiring defensive positioning until volatility normalizes. Historical analysis shows VIX above 25 signals elevated market stress with average subsequent 30-day equity returns significantly negative. The strategy implements tactical risk-off positioning during these periods, rotating to cash equivalents to preserve capital and re-entering equities once volatility subsides.",
        )

        errors = generator._validate_thesis_logic_tree_coherence(strategy, 1)

        assert len(errors) == 0

    def test_exceeds_tolerance_fails(self):
        """Thesis 'VIX > 25' with logic_tree condition 'VIX > 35' should FAIL (40% deviation)"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="VIX Strategy",
            assets=["SPY", "BIL"],
            weights={},
            rebalance_frequency=RebalanceFrequency.DAILY,
            logic_tree={
                "condition": "VIX > 35",
                "if_true": {"SPY": 0.0, "BIL": 1.0},
                "if_false": {"SPY": 1.0, "BIL": 0.0}
            },
            rebalancing_rationale="Daily rebalancing shifts to cash when VIX exceeds 35, implementing regime-aware risk management based on volatility threshold. This defensive rotation protects capital during extreme volatility periods when equity drawdowns typically accelerate. Cash position maintained until VIX normalizes below threshold.",
            thesis_document="When VIX > 25, market enters high volatility regime requiring defensive positioning until volatility normalizes. Historical analysis shows VIX above 25 signals elevated market stress with average subsequent 30-day equity returns significantly negative. The strategy implements tactical risk-off positioning during these periods, rotating to cash equivalents to preserve capital and re-entering equities once volatility subsides.",
        )

        errors = generator._validate_thesis_logic_tree_coherence(strategy, 1)

        assert len(errors) == 1
        assert "Priority 1" in errors[0]
        assert "Value Mismatch" in errors[0]
        assert "Thesis mentions VIX threshold 25.0" in errors[0]
        assert "logic_tree condition uses 35.0" in errors[0]
        assert "40%" in errors[0]

    def test_vix_exceeds_within_tolerance_passes(self):
        """Thesis 'VIX exceeds 20' with logic_tree condition 'VIX > 18' should PASS (within 20%)"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="VIX Strategy",
            assets=["SPY", "BIL"],
            weights={},
            rebalance_frequency=RebalanceFrequency.DAILY,
            logic_tree={
                "condition": "VIX > 18",
                "if_true": {"SPY": 0.0, "BIL": 1.0},
                "if_false": {"SPY": 1.0, "BIL": 0.0}
            },
            rebalancing_rationale="Daily rebalancing shifts to cash when VIX exceeds 18, implementing regime-aware risk management based on volatility threshold. This defensive rotation protects capital during elevated volatility periods when equity drawdowns risk increases substantially. Strategy re-enters equities once VIX normalizes below threshold.",
            thesis_document="When VIX exceeds 20, market volatility signals elevated risk requiring defensive positioning. Historical analysis demonstrates VIX above 20 correlates with increased drawdown probability and reduced risk-adjusted returns. The strategy implements tactical cash rotation during these periods to preserve capital, exploiting the mean-reverting nature of volatility spikes to time equity re-entry when conditions stabilize.",
        )

        errors = generator._validate_thesis_logic_tree_coherence(strategy, 1)

        assert len(errors) == 0

    def test_no_vix_mention_passes(self):
        """Thesis without VIX mention should PASS (no check needed)"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Momentum Strategy",
            assets=["MTUM", "VLUE"],
            weights={},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={
                "condition": "MTUM_return_3m > VLUE_return_3m",
                "if_true": {"MTUM": 0.7, "VLUE": 0.3},
                "if_false": {"MTUM": 0.3, "VLUE": 0.7}
            },
            rebalancing_rationale="Monthly rebalancing tilts toward factor with strongest recent 3-month performance, exploiting factor momentum persistence that typically extends 6-12 months. Dynamic allocation increases exposure to outperforming factor while maintaining diversified factor exposure, capturing factor rotation premium through systematic rebalancing.",
            thesis_document="Rotate between momentum and value factors based on 3-month relative performance, capturing factor rotation premium. In current market environment with cyclical factor leadership patterns, dynamic factor allocation exploits performance persistence while avoiding concentrated bets. Historical analysis shows factors exhibit medium-term momentum, making 3-month lookback optimal for rotation timing without excessive whipsaw.",
        )

        errors = generator._validate_thesis_logic_tree_coherence(strategy, 1)

        assert len(errors) == 0

    def test_empty_logic_tree_passes(self):
        """Empty logic_tree should PASS (no check needed)"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Static Portfolio",
            assets=["SPY", "AGG"],
            weights={"SPY": 0.6, "AGG": 0.4},
            rebalance_frequency=RebalanceFrequency.QUARTERLY,
            logic_tree={},
            rebalancing_rationale="Quarterly rebalancing maintains 60/40 target allocation, implementing contrarian rebalancing that systematically buys dips in equities and sells rallies, capturing mean-reversion premium from tactical drift. This disciplined rebalancing provides downside protection through forced selling of winners and buying losers.",
            thesis_document="When VIX > 25, volatility signals elevated risk but strategy maintains allocation discipline through all market regimes without tactical adjustments. Classic balanced approach relies on asset class diversification and rebalancing discipline rather than timing. Historical evidence supports maintaining strategic allocation through volatility spikes, as tactical timing often underperforms disciplined buy-and-hold with systematic rebalancing.",
        )

        errors = generator._validate_thesis_logic_tree_coherence(strategy, 1)

        assert len(errors) == 0


class TestValidateWeightDerivationCoherence:
    """Test _validate_weight_derivation_coherence validation"""

    def test_momentum_weighted_with_round_weights_fails(self):
        """'momentum-weighted' claim with round weights [0.33, 0.33, 0.34] should FAIL"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Momentum Weighted Portfolio",
            assets=["SPY", "QQQ", "IWM"],
            weights={"SPY": 0.33, "QQQ": 0.33, "IWM": 0.34},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={},
            rebalancing_rationale="Monthly momentum-weighted rebalancing allocates proportional to 3-month momentum values, systematically overweighting winners and underweighting losers to capture momentum persistence. Position sizes derived from trailing return calculations to reflect relative strength across holdings.",
            thesis_document="Momentum-weighted allocation exploits momentum premium by dynamically sizing positions based on trailing returns. In current market with sector dispersion elevated, momentum-weighted positioning captures performance spreads between leaders and laggards. Strategy systematically allocates more capital to assets with stronger momentum signals, implementing proportional weighting based on quantitative momentum measures rather than equal or arbitrary allocations.",
        )

        errors = generator._validate_weight_derivation_coherence(strategy, 1)

        assert len(errors) == 1
        assert "Priority 2" in errors[0]
        assert "Derivation Mismatch" in errors[0]
        assert "momentum-weighted" in errors[0]
        assert "all round numbers" in errors[0]

    def test_momentum_weighted_with_nonround_weights_passes(self):
        """'momentum-weighted' claim with non-round weights [0.54, 0.28, 0.18] should PASS"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Momentum Weighted Portfolio",
            assets=["SPY", "QQQ", "IWM"],
            weights={"SPY": 0.54, "QQQ": 0.28, "IWM": 0.18},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={},
            rebalancing_rationale="Monthly momentum-weighted rebalancing allocates proportional to 3-month momentum values (SPY: 4.09%, QQQ: 2.1%, IWM: 1.5%), systematically overweighting winners to capture momentum persistence. Position sizes mathematically derived from trailing return calculations to reflect relative strength across holdings, resulting in non-round weight allocations.",
            thesis_document="Momentum-weighted allocation exploits momentum premium by dynamically sizing positions based on trailing returns. In current market with sector dispersion elevated, momentum-weighted positioning captures performance spreads between leaders and laggards. Strategy systematically allocates more capital to assets with stronger momentum signals, implementing proportional weighting based on quantitative momentum measures rather than equal or arbitrary allocations.",
        )

        errors = generator._validate_weight_derivation_coherence(strategy, 1)

        assert len(errors) == 0

    def test_no_momentum_claim_with_round_weights_passes(self):
        """NO momentum-weighted claim with round weights should PASS (claim not made)"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Equal Weight Portfolio",
            assets=["SPY", "QQQ", "IWM"],
            weights={"SPY": 0.33, "QQQ": 0.33, "IWM": 0.34},
            rebalance_frequency=RebalanceFrequency.QUARTERLY,
            logic_tree={},
            rebalancing_rationale="Quarterly equal-weight rebalancing maintains uniform allocation across three equity segments, implementing contrarian rebalancing that systematically reduces concentration in outperformers. This disciplined approach forces selling winners and buying losers, capturing mean-reversion premium from short-term performance dispersion.",
            thesis_document="Equal-weight portfolio captures diversification benefits and contrarian rebalancing edge without momentum tilts. In current market environment with sector rotation volatility elevated, equal-weight approach provides balanced exposure while avoiding concentration risks. Historical evidence shows equal-weight strategies outperform cap-weighted approaches over long horizons through systematic rebalancing discipline and contrarian positioning.",
        )

        errors = generator._validate_weight_derivation_coherence(strategy, 1)

        assert len(errors) == 0

    def test_momentum_weighted_with_two_weights_passes(self):
        """'momentum-weighted' claim with only 2 weights should PASS (threshold is 3+)"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Momentum Weighted Portfolio",
            assets=["SPY", "AGG"],
            weights={"SPY": 0.50, "AGG": 0.50},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={},
            rebalancing_rationale="Monthly momentum-weighted rebalancing allocates based on relative momentum between equities and bonds, implementing tactical asset allocation. Position sizing determined by cross-asset momentum measures to capture regime shifts between risk-on and risk-off periods through systematic momentum-based weighting adjustments.",
            thesis_document="Momentum-weighted allocation between stocks and bonds exploits cross-asset momentum patterns to capture regime transitions. In current market environment with equity momentum positive and bond yields stable, momentum-weighted approach provides tactical flexibility. Strategy adjusts equity-bond balance based on trailing momentum measures, systematically increasing equity exposure during bull markets and rotating to bonds during bear phases based on quantitative momentum signals.",
        )

        errors = generator._validate_weight_derivation_coherence(strategy, 1)

        assert len(errors) == 0

    def test_weighted_by_momentum_with_round_weights_fails(self):
        """'weighted by momentum' claim with round weights should FAIL"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Factor Portfolio",
            assets=["MTUM", "QUAL", "SIZE", "VLUE"],
            weights={"MTUM": 0.25, "QUAL": 0.25, "SIZE": 0.25, "VLUE": 0.25},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={},
            rebalancing_rationale="Monthly rebalancing weighted by momentum performance across factors, systematically tilting toward factors with strongest recent performance to capture factor momentum premium. Position sizes derived from quantitative momentum metrics to reflect relative factor strength, implementing momentum-based allocation adjustments.",
            thesis_document="Multi-factor portfolio with dynamic weighting based on factor momentum trends. In current market environment with cyclical factor leadership patterns, momentum-based factor allocation exploits performance persistence across style factors. Strategy systematically allocates more capital to factors exhibiting positive momentum while maintaining diversified factor exposure, capturing factor rotation premium through quantitative momentum-weighted position sizing rather than static equal allocations.",
        )

        errors = generator._validate_weight_derivation_coherence(strategy, 1)

        assert len(errors) == 1
        assert "Priority 2" in errors[0]
        assert "Derivation Mismatch" in errors[0]

    def test_proportional_to_momentum_with_round_weights_fails(self):
        """'proportional to momentum' claim with round weights should FAIL"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Sector Rotation",
            assets=["XLK", "XLV", "XLF"],
            weights={"XLK": 0.40, "XLV": 0.30, "XLF": 0.30},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={},
            rebalancing_rationale="Monthly rebalancing with weights proportional to momentum values, allocating more capital to sectors with stronger momentum signals to capture sector rotation premium. Position sizes mathematically derived from trailing sector momentum calculations to reflect relative strength, implementing proportional momentum-based weighting.",
            thesis_document="Sector allocation proportional to momentum captures sector rotation trends and exploits leadership persistence. In current market with elevated sector dispersion, proportional momentum weighting systematically captures performance spreads between leading and lagging sectors. Strategy allocates capital in proportion to quantitative momentum measures rather than equal or arbitrary weights, exploiting the well-documented momentum persistence effect across equity sectors that typically extends 3-12 months.",
        )

        errors = generator._validate_weight_derivation_coherence(strategy, 1)

        assert len(errors) == 1
        assert "Priority 2" in errors[0]

    def test_momentum_based_weights_with_round_numbers_fails(self):
        """'momentum-based weight' claim with round weights should FAIL"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Dynamic Allocation",
            assets=["SPY", "EFA", "EEM"],
            weights={"SPY": 0.50, "EFA": 0.25, "EEM": 0.25},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={},
            rebalancing_rationale="Monthly momentum-based weighting adjusts allocations based on regional equity momentum measures, overweighting regions with positive momentum trends to capture global rotation premium. Position sizes derived from quantitative momentum calculations across geographic regions to reflect relative strength patterns and leadership shifts.",
            thesis_document="Geographic allocation using momentum-based weights to capture regional rotation opportunities. In current environment with divergent regional equity performance, momentum-based geographic weighting exploits leadership persistence across developed and emerging markets. Strategy systematically allocates capital based on trailing momentum measures across regions, capturing global rotation premium through quantitative momentum-derived position sizing rather than static strategic allocations.",
        )

        errors = generator._validate_weight_derivation_coherence(strategy, 1)

        assert len(errors) == 1
        assert "Priority 2" in errors[0]

    def test_momentum_weighted_hyphenated_variant(self):
        """Test 'momentum-weighted' with hyphen triggers validation"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Hyphenated Momentum",
            assets=["A", "B", "C"],
            weights={"A": 0.333, "B": 0.333, "C": 0.334},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={},
            rebalancing_rationale="Uses momentum-weighted allocation across three assets, systematically tilting toward recent winners to capture momentum premium over 6-12 month horizons. Position sizes derived from trailing return calculations to reflect relative momentum strength, implementing quantitative momentum-based weighting rather than arbitrary equal allocations.",
            thesis_document="Momentum strategy with systematic position sizing based on quantitative momentum measures. In current market environment with dispersion elevated, momentum-weighted positioning captures performance differentials between leaders and laggards. Strategy allocates capital proportional to trailing momentum signals across holdings, exploiting well-documented momentum persistence effect through mathematically-derived position sizing that reflects relative strength rather than static equal weights.",
        )

        errors = generator._validate_weight_derivation_coherence(strategy, 1)

        assert len(errors) == 1
        assert "momentum-weighted" in errors[0] or "Derivation Mismatch" in errors[0]

    def test_momentum_weighted_space_variant(self):
        """Test 'momentum weighted' without hyphen triggers validation"""
        generator = CandidateGenerator()
        strategy = Strategy(
            name="Space Separated Momentum",
            assets=["X", "Y", "Z"],
            weights={"X": 0.30, "Y": 0.35, "Z": 0.35},
            rebalance_frequency=RebalanceFrequency.MONTHLY,
            logic_tree={},
            rebalancing_rationale="Implements momentum weighted approach to capture performance persistence, allocating capital based on trailing 3-month returns across three assets. Position sizes derived from quantitative momentum calculations to reflect relative strength patterns, systematically overweighting winners to exploit momentum persistence over 6-12 month horizons.",
            thesis_document="Dynamic momentum allocation strategy that sizes positions based on trailing momentum measures. In current market with performance dispersion elevated, momentum weighted positioning systematically captures spread between leaders and laggards. Strategy allocates capital proportional to quantitative momentum signals rather than equal weights, exploiting momentum persistence through mathematically-derived position sizing that reflects relative performance strength across holdings.",
        )

        errors = generator._validate_weight_derivation_coherence(strategy, 1)

        assert len(errors) == 1
