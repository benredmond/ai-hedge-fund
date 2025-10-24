import pytest
from datetime import datetime
from freezegun import freeze_time
from unittest.mock import patch
from src.market_context.assembler import assemble_market_context_pack
from src.market_context.validation import validate_context_pack


class TestIntegration:
    """End-to-end integration tests with real data sources."""

    @freeze_time("2025-01-15 12:00:00")
    @patch('src.market_context.fetchers.Fred')
    def test_end_to_end_context_generation(self, mock_fred_class):
        """Generate complete context pack end-to-end and validate it."""
        # Mock FRED API to avoid external dependency
        mock_fred = mock_fred_class.return_value
        mock_fred.get_series_latest_release.return_value = type('obj', (object,), {
            'iloc': type('obj', (object,), {
                '__getitem__': lambda self, x: 5.25
            })()
        })()

        # Generate context pack (uses real yfinance for regime snapshot)
        context_pack = assemble_market_context_pack(fred_api_key="test_key")

        # Validate structure
        assert "metadata" in context_pack
        assert "regime_snapshot" in context_pack
        assert "macro_indicators" in context_pack
        assert "recent_events" in context_pack
        assert "regime_tags" in context_pack

        # Validate metadata
        metadata = context_pack["metadata"]
        assert metadata["anchor_date"].startswith("2025-01-15")
        assert metadata["version"] == "v1.0.0"

        # Validate regime snapshot has required sections
        regime = context_pack["regime_snapshot"]
        assert "trend" in regime
        assert "volatility" in regime
        assert "breadth" in regime
        assert "sector_leadership" in regime
        assert "factor_regime" in regime

        # Validate macro indicators
        macro = context_pack["macro_indicators"]
        assert "interest_rates" in macro
        assert "inflation" in macro
        assert "employment" in macro

        # Validate events is a list
        assert isinstance(context_pack["recent_events"], list)

        # Validate regime tags
        assert isinstance(context_pack["regime_tags"], list)
        assert len(context_pack["regime_tags"]) > 0

        # Run validation suite
        is_valid, errors = validate_context_pack(context_pack)
        assert is_valid, f"Validation failed: {errors}"

    @freeze_time("2025-01-15 12:00:00")
    @patch('src.market_context.fetchers.Fred')
    def test_regime_tags_classification(self, mock_fred_class):
        """Regime tags are correctly classified."""
        mock_fred = mock_fred_class.return_value
        mock_fred.get_series_latest_release.return_value = type('obj', (object,), {
            'iloc': type('obj', (object,), {
                '__getitem__': lambda self, x: 5.25
            })()
        })()

        context_pack = assemble_market_context_pack(fred_api_key="test_key")

        tags = context_pack["regime_tags"]

        # Should have trend classification
        assert any(tag in ["bull", "strong_bull", "bear", "strong_bear"] for tag in tags)

        # Should have volatility classification
        assert any(tag.startswith("volatility_") for tag in tags)

    @freeze_time("2025-01-15 12:00:00")
    @patch('src.market_context.fetchers.Fred')
    def test_no_future_data_leakage(self, mock_fred_class):
        """Ensures no events or data points are from the future."""
        mock_fred = mock_fred_class.return_value
        mock_fred.get_series_latest_release.return_value = type('obj', (object,), {
            'iloc': type('obj', (object,), {
                '__getitem__': lambda self, x: 5.25
            })()
        })()

        context_pack = assemble_market_context_pack(fred_api_key="test_key")

        anchor_date = datetime.fromisoformat(context_pack["metadata"]["anchor_date"])

        # Check all events are before or at anchor date
        for event in context_pack["recent_events"]:
            event_date = datetime.fromisoformat(event["date"])
            assert event_date <= anchor_date, f"Event {event['date']} is after anchor {anchor_date}"
