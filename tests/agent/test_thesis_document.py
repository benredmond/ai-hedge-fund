"""Tests for Strategy.thesis_document field validation."""

import pytest
from pydantic import ValidationError
from src.agent.models import Strategy


class TestThesisDocumentValidation:
    """Test thesis_document field constraints and validators."""

    def test_thesis_document_optional_backward_compatibility(self):
        """thesis_document is optional for backward compatibility (default='')"""
        strategy = Strategy(
            name="Test Strategy",
            assets=["SPY"],
            weights={"SPY": 1.0},
            rebalance_frequency="monthly",
            rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
            # No thesis_document provided - should default to ""
        )
        assert strategy.thesis_document == ""

    def test_thesis_document_min_length_enforced(self):
        """thesis_document must be at least 200 characters when provided"""
        short_thesis = "This thesis is too short to pass validation."

        with pytest.raises(ValidationError, match="at least 200"):
            Strategy(
                name="Test Strategy",
                assets=["SPY"],
                weights={"SPY": 1.0},
                rebalance_frequency="monthly",
                thesis_document=short_thesis,
                rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
            )

    def test_thesis_document_max_length_enforced(self):
        """thesis_document cannot exceed 2000 characters"""
        long_thesis = "X" * 2001  # Exactly 2001 characters

        with pytest.raises(ValidationError, match="at most 2000"):
            Strategy(
                name="Test Strategy",
                assets=["SPY"],
                weights={"SPY": 1.0},
                rebalance_frequency="monthly",
                thesis_document=long_thesis,
                rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
            )

    def test_thesis_document_valid_content_accepted(self):
        """Valid thesis_document with substantive content is accepted"""
        valid_thesis = (
            "This is a valid investment thesis with sufficient length and content. "
            "The market opportunity stems from the current low volatility regime (VIX at 18.6) "
            "which historically favors momentum strategies. The specific edge being exploited "
            "is the institutional capital flow lag in sector rotation, which creates a 2-4 week "
            "window where sector trends persist post-identification. This edge exists because "
            "large asset managers have quarterly rebalancing constraints and cannot react "
            "immediately to sector trends. The risk factor is a VIX spike above 28 for 5+ "
            "consecutive days, which would trigger defensive rotation and invalidate the momentum thesis."
        )

        strategy = Strategy(
            name="Momentum Strategy",
            assets=["XLK", "XLY"],
            weights={"XLK": 0.6, "XLY": 0.4},
            rebalance_frequency="weekly",
            thesis_document=valid_thesis,
            rebalancing_rationale="Buy-and-hold approach lets winners compound without mechanically trimming positions, implementing momentum persistence by allowing natural concentration in outperformers rather than selling winners back to fixed weights."
        )

        assert len(strategy.thesis_document) >= 200
        assert len(strategy.thesis_document) <= 2000
        assert strategy.thesis_document == valid_thesis

    def test_thesis_document_exactly_200_chars_boundary(self):
        """thesis_document with exactly 200 characters passes validation"""
        # Create exactly 200 character thesis
        thesis_200 = "X" * 200

        strategy = Strategy(
            name="Test",
            assets=["SPY"],
            weights={"SPY": 1.0},
            rebalance_frequency="monthly",
            thesis_document=thesis_200,
            rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
        )

        assert len(strategy.thesis_document) == 200

    def test_thesis_document_exactly_2000_chars_boundary(self):
        """thesis_document with exactly 2000 characters passes validation"""
        # Create exactly 2000 character thesis
        thesis_2000 = "X" * 2000

        strategy = Strategy(
            name="Test",
            assets=["SPY"],
            weights={"SPY": 1.0},
            rebalance_frequency="monthly",
            thesis_document=thesis_2000,
            rebalancing_rationale="Monthly rebalancing maintains target weights by systematically buying dips and selling rallies, implementing contrarian exposure that captures mean-reversion across asset classes."
        )

        assert len(strategy.thesis_document) == 2000


class TestThesisDocumentIntegration:
    """Integration tests for thesis_document in workflow context."""

    def test_strategy_serialization_includes_thesis(self):
        """Serialized strategy includes thesis_document field"""
        thesis = "A" * 200  # Valid 200-char thesis

        strategy = Strategy(
            name="Test Strategy",
            assets=["SPY", "AGG"],
            weights={"SPY": 0.6, "AGG": 0.4},
            rebalance_frequency="monthly",
            thesis_document=thesis,
            rebalancing_rationale="Monthly equal-weight rebalancing implements mean-reversion by mechanically buying relative losers and selling relative winners, exploiting sector rotation overshoots that typically reverse within 30-60 days."
        )

        # Verify field is accessible
        assert hasattr(strategy, 'thesis_document')
        assert strategy.thesis_document == thesis

    def test_thesis_document_field_ordering_first(self):
        """thesis_document should appear first in model schema for LLM ordering"""
        # Get model fields in definition order
        fields = list(Strategy.model_fields.keys())

        # thesis_document should be first field
        assert fields[0] == 'thesis_document', f"Expected thesis_document first, got {fields[0]}"
